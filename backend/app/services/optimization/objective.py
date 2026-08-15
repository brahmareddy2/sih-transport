"""
Weighted multi-objective function for route optimization.

The optimizer minimizes a combined score across multiple objectives.
All weights are configurable per optimization request.

Default weights (sum to 1.0):
  cost     : 0.35  → primary objective
  distance : 0.25  → secondary
  delay    : 0.20  → SLA compliance
  empty_km : 0.10  → asset utilization
  co2      : 0.10  → sustainability

Each sub-objective is normalized to [0, 1] before weighting.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ObjectiveWeights:
    """
    Configurable weights for the multi-objective optimization function.
    Weights should sum to 1.0 (they are auto-normalized if not).
    """
    cost_weight: float = 0.35
    distance_weight: float = 0.25
    delay_weight: float = 0.20
    empty_km_weight: float = 0.10
    co2_weight: float = 0.10

    # Advanced toggles
    penalize_unserved: bool = True       # Heavy penalty for unserved shipments
    unserved_penalty: float = 1_000_000  # OR-Tools internal penalty per unserved stop

    def normalize(self) -> "ObjectiveWeights":
        """Return a new ObjectiveWeights with weights normalized to sum=1."""
        total = (
            self.cost_weight + self.distance_weight +
            self.delay_weight + self.empty_km_weight + self.co2_weight
        )
        if total == 0:
            return ObjectiveWeights()
        factor = 1.0 / total
        return ObjectiveWeights(
            cost_weight=self.cost_weight * factor,
            distance_weight=self.distance_weight * factor,
            delay_weight=self.delay_weight * factor,
            empty_km_weight=self.empty_km_weight * factor,
            co2_weight=self.co2_weight * factor,
            penalize_unserved=self.penalize_unserved,
            unserved_penalty=self.unserved_penalty,
        )

    def to_dict(self) -> dict:
        return {
            "cost_weight": self.cost_weight,
            "distance_weight": self.distance_weight,
            "delay_weight": self.delay_weight,
            "empty_km_weight": self.empty_km_weight,
            "co2_weight": self.co2_weight,
        }


# Pre-defined weight profiles
WEIGHT_PROFILES: dict[str, ObjectiveWeights] = {
    "balanced": ObjectiveWeights(
        cost_weight=0.35,
        distance_weight=0.25,
        delay_weight=0.20,
        empty_km_weight=0.10,
        co2_weight=0.10,
    ),
    "cost_minimization": ObjectiveWeights(
        cost_weight=0.60,
        distance_weight=0.20,
        delay_weight=0.10,
        empty_km_weight=0.05,
        co2_weight=0.05,
    ),
    "speed_priority": ObjectiveWeights(
        cost_weight=0.15,
        distance_weight=0.20,
        delay_weight=0.55,
        empty_km_weight=0.05,
        co2_weight=0.05,
    ),
    "green_logistics": ObjectiveWeights(
        cost_weight=0.20,
        distance_weight=0.20,
        delay_weight=0.20,
        empty_km_weight=0.10,
        co2_weight=0.30,
    ),
    "utilization_max": ObjectiveWeights(
        cost_weight=0.25,
        distance_weight=0.20,
        delay_weight=0.20,
        empty_km_weight=0.30,
        co2_weight=0.05,
    ),
}


def compute_objective_score(
    total_cost_inr: float,
    total_distance_km: float,
    delay_minutes: float,
    empty_km: float,
    co2_kg: float,
    weights: ObjectiveWeights,
    baseline_cost: Optional[float] = None,
    baseline_distance: Optional[float] = None,
) -> dict:
    """
    Compute the weighted objective score for a solution.

    Each dimension is normalized against a baseline (or absolute scale)
    and then weighted.

    Returns dict with:
      - individual scores (0–1)
      - weighted_score (lower = better)
      - improvement_pct (if baseline provided)
    """
    w = weights.normalize()

    # Normalize each dimension (lower is better)
    # Using rough Indian logistics baselines for normalization
    norm_cost = min(total_cost_inr / 100_000, 1.0)      # normalize to ₹1L
    norm_distance = min(total_distance_km / 5000, 1.0)   # normalize to 5000 km
    norm_delay = min(delay_minutes / 240, 1.0)            # normalize to 4 hours
    norm_empty = min(empty_km / 500, 1.0)                 # normalize to 500 km
    norm_co2 = min(co2_kg / 500, 1.0)                    # normalize to 500 kg CO2

    weighted_score = (
        w.cost_weight * norm_cost +
        w.distance_weight * norm_distance +
        w.delay_weight * norm_delay +
        w.empty_km_weight * norm_empty +
        w.co2_weight * norm_co2
    )

    result = {
        "weighted_score": round(weighted_score, 4),
        "cost_score": round(norm_cost, 4),
        "distance_score": round(norm_distance, 4),
        "delay_score": round(norm_delay, 4),
        "empty_km_score": round(norm_empty, 4),
        "co2_score": round(norm_co2, 4),
        "weights_used": w.to_dict(),
    }

    if baseline_cost and baseline_distance:
        cost_improvement = (baseline_cost - total_cost_inr) / baseline_cost * 100
        dist_improvement = (baseline_distance - total_distance_km) / baseline_distance * 100
        result["cost_improvement_pct"] = round(cost_improvement, 1)
        result["distance_improvement_pct"] = round(dist_improvement, 1)

    return result
