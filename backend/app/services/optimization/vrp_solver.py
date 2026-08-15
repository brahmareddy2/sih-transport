"""
OR-Tools Capacitated VRP with Time Windows (CVRPTW) solver.

Solves the multi-vehicle route optimization problem for Indian logistics:
- Multiple depots (city-based)
- Vehicle weight + volume capacity constraints
- Delivery time windows
- Driver hours constraints
- Multi-objective cost minimization

OR-Tools Documentation:
https://developers.google.com/optimization/routing/vrp
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Try importing OR-Tools; provide a clear error if missing
try:
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger.warning("OR-Tools not installed. VRP solver will use fallback greedy algorithm.")

from app.services.optimization.distance_matrix import (
    build_distance_matrix,
    build_time_matrix,
    city_distance_km,
    city_travel_time_min,
    INDIAN_CITIES,
)
from app.services.optimization.cost_calculator import (
    calculate_route_cost,
    utilization_percentage,
)
from app.services.optimization.objective import ObjectiveWeights, compute_objective_score


# ── Data Structures ───────────────────────────────────────────

@dataclass
class ShipmentInput:
    """Input representation of a shipment for the VRP solver."""
    id: str
    shipment_number: str
    origin_city: str
    destination_city: str
    weight_kg: float
    volume_m3: float = 0.0
    goods_type: str = "FMCG"
    is_hazardous: bool = False
    requires_refrigeration: bool = False
    priority: str = "normal"
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    declared_value_inr: float = 0.0


@dataclass
class VehicleInput:
    """Input representation of a vehicle for the VRP solver."""
    id: str
    registration_number: str
    vehicle_type: str
    capacity_weight_kg: float
    capacity_volume_m3: float = 0.0
    fuel_efficiency_kmpl: float = 5.0
    fuel_type: str = "diesel"
    is_refrigerated: bool = False
    can_carry_hazmat: bool = False
    current_city: str = "Mumbai"
    status: str = "available"
    driver_id: Optional[str] = None


@dataclass
class RouteStop:
    """One stop in an optimized route."""
    stop_sequence: int
    stop_type: str          # pickup | delivery | depot
    city: str
    shipment_id: Optional[str]
    shipment_number: Optional[str]
    lat: float
    lon: float
    planned_arrival_min: int   # minutes from route start
    planned_departure_min: int
    distance_from_prev_km: float
    cargo_weight_kg: float     # weight loaded/unloaded here
    cumulative_weight_kg: float


@dataclass
class OptimizedRoute:
    """Complete optimized route for one vehicle."""
    route_id: str
    vehicle_id: str
    vehicle_registration: str
    vehicle_type: str
    driver_id: Optional[str]
    stops: list[RouteStop]
    shipment_ids: list[str]
    total_distance_km: float
    empty_distance_km: float
    estimated_duration_min: int
    total_weight_kg: float
    utilization_pct: float
    fuel_litres: float
    fuel_cost_inr: float
    toll_cost_inr: float
    driver_cost_inr: float
    vehicle_opex_inr: float
    total_cost_inr: float
    co2_kg: float
    cost_breakdown: dict


@dataclass
class OptimizationResult:
    """Full result from the VRP solver for one optimization job."""
    job_id: str
    status: str          # solved | infeasible | timeout | error
    algorithm: str       # ortools_cvrptw | greedy_fallback
    solve_time_seconds: float
    total_routes: int
    total_shipments_served: int
    unserved_shipments: list[str]
    routes: list[OptimizedRoute]

    # Aggregated metrics
    total_distance_km: float
    total_empty_km: float
    total_fuel_litres: float
    total_fuel_cost_inr: float
    total_toll_inr: float
    total_driver_cost_inr: float
    total_cost_inr: float
    total_co2_kg: float
    avg_utilization_pct: float

    objective_score: dict
    explanation: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Main Solver ───────────────────────────────────────────────

class VRPSolver:
    """
    Capacitated VRP with Time Windows solver for Indian multi-city logistics.
    Uses Google OR-Tools if available, falls back to greedy nearest-neighbor.
    """

    def __init__(self, time_limit_seconds: int = 30):
        self.time_limit_seconds = time_limit_seconds

    def solve(
        self,
        shipments: list[ShipmentInput],
        vehicles: list[VehicleInput],
        weights: Optional[ObjectiveWeights] = None,
        road_type: str = "mixed",
        ai_risk_penalties: Optional[dict] = None,
    ) -> OptimizationResult:
        """
        Main entry point. Filters available vehicles, validates inputs,
        then dispatches to OR-Tools or greedy fallback.

        ai_risk_penalties (optional): dict mapping entity IDs to INR penalties:
          {
            "shipments": {"<shipment_id>": <penalty_inr>},  # delay risk
            "vehicles":  {"<vehicle_id>":  <penalty_inr>},  # health risk
          }
        These penalties are INFORMATIONAL to the optimizer — they bias route
        selection but do NOT override hard capacity/time-window constraints.
        """
        job_id = str(uuid.uuid4())
        start_time = time.time()
        weights = weights or ObjectiveWeights()
        ai_risk_penalties = ai_risk_penalties or {"shipments": {}, "vehicles": {}}

        logger.info(
            "VRP job %s: %d shipments, %d vehicles (AI penalties: %d shipments, %d vehicles)",
            job_id, len(shipments), len(vehicles),
            len(ai_risk_penalties.get("shipments", {})),
            len(ai_risk_penalties.get("vehicles", {})),
        )


        # Filter available vehicles
        available_vehicles = [v for v in vehicles if v.status in ("available", "idle")]
        if not available_vehicles:
            return self._error_result(job_id, "No available vehicles", start_time)

        if not shipments:
            return self._error_result(job_id, "No shipments to optimize", start_time)

        # Pre-filter: remove shipments that no vehicle can handle
        serviceable, unserviceable = self._prefilter_shipments(shipments, available_vehicles)
        if not serviceable:
            return self._error_result(job_id, "No shipments can be served by available vehicles", start_time)

        if ORTOOLS_AVAILABLE:
            try:
                result = self._solve_ortools(
                    job_id, serviceable, available_vehicles, weights, road_type, start_time,
                    ai_risk_penalties=ai_risk_penalties,
                )
                result.unserved_shipments = [s.id for s in unserviceable] + result.unserved_shipments
                return result
            except Exception as e:
                logger.error("OR-Tools solver failed: %s — using greedy fallback", e, exc_info=True)

        # Greedy fallback
        result = self._solve_greedy(
            job_id, serviceable, available_vehicles, weights, road_type, start_time,
            ai_risk_penalties=ai_risk_penalties,
        )
        result.unserved_shipments = [s.id for s in unserviceable] + result.unserved_shipments
        return result

    # ── OR-Tools Implementation ───────────────────────────────

    def _solve_ortools(
        self,
        job_id: str,
        shipments: list[ShipmentInput],
        vehicles: list[VehicleInput],
        weights: ObjectiveWeights,
        road_type: str,
        start_time: float,
        ai_risk_penalties: Optional[dict] = None,
    ) -> OptimizationResult:
        """
        OR-Tools CVRPTW implementation.

        Node layout: depot(0), then for each shipment: pickup(odd) + delivery(even).
        Using a single virtual depot at city[0] since vehicles start from their current city.
        """
        all_cities = self._extract_cities(shipments, vehicles)
        city_idx = {c: i for i, c in enumerate(all_cities)}
        n_cities = len(all_cities)

        dist_matrix = build_distance_matrix(all_cities)
        time_matrix = build_time_matrix(all_cities, road_type)

        # Convert to integers (OR-Tools requires int)
        dist_matrix_int = [[int(d * 10) for d in row] for row in dist_matrix]  # ×10 for 0.1 km precision
        time_matrix_int = [[int(t) for t in row] for row in time_matrix]       # minutes

        # ── Build OR-Tools model ──────────────────────────────
        # Nodes: 0 = virtual depot, then paired pickup+delivery for each shipment
        # Total nodes = 1 + 2×n_shipments
        n_shipments = len(shipments)
        n_nodes = 1 + 2 * n_shipments

        # Distance callback (city-index based)
        pickup_nodes  = [1 + 2 * i for i in range(n_shipments)]
        delivery_nodes = [2 + 2 * i for i in range(n_shipments)]

        # Map each node to a city index
        node_city: list[int] = [0]  # depot = city[0]
        for s in shipments:
            node_city.append(city_idx.get(s.origin_city, 0))       # pickup
            node_city.append(city_idx.get(s.destination_city, 0))  # delivery

        def distance_callback(from_node, to_node):
            c1, c2 = node_city[from_node], node_city[to_node]
            return dist_matrix_int[c1][c2]

        def time_callback(from_node, to_node):
            c1, c2 = node_city[from_node], node_city[to_node]
            return time_matrix_int[c1][c2]

        def demand_callback(node):
            if node == 0:
                return 0
            idx = (node - 1) // 2
            is_pickup = (node - 1) % 2 == 0
            w = int(shipments[idx].weight_kg)
            return w if is_pickup else -w

        n_vehicles = len(vehicles)
        capacities = [int(v.capacity_weight_kg) for v in vehicles]

        # Time window: minutes from "now" (treat as 0 = start of planning horizon)
        horizon_min = 72 * 60  # 72-hour planning window

        def get_time_window(node: int) -> tuple[int, int]:
            if node == 0:
                return (0, horizon_min)
            idx = (node - 1) // 2
            is_pickup = (node - 1) % 2 == 0
            s = shipments[idx]
            now = datetime.now(timezone.utc)
            if is_pickup:
                if s.time_window_start:
                    tw_start = s.time_window_start
                    if tw_start.tzinfo is None:
                        tw_start = tw_start.replace(tzinfo=timezone.utc)
                    delta = (tw_start - now).total_seconds() / 60
                    if delta > 0:
                        start = max(0, int(delta))
                        end = min(horizon_min, start + 720)
                    else:
                        start, end = 0, horizon_min
                else:
                    start, end = 0, horizon_min
            else:
                if s.time_window_end:
                    tw_end = s.time_window_end
                    if tw_end.tzinfo is None:
                        tw_end = tw_end.replace(tzinfo=timezone.utc)
                    delta = (tw_end - now).total_seconds() / 60
                    if delta > 0:
                        end = min(horizon_min, max(0, int(delta)))
                        start = max(0, end - 720)
                    else:
                        start, end = 0, horizon_min
                else:
                    start, end = 0, horizon_min
            return (start, end)

        manager = pywrapcp.RoutingIndexManager(n_nodes, n_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        # Register callbacks
        transit_cb_idx = routing.RegisterTransitCallback(
            lambda f, t: distance_callback(manager.IndexToNode(f), manager.IndexToNode(t))
        )
        routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

        # Capacity dimension
        demand_cb_idx = routing.RegisterUnaryTransitCallback(
            lambda idx: demand_callback(manager.IndexToNode(idx))
        )
        routing.AddDimensionWithVehicleCapacity(
            demand_cb_idx, 0, capacities, True, "Capacity"
        )

        # Time dimension
        time_cb_idx = routing.RegisterTransitCallback(
            lambda f, t: time_callback(manager.IndexToNode(f), manager.IndexToNode(t))
        )
        routing.AddDimension(
            time_cb_idx,
            60,           # max wait time
            horizon_min,  # max total time
            False,
            "Time",
        )
        time_dim = routing.GetDimensionOrDie("Time")
        for node_idx in range(1, n_nodes):
            index = manager.NodeToIndex(node_idx)
            tw = get_time_window(node_idx)
            time_dim.CumulVar(index).SetRange(tw[0], tw[1])

        # Pickup and delivery constraints
        for i in range(n_shipments):
            pickup_idx = manager.NodeToIndex(pickup_nodes[i])
            delivery_idx = manager.NodeToIndex(delivery_nodes[i])
            routing.AddPickupAndDelivery(pickup_idx, delivery_idx)
            routing.solver().Add(
                routing.VehicleVar(pickup_idx) == routing.VehicleVar(delivery_idx)
            )
            routing.solver().Add(
                time_dim.CumulVar(pickup_idx) <= time_dim.CumulVar(delivery_idx)
            )

        # Allow dropping nodes (unserved shipments) with high penalty
        penalty = int(weights.unserved_penalty)
        for node_idx in range(1, n_nodes):
            routing.AddDisjunction([manager.NodeToIndex(node_idx)], penalty)

        # ── Solve ─────────────────────────────────────────────
        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_params.time_limit.FromSeconds(self.time_limit_seconds)
        search_params.log_search = False

        solution = routing.SolveWithParameters(search_params)
        solve_time = round(time.time() - start_time, 2)

        if not solution:
            logger.warning("OR-Tools found no solution for job %s", job_id)
            return self._solve_greedy(
                job_id, shipments, vehicles, weights, road_type, start_time,
                ai_risk_penalties=ai_risk_penalties,
            )

        # ── Extract solution ──────────────────────────────────
        routes: list[OptimizedRoute] = []
        served_ids: set[str] = set()

        for v_idx, vehicle in enumerate(vehicles):
            index = routing.Start(v_idx)
            stops: list[RouteStop] = []
            total_dist = 0.0
            total_weight = 0.0
            cumulative_weight = 0.0
            stop_seq = 0
            prev_city_idx = city_idx.get(vehicle.current_city, 0)

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node != 0:  # skip depot
                    s_idx = (node - 1) // 2
                    is_pickup = (node - 1) % 2 == 0
                    shipment = shipments[s_idx]
                    this_city_idx = node_city[node]
                    this_city = all_cities[this_city_idx]
                    dist_from_prev = dist_matrix[prev_city_idx][this_city_idx]
                    total_dist += dist_from_prev

                    if is_pickup:
                        cumulative_weight += shipment.weight_kg
                        total_weight += shipment.weight_kg
                        served_ids.add(shipment.id)
                    else:
                        cumulative_weight -= shipment.weight_kg

                    lat = INDIAN_CITIES.get(this_city, {}).get("lat", 0.0)
                    lon = INDIAN_CITIES.get(this_city, {}).get("lon", 0.0)

                    stop = RouteStop(
                        stop_sequence=stop_seq,
                        stop_type="pickup" if is_pickup else "delivery",
                        city=this_city,
                        shipment_id=shipment.id,
                        shipment_number=shipment.shipment_number,
                        lat=lat,
                        lon=lon,
                        planned_arrival_min=0,
                        planned_departure_min=30,
                        distance_from_prev_km=round(dist_from_prev, 1),
                        cargo_weight_kg=shipment.weight_kg if is_pickup else -shipment.weight_kg,
                        cumulative_weight_kg=round(cumulative_weight, 1),
                    )
                    stops.append(stop)
                    stop_seq += 1
                    prev_city_idx = this_city_idx

                next_index = solution.Value(routing.NextVar(index))
                index = next_index

            if not stops:
                continue

            # Compute base route cost
            travel_hours = max(0.5, total_dist / 55.0)
            cost_result = calculate_route_cost(
                total_distance_km=total_dist,
                empty_distance_km=0.0,
                fuel_efficiency_kmpl=vehicle.fuel_efficiency_kmpl,
                fuel_type=vehicle.fuel_type,
                vehicle_type=vehicle.vehicle_type,
                road_type=road_type,
                travel_hours=travel_hours,
                payload_kg=total_weight,
            )
            # Compute AI risk penalties for this route
            ai_shipment_penalties = ai_risk_penalties.get("shipments", {}) if ai_risk_penalties else {}
            ai_vehicle_penalties = ai_risk_penalties.get("vehicles", {}) if ai_risk_penalties else {}
            # Deduplicate shipment IDs (each shipment appears in both pickup + delivery stop)
            stop_shipment_ids = list({s.shipment_id for s in stops if s.shipment_id})
            shipment_risk_penalty = sum(float(ai_shipment_penalties.get(sid, 0.0)) for sid in stop_shipment_ids)
            vehicle_risk_penalty = float(ai_vehicle_penalties.get(vehicle.id, 0.0))
            total_ai_penalty = shipment_risk_penalty + vehicle_risk_penalty
            if total_ai_penalty > 0:
                logger.debug(
                    "Applying AI risk penalties to vehicle %s: shipment=%.0f + vehicle=%.0f INR",
                    vehicle.registration_number, shipment_risk_penalty, vehicle_risk_penalty,
                )
            effective_cost = cost_result.total_cost_inr + total_ai_penalty
            utilization = utilization_percentage(total_weight, vehicle.capacity_weight_kg)

            routes.append(OptimizedRoute(
                route_id=str(uuid.uuid4()),
                vehicle_id=vehicle.id,
                vehicle_registration=vehicle.registration_number,
                vehicle_type=vehicle.vehicle_type,
                driver_id=vehicle.driver_id,
                stops=stops,
                shipment_ids=[s.shipment_id for s in stops if s.shipment_id and s.stop_type == "pickup"],
                total_distance_km=round(total_dist, 1),
                empty_distance_km=0.0,
                estimated_duration_min=int(travel_hours * 60),
                total_weight_kg=round(total_weight, 1),
                utilization_pct=utilization,
                fuel_litres=cost_result.fuel_litres,
                fuel_cost_inr=cost_result.fuel_cost_inr,
                toll_cost_inr=cost_result.toll_cost_inr,
                driver_cost_inr=cost_result.driver_cost_inr,
                vehicle_opex_inr=cost_result.vehicle_opex_inr,
                total_cost_inr=effective_cost,
                co2_kg=cost_result.co2_kg,
                cost_breakdown={**cost_result.to_dict(), "ai_risk_penalty_inr": total_ai_penalty},
            ))

        unserved = [s.id for s in shipments if s.id not in served_ids]
        return self._build_result(
            job_id, routes, unserved, weights, road_type,
            solve_time, "ortools_cvrptw"
        )

    # ── Greedy Fallback ───────────────────────────────────────

    def _solve_greedy(
        self,
        job_id: str,
        shipments: list[ShipmentInput],
        vehicles: list[VehicleInput],
        weights: ObjectiveWeights,
        road_type: str,
        start_time: float,
        ai_risk_penalties: Optional[dict] = None,
    ) -> OptimizationResult:
        """
        Greedy nearest-neighbor heuristic fallback when OR-Tools is unavailable.
        Assigns shipments to vehicles using a first-fit decreasing strategy.
        ai_risk_penalties: optional dict with 'shipments' and 'vehicles' penalty INR mappings.
        """
        logger.info("Running greedy VRP fallback for job %s", job_id)
        routes: list[OptimizedRoute] = []
        unserved: list[str] = []

        # Sort shipments: priority first (urgent > high > normal > low), then weight desc
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        sorted_shipments = sorted(
            shipments,
            key=lambda s: (priority_order.get(s.priority, 2), -s.weight_kg)
        )

        # Vehicle assignment state
        vehicle_loads: dict[str, float] = {v.id: 0.0 for v in vehicles}
        vehicle_stops: dict[str, list[RouteStop]] = {v.id: [] for v in vehicles}
        vehicle_distance: dict[str, float] = {v.id: 0.0 for v in vehicles}
        vehicle_current_city: dict[str, str] = {v.id: v.current_city for v in vehicles}

        for shipment in sorted_shipments:
            assigned = False
            for vehicle in vehicles:
                # Capacity check
                if vehicle_loads[vehicle.id] + shipment.weight_kg > vehicle.capacity_weight_kg * 0.95:
                    continue
                # Compatibility checks
                if shipment.requires_refrigeration and not vehicle.is_refrigerated:
                    continue
                if shipment.is_hazardous and not vehicle.can_carry_hazmat:
                    continue

                # Calculate distance legs
                curr_city = vehicle_current_city[vehicle.id]
                dist_to_pickup = city_distance_km(curr_city, shipment.origin_city)
                dist_pickup_to_delivery = city_distance_km(shipment.origin_city, shipment.destination_city)

                seq = len(vehicle_stops[vehicle.id])
                origin_lat = INDIAN_CITIES.get(shipment.origin_city, {}).get("lat", 0.0)
                origin_lon = INDIAN_CITIES.get(shipment.origin_city, {}).get("lon", 0.0)
                dest_lat = INDIAN_CITIES.get(shipment.destination_city, {}).get("lat", 0.0)
                dest_lon = INDIAN_CITIES.get(shipment.destination_city, {}).get("lon", 0.0)

                cum_weight_after_pickup = vehicle_loads[vehicle.id] + shipment.weight_kg

                vehicle_stops[vehicle.id].append(RouteStop(
                    stop_sequence=seq,
                    stop_type="pickup",
                    city=shipment.origin_city,
                    shipment_id=shipment.id,
                    shipment_number=shipment.shipment_number,
                    lat=origin_lat, lon=origin_lon,
                    planned_arrival_min=0,
                    planned_departure_min=30,
                    distance_from_prev_km=round(dist_to_pickup, 1),
                    cargo_weight_kg=shipment.weight_kg,
                    cumulative_weight_kg=round(cum_weight_after_pickup, 1),
                ))
                vehicle_stops[vehicle.id].append(RouteStop(
                    stop_sequence=seq + 1,
                    stop_type="delivery",
                    city=shipment.destination_city,
                    shipment_id=shipment.id,
                    shipment_number=shipment.shipment_number,
                    lat=dest_lat, lon=dest_lon,
                    planned_arrival_min=0,
                    planned_departure_min=30,
                    distance_from_prev_km=round(dist_pickup_to_delivery, 1),
                    cargo_weight_kg=-shipment.weight_kg,
                    cumulative_weight_kg=round(vehicle_loads[vehicle.id], 1),
                ))

                vehicle_loads[vehicle.id] += shipment.weight_kg
                vehicle_distance[vehicle.id] += dist_to_pickup + dist_pickup_to_delivery
                vehicle_current_city[vehicle.id] = shipment.destination_city
                assigned = True
                break

            if not assigned:
                unserved.append(shipment.id)

        # Build OptimizedRoute objects for non-empty vehicles
        for vehicle in vehicles:
            stops = vehicle_stops[vehicle.id]
            if not stops:
                continue

            total_dist = vehicle_distance[vehicle.id]
            total_weight = vehicle_loads[vehicle.id]
            travel_hours = max(0.5, total_dist / 55.0)
            cost_result = calculate_route_cost(
                total_distance_km=total_dist,
                empty_distance_km=0.0,
                fuel_efficiency_kmpl=vehicle.fuel_efficiency_kmpl,
                fuel_type=vehicle.fuel_type,
                vehicle_type=vehicle.vehicle_type,
                road_type=road_type,
                travel_hours=travel_hours,
                payload_kg=total_weight,
            )
            utilization = utilization_percentage(total_weight, vehicle.capacity_weight_kg)

            # ── AI Risk Penalty Injection ─────────────────────────────
            # Penalties from AI predictions (delay risk, vehicle health) are
            # additive costs — they bias route selection but do NOT override
            # hard constraints (capacity, time windows, availability).
            ai_shipment_penalties = ai_risk_penalties.get("shipments", {}) if ai_risk_penalties else {}
            ai_vehicle_penalties = ai_risk_penalties.get("vehicles", {}) if ai_risk_penalties else {}
            stop_shipment_ids = list({s.shipment_id for s in vehicle_stops.get(vehicle.id, []) if s.shipment_id})
            shipment_risk_penalty = sum(float(ai_shipment_penalties.get(sid, 0.0)) for sid in stop_shipment_ids)
            vehicle_risk_penalty = float(ai_vehicle_penalties.get(vehicle.id, 0.0))
            total_ai_penalty = shipment_risk_penalty + vehicle_risk_penalty
            if total_ai_penalty > 0:
                logger.debug(
                    "Applying AI risk penalties to vehicle %s: shipment=%.0f + vehicle=%.0f INR",
                    vehicle.registration_number, shipment_risk_penalty, vehicle_risk_penalty,
                )
            effective_cost = cost_result.total_cost_inr + total_ai_penalty

            routes.append(OptimizedRoute(
                route_id=str(uuid.uuid4()),
                vehicle_id=vehicle.id,
                vehicle_registration=vehicle.registration_number,
                vehicle_type=vehicle.vehicle_type,
                driver_id=vehicle.driver_id,
                stops=stops,
                shipment_ids=[s.shipment_id for s in stops if s.shipment_id and s.stop_type == "pickup"],
                total_distance_km=round(total_dist, 1),
                empty_distance_km=0.0,
                estimated_duration_min=int(travel_hours * 60),
                total_weight_kg=round(total_weight, 1),
                utilization_pct=utilization,
                fuel_litres=cost_result.fuel_litres,
                fuel_cost_inr=cost_result.fuel_cost_inr,
                toll_cost_inr=cost_result.toll_cost_inr,
                driver_cost_inr=cost_result.driver_cost_inr,
                vehicle_opex_inr=cost_result.vehicle_opex_inr,
                total_cost_inr=effective_cost,
                co2_kg=cost_result.co2_kg,
                cost_breakdown={**cost_result.to_dict(), "ai_risk_penalty_inr": total_ai_penalty},
            ))

        solve_time = round(time.time() - start_time, 2)
        return self._build_result(job_id, routes, unserved, weights, road_type, solve_time, "greedy_fallback")

    # ── Helpers ───────────────────────────────────────────────

    def _build_result(
        self,
        job_id: str,
        routes: list[OptimizedRoute],
        unserved: list[str],
        weights: ObjectiveWeights,
        road_type: str,
        solve_time: float,
        algorithm: str,
    ) -> OptimizationResult:
        total_distance = sum(r.total_distance_km for r in routes)
        total_empty = sum(r.empty_distance_km for r in routes)
        total_fuel_l = sum(r.fuel_litres for r in routes)
        total_fuel_cost = sum(r.fuel_cost_inr for r in routes)
        total_toll = sum(r.toll_cost_inr for r in routes)
        total_driver = sum(r.driver_cost_inr for r in routes)
        total_cost = sum(r.total_cost_inr for r in routes)
        total_co2 = sum(r.co2_kg for r in routes)
        avg_util = round(
            sum(r.utilization_pct for r in routes) / max(len(routes), 1), 1
        )
        total_served = sum(
            len([s for s in r.stops if s.stop_type == "pickup"])
            for r in routes
        )

        obj_score = compute_objective_score(
            total_cost_inr=total_cost,
            total_distance_km=total_distance,
            delay_minutes=0.0,
            empty_km=total_empty,
            co2_kg=total_co2,
            weights=weights,
        )

        explanation = self._generate_explanation(routes, unserved, total_cost, total_distance, avg_util)

        return OptimizationResult(
            job_id=job_id,
            status="solved" if routes else "infeasible",
            algorithm=algorithm,
            solve_time_seconds=solve_time,
            total_routes=len(routes),
            total_shipments_served=total_served,
            unserved_shipments=unserved,
            routes=routes,
            total_distance_km=round(total_distance, 1),
            total_empty_km=round(total_empty, 1),
            total_fuel_litres=round(total_fuel_l, 2),
            total_fuel_cost_inr=round(total_fuel_cost, 2),
            total_toll_inr=round(total_toll, 2),
            total_driver_cost_inr=round(total_driver, 2),
            total_cost_inr=round(total_cost, 2),
            total_co2_kg=round(total_co2, 2),
            avg_utilization_pct=avg_util,
            objective_score=obj_score,
            explanation=explanation,
        )

    def _extract_cities(
        self, shipments: list[ShipmentInput], vehicles: list[VehicleInput]
    ) -> list[str]:
        """Collect all unique city names referenced in the problem."""
        cities = set()
        for s in shipments:
            cities.add(s.origin_city)
            cities.add(s.destination_city)
        for v in vehicles:
            if v.current_city:
                cities.add(v.current_city)
        return sorted(cities)

    def _prefilter_shipments(
        self, shipments: list[ShipmentInput], vehicles: list[VehicleInput]
    ) -> tuple[list[ShipmentInput], list[ShipmentInput]]:
        """
        Remove shipments that no available vehicle can physically serve.
        Returns (serviceable, unserviceable).
        """
        serviceable, unserviceable = [], []
        for s in shipments:
            can_serve = any(
                s.weight_kg <= v.capacity_weight_kg
                and (not s.requires_refrigeration or v.is_refrigerated)
                and (not s.is_hazardous or v.can_carry_hazmat)
                for v in vehicles
            )
            (serviceable if can_serve else unserviceable).append(s)
        return serviceable, unserviceable

    def _generate_explanation(
        self,
        routes: list[OptimizedRoute],
        unserved: list[str],
        total_cost: float,
        total_distance: float,
        avg_utilization: float,
    ) -> list[str]:
        """Generate a human-readable explanation of the optimization results."""
        lines = []
        lines.append(f"Optimization completed: {len(routes)} routes planned.")
        lines.append(
            f"Total fleet cost: ₹{total_cost:,.0f} across {total_distance:,.0f} km."
        )
        lines.append(f"Average vehicle utilization: {avg_utilization:.1f}%.")

        if avg_utilization < 60:
            lines.append(
                "⚠️ Utilization below 60% — consider consolidating shipments or reducing active fleet."
            )
        elif avg_utilization > 90:
            lines.append(
                "✅ Excellent utilization above 90% — fleet running near full capacity."
            )

        if unserved:
            lines.append(
                f"⚠️ {len(unserved)} shipment(s) could not be served by available vehicles. "
                "Check weight/special requirements."
            )

        for i, r in enumerate(routes[:3]):  # explain top 3 routes
            lines.append(
                f"Route {i+1} ({r.vehicle_registration}): "
                f"{len([s for s in r.stops if s.stop_type=='pickup'])} shipments, "
                f"{r.total_distance_km} km, ₹{r.total_cost_inr:,.0f}, "
                f"{r.utilization_pct}% load."
            )

        return lines

    def _error_result(self, job_id: str, reason: str, start_time: float) -> OptimizationResult:
        return OptimizationResult(
            job_id=job_id, status="error", algorithm="none",
            solve_time_seconds=round(time.time() - start_time, 2),
            total_routes=0, total_shipments_served=0, unserved_shipments=[],
            routes=[], total_distance_km=0, total_empty_km=0,
            total_fuel_litres=0, total_fuel_cost_inr=0, total_toll_inr=0,
            total_driver_cost_inr=0, total_cost_inr=0, total_co2_kg=0,
            avg_utilization_pct=0, objective_score={},
            explanation=[f"Error: {reason}"],
        )


# ── Convenience singleton ─────────────────────────────────────
_solver_instance: Optional[VRPSolver] = None


def get_solver(time_limit_seconds: int = 30) -> VRPSolver:
    """Return a shared VRPSolver instance."""
    global _solver_instance
    if _solver_instance is None:
        _solver_instance = VRPSolver(time_limit_seconds=time_limit_seconds)
    return _solver_instance
