import React, { useState, useEffect, useRef } from 'react'
import { LANGUAGES, useI18nStore } from '../../services/i18n'
import { executeVoiceCommand } from '../../services/voiceApi'

export default function VoiceAssistantModal({ isOpen, onClose }) {
  const { language, t } = useI18nStore()
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [speaking, setSpeaking] = useState(false)
  const [voiceAvailable, setVoiceAvailable] = useState(true)

  const recognitionRef = useRef(null)

  // Get active speech code
  const currentLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]
  const speechCode = currentLangObj.speechCode || 'en-IN'

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = speechCode

        recognition.onstart = () => {
          setIsListening(true)
        }

        recognition.onresult = (event) => {
          const speechResult = event.results[0][0].transcript
          setTranscript(speechResult)
          setIsListening(false)
          handleCommand(speechResult, false)
        }

        recognition.onerror = (event) => {
          console.warn('Speech recognition error:', event.error)
          setIsListening(false)
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        recognitionRef.current = recognition
        setVoiceAvailable(true)
      } catch (e) {
        setVoiceAvailable(false)
      }
    } else {
      setVoiceAvailable(false)
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {}
      }
    }
  }, [speechCode])

  const startListening = () => {
    setResponse(null)
    setTranscript('')
    if (recognitionRef.current) {
      try {
        recognitionRef.current.lang = speechCode
        recognitionRef.current.start()
      } catch (e) {
        setIsListening(false)
      }
    } else {
      setIsListening(false)
    }
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {}
    }
    setIsListening(false)
  }

  const handleCommand = async (queryText, isConfirmed = false, actionPayload = null) => {
    if (!queryText || !queryText.trim()) return
    setLoading(true)
    try {
      const res = await executeVoiceCommand({
        query: queryText,
        language,
        confirmed: isConfirmed,
        action_payload: actionPayload,
      })
      setResponse(res)

      // Auto-speak response if speech synthesis available
      if (res && res.speech_text) {
        speakText(res.speech_text)
      }
    } catch (err) {
      setResponse({
        text: 'Sorry, I could not process that request. Please try typing.',
        speech_text: 'Sorry, I could not process that request.',
        language,
        requires_confirmation: false,
      })
    } finally {
      setLoading(false)
    }
  }

  const speakText = (textToSpeak) => {
    if (!window.speechSynthesis) return
    try {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(textToSpeak)
      utterance.lang = speechCode
      utterance.rate = 0.95
      utterance.onstart = () => setSpeaking(true)
      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => setSpeaking(false)
      window.speechSynthesis.speak(utterance)
    } catch (e) {
      setSpeaking(false)
    }
  }

  const handleManualSubmit = (e) => {
    e.preventDefault()
    if (!inputText.trim()) return
    setTranscript(inputText)
    handleCommand(inputText, false)
    setInputText('')
  }

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(10, 10, 20, 0.8)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: "'Inter', sans-serif",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '640px',
          background: '#181828',
          border: '1px solid #3b3b54',
          borderRadius: 24,
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #2d2d3d',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#1f1f33',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)',
              }}
            >
              🎤
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
                {t('voice_assistant', 'Voice Assistant')}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                {currentLangObj.native} ({currentLangObj.speechCode})
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#9ca3af',
              fontSize: '1.4rem',
              cursor: 'pointer',
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>

        {/* Conversation Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Voice Prompt Hero */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              background: isListening ? '#6366f115' : '#131320',
              border: `2px dashed ${isListening ? '#6366f1' : '#2d2d3d'}`,
              borderRadius: 20,
              transition: 'all 0.3s',
            }}
          >
            <button
              onClick={isListening ? stopListening : startListening}
              style={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: isListening ? '#ef4444' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                border: 'none',
                color: '#fff',
                fontSize: '2rem',
                cursor: 'pointer',
                boxShadow: isListening ? '0 0 25px #ef4444' : '0 10px 25px rgba(99, 102, 241, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s',
                transform: isListening ? 'scale(1.08)' : 'scale(1)',
              }}
            >
              {isListening ? '⏹️' : '🎤'}
            </button>
            <div style={{ marginTop: '14px', fontWeight: 700, fontSize: '1rem', color: isListening ? '#6366f1' : '#e2e8f0' }}>
              {isListening ? t('listening', 'Listening...') : t('speak', 'Tap to Speak')}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '4px', textAlign: 'center' }}>
              {currentLangObj.name === 'English'
                ? 'Try saying: "Plan a trip from Delhi to Hyderabad" or "How much fuel is left?"'
                : `చెప్పండి: "ఢిల్లీ నుండి హైదరాబాద్ ప్రయాణం" లేదా "ఎంత డీజిల్ ఉంది?"`}
            </div>
          </div>

          {/* Transcript Understood Prompt */}
          {transcript && (
            <div
              style={{
                padding: '14px 18px',
                background: '#232338',
                borderRadius: 14,
                border: '1px solid #3b3b54',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 700 }}>
                  You Said:
                </span>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginTop: '2px' }}>
                  "{transcript}"
                </div>
              </div>
              {speaking && (
                <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 700 }}>
                  🔊 Speaking...
                </span>
              )}
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div style={{ textAlign: 'center', padding: '16px', color: '#a5b4fc', fontSize: '0.9rem', fontWeight: 600 }}>
              ⚡ Processing logistics intelligence...
            </div>
          )}

          {/* Confirmation Dialog Question */}
          {response && response.requires_confirmation && (
            <div
              style={{
                padding: '20px',
                background: '#24243a',
                borderRadius: 16,
                border: '1px solid #6366f1aa',
                boxShadow: '0 8px 24px rgba(99, 102, 241, 0.2)',
              }}
            >
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginBottom: '14px' }}>
                {response.text}
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => handleCommand(transcript, true, response.action_payload)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: 10,
                    background: '#10b981',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 800,
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                  }}
                >
                  ✓ {t('yes_confirm', 'Yes, Proceed')}
                </button>
                <button
                  onClick={() => setResponse(null)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: 10,
                    background: '#2d2d3d',
                    color: '#e2e8f0',
                    border: '1px solid #3b3b54',
                    fontWeight: 800,
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                  }}
                >
                  ✕ {t('no_change', 'No, Change')}
                </button>
              </div>
            </div>
          )}

          {/* Visual Card Result */}
          {response && !response.requires_confirmation && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Text Summary + Speech Button */}
              <div
                style={{
                  padding: '16px 20px',
                  background: '#1f1f33',
                  borderRadius: 16,
                  border: '1px solid #3b3b54',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ fontSize: '0.95rem', color: '#e2e8f0', lineHeight: 1.5 }}>
                    {response.text}
                  </div>
                  <button
                    onClick={() => speakText(response.speech_text || response.text)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: 8,
                      background: '#6366f122',
                      color: '#a5b4fc',
                      border: '1px solid #6366f166',
                      fontWeight: 700,
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {t('listen', '🔊 Listen')}
                  </button>
                </div>
              </div>

              {/* TRIP RESULT CARD */}
              {response.card_type === 'TRIP_RESULT' && response.card_data && (
                <div
                  style={{
                    padding: '20px',
                    background: 'linear-gradient(135deg, #1b1b2d, #202038)',
                    borderRadius: 18,
                    border: '1px solid #6366f144',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
                      {response.card_data.title}
                    </h4>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: '#10b98122', color: '#10b981' }}>
                      Optimized Route
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Distance</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
                        ~{response.card_data.distance_km} km
                      </div>
                    </div>
                    <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Driving Time</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#60a5fa', marginTop: '2px' }}>
                        ~{response.card_data.driving_hours} hrs
                      </div>
                    </div>
                    <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Est. Diesel</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>
                        ~{response.card_data.fuel_litres} L
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr', gap: '10px' }}>
                    <div style={{ padding: '10px 14px', background: '#141422', borderRadius: 10 }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Fuel Cost:</div>
                      <strong style={{ color: '#fff' }}>₹{response.card_data.fuel_cost_inr?.toLocaleString?.()}</strong>
                    </div>
                    <div style={{ padding: '10px 14px', background: '#141422', borderRadius: 10 }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Toll Cost:</div>
                      <strong style={{ color: '#fff' }}>₹{response.card_data.toll_cost_inr?.toLocaleString?.()}</strong>
                    </div>
                    <div style={{ padding: '10px 14px', background: '#10b98118', border: '1px solid #10b98144', borderRadius: 10 }}>
                      <div style={{ fontSize: '0.7rem', color: '#10b981' }}>Total Trip Cost:</div>
                      <strong style={{ color: '#10b981', fontSize: '1.05rem' }}>₹{response.card_data.total_cost_inr?.toLocaleString?.()}</strong>
                    </div>
                  </div>

                  {/* Fuel Bunkers List */}
                  {response.card_data.fuel_stations && response.card_data.fuel_stations.length > 0 && (
                    <div style={{ marginTop: '4px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#9ca3af', marginBottom: '6px' }}>
                        ⛽ Recommended Fuel Stops:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {response.card_data.fuel_stations.map((st, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', padding: '6px 10px', background: '#141422', borderRadius: 6 }}>
                            <span>📍 {st.name} ({st.km} km)</span>
                            <span style={{ color: '#fbbf24', fontWeight: 700 }}>₹{st.price}/L</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* BREAKDOWN RECOVERY CARD */}
              {response.card_type === 'BREAKDOWN_RECOVERY' && response.card_data && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ef4444' }}>
                    🚨 Incident Reported for {response.card_data.vehicle} at {response.card_data.location}
                  </div>
                  {response.card_data.plans.map((p) => (
                    <div key={p.id} style={{ padding: '14px', background: '#202035', borderRadius: 12, border: '1px solid #3b3b54', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 800, color: '#fff', fontSize: '0.95rem' }}>{p.title}</div>
                        <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '2px' }}>{p.action}</div>
                        <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', marginTop: '6px', color: '#60a5fa' }}>
                          <span>⏱️ ETA: {p.eta_minutes} min</span>
                          <span>💰 Cost: ₹{p.cost_inr}</span>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, padding: '4px 10px', borderRadius: 8, background: '#10b98122', color: '#10b981' }}>
                        {p.score}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Text Input Fallback Footer */}
        <form
          onSubmit={handleManualSubmit}
          style={{
            padding: '16px 20px',
            borderTop: '1px solid #2d2d3d',
            background: '#19192b',
            display: 'flex',
            gap: '10px',
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={t('ask_anything', 'Type your request in English or your language...')}
            style={{
              flex: 1,
              background: '#12121f',
              border: '1px solid #3b3b54',
              borderRadius: 12,
              padding: '10px 16px',
              color: '#fff',
              fontSize: '0.9rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            style={{
              padding: '10px 18px',
              borderRadius: 12,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              opacity: inputText.trim() ? 1 : 0.5,
            }}
          >
            Send ➔
          </button>
        </form>
      </div>
    </div>
  )
}
