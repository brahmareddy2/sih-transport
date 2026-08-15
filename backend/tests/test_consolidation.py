"""
Unit tests for load consolidation compatibility rules and bin-packing.
"""
from datetime import datetime, timedelta
from app.services.optimization.consolidation import (
    is_goods_compatible,
    is_time_window_compatible,
    can_consolidate,
    group_shipments_for_consolidation,
)

def test_is_goods_compatible():
    assert is_goods_compatible("FMCG", "FMCG") is True
    assert is_goods_compatible("FMCG", "Electronics") is True
    # Incompatible pairs (Hazmat + Food/Pharma/etc)
    assert is_goods_compatible("Hazardous", "Food") is False
    assert is_goods_compatible("Chemicals", "Food") is False

def test_is_time_window_compatible():
    now = datetime.now()
    tw_a_start = now + timedelta(hours=2)
    tw_a_end = now + timedelta(hours=6)

    # Overlapping window
    tw_b_start = now + timedelta(hours=4)
    tw_b_end = now + timedelta(hours=8)
    assert is_time_window_compatible(tw_a_start, tw_a_end, tw_b_start, tw_b_end) is True

    # Far window (12 hours later)
    tw_c_start = now + timedelta(hours=18)
    tw_c_end = now + timedelta(hours=22)
    assert is_time_window_compatible(tw_a_start, tw_a_end, tw_c_start, tw_c_end) is False

def test_can_consolidate():
    shipment_a = {
        "is_hazardous": False,
        "requires_refrigeration": False,
        "goods_type": "FMCG",
        "time_window_start": None,
        "time_window_end": None,
    }
    shipment_b = {
        "is_hazardous": False,
        "requires_refrigeration": False,
        "goods_type": "FMCG",
        "time_window_start": None,
        "time_window_end": None,
    }
    shipment_c = {
        "is_hazardous": True,
        "requires_refrigeration": False,
        "goods_type": "Hazardous",
        "time_window_start": None,
        "time_window_end": None,
    }

    compat, reason = can_consolidate(shipment_a, shipment_b)
    assert compat is True

    compat_haz, reason = can_consolidate(shipment_a, shipment_c)
    assert compat_haz is False
    assert "hazardous" in reason.lower()

def test_group_shipments_for_consolidation():
    shipments = [
        {"id": "shp-1", "weight_kg": 200.0, "volume_m3": 1.0, "goods_type": "FMCG", "origin_city": "Mumbai", "destination_city": "Pune"},
        {"id": "shp-2", "weight_kg": 300.0, "volume_m3": 1.5, "goods_type": "FMCG", "origin_city": "Mumbai", "destination_city": "Pune"},
        {"id": "shp-3", "weight_kg": 400.0, "volume_m3": 2.0, "goods_type": "FMCG", "origin_city": "Mumbai", "destination_city": "Pune"},
    ]
    # Single vehicle that can handle the entire consolidated weight
    vehicles = [
        {"id": "v-1", "capacity_weight_kg": 2000.0, "capacity_volume_m3": 10.0, "status": "available"}
    ]

    groups = group_shipments_for_consolidation(shipments, vehicles)
    assert len(groups) == 1
    assert groups[0]["shipment_count"] == 3
    assert groups[0]["total_weight_kg"] == 900.0
