"""
Operator Assistant Service — Phase 8
Provides conversational intelligence for logistics dispatchers/operators:
- Load consolidation summaries
- Delayed shipments alerts
- Disruption and incident recovery plans
- Return cargo backhaul opportunities.
"""
from typing import Any, Dict
from app.services.voice.language_service import get_language_service


class OperatorAssistant:
    """Handles operator dispatch queries, routing optimization, and incident recovery."""

    def __init__(self):
        self.lang_service = get_language_service()

    def get_dispatch_summary(self, language: str = "en") -> Dict[str, Any]:
        """Return active dispatch operations summary."""
        text = "Dispatch Status: 45 active consignments in transit, 3 consolidated multi-drop routes, 2 minor delay alerts due to monsoon rain."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "OPERATOR_DISPATCH_SUMMARY",
            "card_data": {
                "active_consignments": 45,
                "consolidated_routes": 3,
                "delayed_shipments": 2,
                "pending_recoveries": 1,
                "open_return_opportunities": 4,
            },
        }

    def get_delayed_shipments(self, language: str = "en") -> Dict[str, Any]:
        """List delayed shipments with root cause."""
        text = "There are 2 shipments experiencing delay: SHP-104 (Mumbai ➔ Pune, +35 min delay due to ghat traffic) and SHP-209 (Delhi ➔ Jaipur, +20 min delay)."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "DELAYED_SHIPMENTS",
            "card_data": {
                "delayed_items": [
                    {"shipment_id": "SHP-104", "route": "Mumbai ➔ Pune", "delay_min": 35, "cause": "Monsoon ghat traffic", "carrier": "MH02AB1234"},
                    {"shipment_id": "SHP-209", "route": "Delhi ➔ Jaipur", "delay_min": 20, "cause": "Highway toll queue", "carrier": "DL01CD5678"},
                ],
            },
        }
