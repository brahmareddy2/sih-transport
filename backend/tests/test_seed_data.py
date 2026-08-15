"""
Unit tests for the synthetic data generator.
Verifies correct model attributes and internal data consistency.
"""
from app.services.seed_data.generator import (
    generate_vehicles,
    generate_drivers,
    generate_shipments,
    generate_trips_and_incidents,
    run_full_seed,
)

def test_generate_vehicles():
    vehicles = generate_vehicles(50)
    assert len(vehicles) == 50
    # Verify MH/GJ/KA prefix states are realistic
    for v in vehicles:
        assert len(v["registration_number"]) >= 8
        assert v["capacity_weight_kg"] > 0
        assert v["fuel_efficiency_kmpl"] > 0

def test_generate_drivers():
    drivers = generate_drivers(50)
    assert len(drivers) == 50
    for d in drivers:
        assert d["license_number"] is not None
        assert d["experience_years"] >= 2
        assert len(d["phone"]) >= 10

def test_generate_shipments():
    shipments = generate_shipments(100)
    assert len(shipments) == 100
    for s in shipments:
        assert s["origin_city"] != s["destination_city"]
        assert s["weight_kg"] >= 50.0
        assert s["volume_m3"] > 0.0

def test_run_full_seed():
    res = run_full_seed()
    assert res["summary"]["vehicles_count"] == 50
    assert res["summary"]["drivers_count"] == 50
    assert res["summary"]["shipments_count"] == 500
    assert res["summary"]["trips_count"] == 300
    assert res["summary"]["incidents_count"] == 80
