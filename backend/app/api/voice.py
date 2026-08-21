"""
Voice & Universal Search API Endpoints — Phase 8
Provides multilingual speech-to-text, universal search routing, highway facilities search,
safe communication dialer, and confirmation orchestration with RBAC security.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.voice.language_service import get_language_service, SUPPORTED_LANGUAGES
from app.services.voice.intent_router import get_intent_router
from app.services.voice.driver_assistant import HIGHWAY_FACILITIES
from app.services.voice.communication import get_communication_service
from app.services.voice.intent_parser import VoiceIntentParser

router = APIRouter(prefix="/voice", tags=["Voice & Universal Search Assistant"])


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


class CallRequest(BaseModel):
    target_category: str
    target_name: Optional[str] = None
    purpose: Optional[str] = "Emergency roadside assistance"


class CallResponse(BaseModel):
    status: str
    caller_role: str
    target_name: str
    category: str
    phone_masked: str
    phone_display: str
    location: str
    hours: str
    purpose: str
    provider: str
    message: str
    disclaimer: str


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
    """Retrieve supported Indian languages (English, Telugu, Hindi, Punjabi, Marathi)."""
    return SUPPORTED_LANGUAGES


@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(
    req: TranscribeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe raw WAV audio (Base64) using SpeechRecognition library, or fall back to client text.
    """
    audio_len = len(req.audio_base64) if req.audio_base64 else 0
    logger.info(
        "[Voice Transcribe] Received request. Audio payload size: %d bytes, Language: %s",
        audio_len,
        req.language,
    )

    text = ""
    detected_lang = req.language or "en"

    if req.audio_base64:
        try:
            import base64
            import io
            import speech_recognition as sr

            # Decode base64 bytes
            audio_data = base64.b64decode(req.audio_base64)
            audio_file = io.BytesIO(audio_data)

            r = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio = r.record(source)

            # Map simple language codes to standard Google Speech locale codes
            lang_map = {
                "en": "en-IN",
                "te": "te-IN",
                "hi": "hi-IN",
                "pa": "pa-IN",
                "mr": "mr-IN"
            }
            lang_code = lang_map.get(req.language, "en-IN")

            logger.info("[Voice Transcribe] Attempting recognize_google with language: %s", lang_code)
            text = r.recognize_google(audio, language=lang_code)
            logger.info("[Voice Transcribe] Google transcription result: '%s'", text)
        except sr.UnknownValueError:
            logger.warning("[Voice Transcribe] Google Speech Recognition could not understand the audio.")
            text = ""
        except sr.RequestError as e:
            logger.error("[Voice Transcribe] Could not request results from Google service: %s", e)
            text = ""
        except Exception as e:
            logger.error("[Voice Transcribe] Error processing audio transcription: %s", e, exc_info=True)
            text = ""

    # Fallback to client-provided fallback text if transcription failed but fallback exists
    if not text and req.text_fallback:
        text = req.text_fallback.strip()
        parser = VoiceIntentParser()
        detected_lang = req.language or parser.detect_language(text)
        logger.info("[Voice Transcribe] Falling back to client text_fallback: '%s'", text)

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
    Execute natural-language voice or search command using the Universal Intent Router.
    Enforces RBAC security and confirmation checkpoints.
    """
    router_service = get_intent_router()
    result = router_service.route_query(
        query=req.query,
        user_role=current_user.role,
        user_id=str(current_user.id),
        language=req.language or "en",
        confirmed=req.confirmed or False,
        action_payload=req.action_payload,
        db=db,
    )
    return VoiceCommandResponse(**result)


@router.get("/facilities")
def get_highway_facilities(
    category: str = Query(default="restaurants", description="restaurants, parking, restrooms, fuel_stations, puncture_shops"),
    current_user: User = Depends(get_current_user),
):
    """Search nearby Indian highway facilities for drivers (Food, Parking, Restrooms, Fuel, Puncture)."""
    cat = category.lower()
    items = HIGHWAY_FACILITIES.get(cat, HIGHWAY_FACILITIES.get("restaurants", []))
    return {
        "category": cat,
        "count": len(items),
        "facilities": items,
        "disclaimer": "Verified Indian freight corridor amenities dataset.",
    }


@router.post("/call", response_model=CallResponse)
def initiate_call(
    req: CallRequest,
    current_user: User = Depends(get_current_user),
):
    """Initiate a safe call to a puncture shop, fleet manager, driver, or operator desk."""
    comm = get_communication_service()
    data = comm.initiate_contact(
        target_category=req.target_category,
        caller_role=current_user.role,
        target_name=req.target_name,
        purpose=req.purpose or "Emergency assistance",
    )
    return CallResponse(**data)


@router.post("/respond", response_model=VoiceRespondResponse)
def get_voice_synthesis_payload(
    req: VoiceRespondRequest,
    current_user: User = Depends(get_current_user),
):
    """Format text for speech synthesis with BCP-47 language tag."""
    lang_svc = get_language_service()
    speech_code = lang_svc.get_speech_code(req.language)

    return VoiceRespondResponse(
        speech_text=req.text,
        speech_code=speech_code,
        language=req.language,
    )
