"""
Voice API Endpoints — Phase 8
Provides multilingual speech-to-text, intent parsing, confirmation orchestration,
and voice execution APIs for all 5 roles with RBAC security.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.voice.language_service import get_language_service, SUPPORTED_LANGUAGES
from app.services.voice.voice_service import get_voice_service
from app.services.voice.intent_parser import VoiceIntentParser

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])


# ── Pydantic Request / Response Schemas ────────────────────────────────────────

class TranscribeRequest(BaseModel):
    audio_base64: Optional[str] = None
    language: str = "en"
    text_fallback: Optional[str] = None


class TranscribeResponse(BaseModel):
    text: str
    detected_language: str
    confidence: float


class IntentRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


class IntentResponse(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any]
    detected_language: str
    requires_confirmation: bool


class VoiceCommandRequest(BaseModel):
    query: str
    language: Optional[str] = "en"
    confirmed: Optional[bool] = False
    action_payload: Optional[Dict[str, Any]] = None


class VoiceCommandResponse(BaseModel):
    text: str
    speech_text: str
    language: str
    intent: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_type: Optional[str] = None
    action_payload: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    card_type: Optional[str] = None
    card_data: Optional[Dict[str, Any]] = None
    is_authorized: Optional[bool] = True


class VoiceRespondRequest(BaseModel):
    text: str
    language: str = "en"


class VoiceRespondResponse(BaseModel):
    speech_text: str
    speech_code: str
    language: str


# ── API Endpoints ─────────────────────────────────────────────────────────────

@router.get("/languages", response_model=List[Dict[str, Any]])
def get_languages():
    """Retrieve the list of supported Indian languages (English, Telugu, Hindi, Punjabi, Marathi)."""
    return SUPPORTED_LANGUAGES


@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(
    req: TranscribeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe audio or return client-provided fallback text.
    Connects to browser Web Speech API with server-side text fallback.
    """
    text = (req.text_fallback or "").strip()
    parser = VoiceIntentParser()
    detected_lang = req.language or parser.detect_language(text)

    return TranscribeResponse(
        text=text,
        detected_language=detected_lang,
        confidence=0.95 if text else 0.0,
    )


@router.post("/intent", response_model=IntentResponse)
def parse_voice_intent(
    req: IntentRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse text into intent and extracted entities across 5 languages."""
    parser = VoiceIntentParser()
    res = parser.parse(req.text, user_language=req.language)

    return IntentResponse(
        intent=res.intent,
        confidence=res.confidence,
        entities=res.entities,
        detected_language=res.detected_language,
        requires_confirmation=res.requires_confirmation,
    )


@router.post("/command", response_model=VoiceCommandResponse)
def execute_voice_command(
    req: VoiceCommandRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute voice command with strict RBAC security, domain service integration,
    confirmation checkpoints, and localized response formatting.
    """
    service = get_voice_service()
    result = service.process_voice_query(
        query=req.query,
        user_role=current_user.role,
        user_id=str(current_user.id),
        language=req.language or "en",
        confirmed=req.confirmed or False,
        action_payload=req.action_payload,
        db=db,
    )
    return VoiceCommandResponse(**result)


@router.post("/respond", response_model=VoiceRespondResponse)
def get_voice_synthesis_payload(
    req: VoiceRespondRequest,
    current_user: User = Depends(get_current_user),
):
    """Format text for speech synthesis with the correct BCP-47 language tag."""
    lang_svc = get_language_service()
    speech_code = lang_svc.get_speech_code(req.language)

    return VoiceRespondResponse(
        speech_text=req.text,
        speech_code=speech_code,
        language=req.language,
    )
