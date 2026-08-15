"""
Unit/integration tests for OR-Tools and greedy VRP solver.
"""
from datetime import datetime, timedelta, timezone
from app.services.optimization.vrp_solver import VRPSolver, ShipmentInput, VehicleInput
from app.services.optimization.objective import ObjectiveWeights

def test_vrp_solver_greedy_fallback():
    # Test using the greedy solver fallback path
    solver = VRPSolver(time_limit_seconds=5)

    shipments = [
        ShipmentInput(
            id="shp-1",
            shipment_number="SHP001",
            origin_city="Mumbai",
            destination_city="Pune",
            weight_kg=1500.0,
            volume_m3=6.0,
        ),
        ShipmentInput(
            id="shp-2",
            shipment_number="SHP002",
            origin_city="Mumbai",
            destination_city="Pune",
            weight_kg=2000.0,
            volume_m3=8.0,
        ),
    ]

    vehicles = [
        VehicleInput(
            id="v-1",
            registration_number="MH12AB1234",
            vehicle_type="medium_truck",
            capacity_weight_kg=5000.0,
            capacity_volume_m3=20.0,
            fuel_efficiency_kmpl=6.0,
            status="available",
        )
    ]

    result = solver.solve(shipments, vehicles)
    assert result.status == "solved"
    assert result.total_routes == 1
    assert result.total_shipments_served == 2
    assert len(result.unserved_shipments) == 0

def test_vrp_solver_ortools_solution():
    solver = VRPSolver(time_limit_seconds=5)

    # Basic input parameters for full VRP check
    shipments = [
        ShipmentInput(
            id="shp-1",
            shipment_number="SHP001",
            origin_city="Mumbai",
            destination_city="Pune",
            weight_kg=500.0,
            volume_m3=2.0,
        ),
        ShipmentInput(
            id="shp-2",
            shipment_number="SHP002",
            origin_city="Pune",
            destination_city="Mumbai",
            weight_kg=800.0,
            volume_m3=3.0,
        ),
    ]

    vehicles = [
        VehicleInput(
            id="v-1",
            registration_number="MH12AB1234",
            vehicle_type="medium_truck",
            capacity_weight_kg=5000.0,
            capacity_volume_m3=20.0,
            fuel_efficiency_kmpl=6.0,
            status="available",
        ),
        VehicleInput(
            id="v-2",
            registration_number="MH14CD5678",
            vehicle_type="medium_truck",
            capacity_weight_kg=5000.0,
            capacity_volume_m3=20.0,
            fuel_efficiency_kmpl=6.0,
            status="available",
        )
    ]

    result = solver.solve(shipments, vehicles)
    assert result.status == "solved"
    assert result.total_routes >= 1
    assert result.total_cost_inr > 0
    assert result.total_distance_km > 0
