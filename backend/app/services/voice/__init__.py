"""
Voice & Universal Search Services — Phase 8
"""
from app.services.voice.language_service import (
    LanguageService,
    SUPPORTED_LANGUAGES,
    get_language_service,
)
from app.services.voice.intent_parser import VoiceIntentParser, IntentResult
from app.services.voice.response_builder import VoiceResponseBuilder
from app.services.voice.voice_service import VoiceService, get_voice_service
from app.services.voice.intent_router import UniversalIntentRouter, get_intent_router
from app.services.voice.driver_assistant import DriverAssistant, HIGHWAY_FACILITIES
from app.services.voice.owner_assistant import OwnerAssistant
from app.services.voice.admin_assistant import AdminAssistant
from app.services.voice.operator_assistant import OperatorAssistant
from app.services.voice.customer_assistant import CustomerAssistant
from app.services.voice.communication import CommunicationService, get_communication_service

__all__ = [
    "LanguageService",
    "SUPPORTED_LANGUAGES",
    "get_language_service",
    "VoiceIntentParser",
    "IntentResult",
    "VoiceResponseBuilder",
    "VoiceService",
    "get_voice_service",
    "UniversalIntentRouter",
    "get_intent_router",
    "DriverAssistant",
    "HIGHWAY_FACILITIES",
    "OwnerAssistant",
    "AdminAssistant",
    "OperatorAssistant",
    "CustomerAssistant",
    "CommunicationService",
    "get_communication_service",
]
