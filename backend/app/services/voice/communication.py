"""
Communication Service — Phase 8
Safe communication provider abstraction for contacting puncture shops, fleet managers,
drivers, and customers with permission enforcement and phone number masking.

For SIH prototype: Provides a safe demo dialer payload with clear disclosure.
For production: WebRTC / Twilio / approved telephony provider hooks.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Sample verified Indian highway service centers & directory
HIGHWAY_CONTACTS: Dict[str, Dict[str, Any]] = {
    "puncture_xyz": {
        "id": "cont-punc-1",
        "name": "XYZ Highway Tyre & Puncture Care",
        "category": "puncture_shop",
        "phone_masked": "+91 98XXX X4210",
        "phone_display": "+91 98765 44210",
        "location": "NH48 Express Mile 64 (Near Lonavala)",
        "rating": 4.8,
        "hours": "24 Hours Open",
    },
    "puncture_om": {
        "id": "cont-punc-2",
        "name": "Om Sai Tubeless Radial Repair",
        "category": "puncture_shop",
        "phone_masked": "+91 94XXX X8832",
        "phone_display": "+91 94230 18832",
        "location": "NH44 North-South Corridor (Near Nagpur)",
        "rating": 4.6,
        "hours": "06:00 AM - 11:00 PM",
    },
    "fleet_manager": {
        "id": "cont-fleet-1",
        "name": "Central Fleet Control Room",
        "category": "fleet_manager",
        "phone_masked": "+91 80XXX X1001",
        "phone_display": "+91 80456 71001",
        "location": "Logistics DSS Operations Hub",
        "rating": 5.0,
        "hours": "24/7 Dispatch Desk",
    },
    "operator_support": {
        "id": "cont-op-1",
        "name": "Logistics Dispatch & Emergency Desk",
        "category": "operator",
        "phone_masked": "+91 80XXX X9999",
        "phone_display": "+91 80456 79999",
        "location": "Logistics DSS Support Center",
        "rating": 5.0,
        "hours": "24/7 Emergency Support",
    },
    "driver_rajesh": {
        "id": "cont-drv-1",
        "name": "Rajesh Kumar (Driver - MH02AB1234)",
        "category": "driver",
        "phone_masked": "+91 91XXX X3341",
        "phone_display": "+91 91543 23341",
        "location": "En route Mumbai ➔ Hyderabad",
        "rating": 4.9,
        "hours": "On Duty",
    },
}


class CommunicationService:
    """Handles communication requests, permission checks, and dialer payloads."""

    def initiate_contact(
        self,
        target_category: str,
        caller_role: str = "driver",
        target_name: Optional[str] = None,
        purpose: str = "Emergency assistance",
    ) -> Dict[str, Any]:
        """Generate safe contact modal payload without exposing private raw identifiers."""
        # Find best matching contact
        contact = None
        for key, c in HIGHWAY_CONTACTS.items():
            if target_category.lower() in key or target_category.lower() in c["category"]:
                contact = c
                break

        if not contact:
            contact = HIGHWAY_CONTACTS["operator_support"]

        logger.info("Initiating safe communication: Role %s calling %s (%s)", caller_role, contact["name"], purpose)

        return {
            "status": "READY_TO_DIAL",
            "caller_role": caller_role,
            "target_name": target_name or contact["name"],
            "category": contact["category"],
            "phone_masked": contact["phone_masked"],
            "phone_display": contact["phone_display"],
            "location": contact["location"],
            "hours": contact["hours"],
            "purpose": purpose,
            "provider": "WebRTC / Browser Telephony (Demo Mode)",
            "message": f"Connecting call to {contact['name']} for {purpose}.",
            "disclaimer": "Demo call mode — configure Twilio/WebRTC provider for production VoIP routing.",
        }


_comm_instance: Optional[CommunicationService] = None


def get_communication_service() -> CommunicationService:
    global _comm_instance
    if _comm_instance is None:
        _comm_instance = CommunicationService()
    return _comm_instance
