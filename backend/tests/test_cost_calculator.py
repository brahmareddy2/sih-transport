"""
Unit tests for the India-specific cost calculation engine.
"""
from app.services.optimization.cost_calculator import (
    calculate_fuel_cost,
    calculate_toll_cost,
    calculate_driver_cost,
    calculate_route_cost,
    utilization_percentage,
)

def test_calculate_fuel_cost():
    # Mini truck with 10 kmpl efficiency on 100 km distance
    litres, cost = calculate_fuel_cost(distance_km=100.0, fuel_efficiency_kmpl=10.0, fuel_type="diesel")
    assert litres == 10.0
    assert cost == 930.0  # 10L * 93.0 INR/L

def test_calculate_toll_cost():
    # Medium truck on 200 km distance with mixed road type
    # Toll distance = 200 * 0.65 = 130 km
    # Rate for medium truck = 2.20 INR/km
    toll = calculate_toll_cost(distance_km=200.0, vehicle_type="medium_truck", road_type="mixed")
    assert toll == 286.0  # 130 * 2.2 = 286.0

def test_calculate_driver_cost():
    # 1 day, 6 hours travel (no overtime)
    cost_base = calculate_driver_cost(total_hours=6.0, num_days=1, include_batta=True)
    assert cost_base == 800.0  # 650 wage + 150 batta

    # 1 day, 12 hours travel (4 hours overtime)
    cost_ot = calculate_driver_cost(total_hours=12.0, num_days=1, include_batta=True)
    assert cost_ot == 1040.0  # 650 wage + 150 batta + 4 * 60 overtime

def test_calculate_route_cost():
    result = calculate_route_cost(
        total_distance_km=500.0,
        empty_distance_km=50.0,
        fuel_efficiency_kmpl=5.0,
        fuel_type="diesel",
        vehicle_type="large_truck",
        road_type="mixed",
        travel_hours=10.0,
        num_days=1,
        payload_kg=5000.0,
    )
    assert result.distance_km == 500.0
    assert result.fuel_litres == 100.0
    assert result.fuel_cost_inr == 9300.0
    assert result.driver_cost_inr == 920.0  # 650 + 150 + 2*60
    assert result.total_cost_inr > 10000.0
    assert result.empty_km_cost_inr > 0.0

def test_utilization_percentage():
    assert utilization_percentage(500, 1000) == 50.0
    assert utilization_percentage(1500, 1000) == 100.0
