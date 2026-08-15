"""
Voice Services Module — Phase 8 Universal Voice-First + Simple Mode User Experience.
Provides multilingual translation, intent parsing, confirmation builders, and voice execution orchestration.
"""
from app.services.voice.language_service import (
    LanguageService,
    SUPPORTED_LANGUAGES,
    get_language_service,
)
from app.services.voice.intent_parser import VoiceIntentParser, IntentResult
from app.services.voice.response_builder import VoiceResponseBuilder
from app.services.voice.voice_service import VoiceService, get_voice_service

__all__ = [
    "LanguageService",
    "SUPPORTED_LANGUAGES",
    "get_language_service",
    "VoiceIntentParser",
    "IntentResult",
    "VoiceResponseBuilder",
    "VoiceService",
    "get_voice_service",
]
