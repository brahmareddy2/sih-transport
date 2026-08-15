import React, { useState, useEffect, useRef } from 'react'
import { LANGUAGES, useI18nStore } from '../../services/i18n'
import { executeVoiceCommand } from '../../services/voiceApi'
import CommunicationModal from './CommunicationModal'

export default function VoiceAssistantModal({ isOpen, onClose, initialQuery = '' }) {
  const { language, setLanguage, detectAndSetLanguage, t } = useI18nStore()
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimText, setInterimText] = useState('')
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [speaking, setSpeaking] = useState(false)
  const [voiceAvailable, setVoiceAvailable] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [commTarget, setCommTarget] = useState(null)
  const [isCommOpen, setIsCommOpen] = useState(false)

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
        recognition.interimResults = true
        recognition.lang = speechCode

        recognition.onstart = () => {
          setIsListening(true)
          setErrorMessage('')
        }

        recognition.onresult = (event) => {
          let interim = ''
          let finalTranscript = ''
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript
            } else {
              interim += event.results[i][0].transcript
            }
          }
          if (interim) {
            setInterimText(interim)
          }
          if (finalTranscript) {
            setTranscript(finalTranscript)
            setInterimText('')
            setIsListening(false)
            handleCommand(finalTranscript, false)
          }
        }

        recognition.onerror = (event) => {
          console.warn('Speech recognition error:', event.error)
          setIsListening(false)
          if (event.error === 'not-allowed') {
            setErrorMessage('⚠️ Microphone permission is blocked. Please allow mic access in your browser or type below.')
          } else if (event.error === 'no-speech') {
            setErrorMessage('⚠️ No speech detected. Please tap the mic and speak clearly.')
          } else if (event.error === 'network') {
            setErrorMessage('⚠️ Speech network timeout. You can use the instant voice test buttons or type below.')
          }
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

  // Handle initial query on open
  useEffect(() => {
    if (isOpen) {
      setErrorMessage('')
      if (initialQuery && initialQuery.trim()) {
        setInputText(initialQuery)
        setTranscript(initialQuery)
        handleCommand(initialQuery, false)
      }
    }
  }, [isOpen, initialQuery])

  const startListening = () => {
    setErrorMessage('')
    setResponse(null)
    setTranscript('')
    setInterimText('')
    if (recognitionRef.current) {
      try {
        recognitionRef.current.lang = speechCode
        recognitionRef.current.start()
        setIsListening(true)
      } catch (e) {
        // If already started, stop and restart
        try {
          recognitionRef.current.stop()
          setTimeout(() => recognitionRef.current.start(), 200)
          setIsListening(true)
        } catch (err) {
          setIsListening(false)
        }
      }
    } else {
      setErrorMessage('Speech recognition is not supported in this browser. Please type your query or use the test voice buttons.')
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
    const activeLang = detectAndSetLanguage(queryText) || language
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await executeVoiceCommand({
        query: queryText,
        language: activeLang,
        confirmed: isConfirmed,
        action_payload: actionPayload,
      })
      setResponse(res)

      // Auto-speak response if speech synthesis available
      if (res && res.speech_text) {
        speakText(res.speech_text, activeLang)
      }
    } catch (err) {
      setResponse({
        text: 'Sorry, I could not process that request. Please try typing or select a test query below.',
        speech_text: 'Sorry, I could not process that request.',
        language: activeLang,
        requires_confirmation: false,
      })
    } finally {
      setLoading(false)
    }
  }

  const speakText = (textToSpeak, targetLang = language) => {
    if (!window.speechSynthesis) return
    try {
      window.speechSynthesis.cancel()
      const langObj = LANGUAGES.find((l) => l.code === targetLang) || currentLangObj
      const utterance = new SpeechSynthesisUtterance(textToSpeak)
      utterance.lang = langObj.speechCode || speechCode
      utterance.rate = 0.92
      utterance.pitch = 1.0
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

  const QUICK_TEST_QUERIES = [
    { label: 'ఢిల్లీ నుండి హైదరాబాద్', query: 'నేను ఢిల్లీ నుండి హైదరాబాద్ వెళ్ళాలి', lang: 'te', icon: '🇮🇳' },
    { label: 'భోజనం ఎక్కడ దొరుకుతుంది?', query: 'నాకు దగ్గర్లో భోజనం ఎక్కడ దొరుకుతుంది?', lang: 'te', icon: '🍛' },
    { label: 'నాకు పంక్చర్ అయ్యింది', query: 'నా లారీ టైర్ పంక్చర్ అయ్యింది', lang: 'te', icon: '⚙️' },
    { label: 'Route Delhi to Hyderabad', query: 'Plan a trip from Delhi to Hyderabad', lang: 'en', icon: '🗺️' },
    { label: 'Today\'s Profit & Fuel', query: 'How much did I earn today and what is my profit?', lang: 'en', icon: '📊' },
    { label: 'दिल्ली से हैदराबाद', query: 'मुझे दिल्ली से हैदराबाद जाना है', lang: 'hi', icon: '🇮🇳' },
  ]

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(10, 10, 20, 0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        fontFamily: "'Inter', sans-serif",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '700px',
          background: '#16162a',
          border: '1px solid #3b3b5c',
          borderRadius: 24,
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7)',
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
            padding: '18px 24px',
            borderBottom: '1px solid #2d2d44',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#1c1c34',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: 42,
                height: 42,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.3rem',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)',
              }}
            >
              🎤
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
                {t('voice_assistant', 'Universal Voice & Search Assistant')}
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#a5b4fc', fontWeight: 600 }}>
                {currentLangObj.flag} {currentLangObj.native} ({currentLangObj.name})
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#9ca3af',
              fontSize: '1.6rem',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div
          style={{
            padding: '24px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          {/* Microphone Visualizer & Status */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              background: isListening ? '#6366f118' : speaking ? '#10b98118' : '#121222',
              borderRadius: 20,
              border: isListening ? '2px solid #6366f1' : speaking ? '2px solid #10b981' : '1px solid #2d2d44',
              transition: 'all 0.3s',
            }}
          >
            <button
              onClick={isListening ? stopListening : startListening}
              style={{
                width: 84,
                height: 84,
                borderRadius: '50%',
                background: isListening
                  ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                  : speaking
                  ? 'linear-gradient(135deg, #10b981, #059669)'
                  : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                border: 'none',
                color: '#fff',
                fontSize: '2.2rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: isListening
                  ? '0 0 35px rgba(239, 68, 68, 0.7)'
                  : speaking
                  ? '0 0 35px rgba(16, 185, 129, 0.7)'
                  : '0 0 30px rgba(99, 102, 241, 0.5)',
                transform: isListening ? 'scale(1.08)' : 'scale(1)',
                transition: 'all 0.2s',
              }}
            >
              {isListening ? '🛑' : speaking ? '🔊' : '🎤'}
            </button>

            <div style={{ marginTop: '14px', textAlign: 'center' }}>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: isListening ? '#f87171' : speaking ? '#34d399' : '#a5b4fc' }}>
                {isListening
                  ? t('listening', 'Listening to your voice... Speak now!')
                  : speaking
                  ? '🔊 Assistant is Speaking Audio Response...'
                  : t('tap_to_speak', 'Tap Mic to Speak in English, Telugu, Hindi, etc.')}
              </span>
            </div>

            {/* Live Interim / Final Speech Text Display */}
            {(interimText || transcript) && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '10px 18px',
                  background: '#1c1c34',
                  borderRadius: 12,
                  border: '1px solid #3b3b5c',
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: interimText ? '#a5b4fc' : '#fff',
                  maxWidth: '92%',
                  textAlign: 'center',
                }}
              >
                "{interimText || transcript}"
              </div>
            )}

            {/* Error Message Display */}
            {errorMessage && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '10px 16px',
                  background: '#ef444422',
                  borderRadius: 10,
                  border: '1px solid #ef444455',
                  fontSize: '0.82rem',
                  color: '#f87171',
                  textAlign: 'center',
                }}
              >
                {errorMessage}
              </div>
            )}
          </div>

          {/* Quick 1-Click Voice Test Chips */}
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#9ca3af', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ⚡ 1-Click Voice Test (Telugu & English):
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {QUICK_TEST_QUERIES.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setTranscript(q.query)
                    handleCommand(q.query, false)
                  }}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 20,
                    background: '#1c1c34',
                    border: '1px solid #3b3b5c',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#6366f122'
                    e.currentTarget.style.borderColor = '#6366f1'
                    e.currentTarget.style.color = '#fff'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#1c1c34'
                    e.currentTarget.style.borderColor = '#3b3b5c'
                    e.currentTarget.style.color = '#e2e8f0'
                  }}
                >
                  <span>{q.icon}</span>
                  <span>{q.label}</span>
                </button>
              ))}
            </div>
          </div>

          {loading && (
            <div style={{ textAlign: 'center', padding: '16px', color: '#a5b4fc', fontSize: '0.95rem', fontWeight: 700 }}>
              ⚡ Processing with AI Logistics Engine...
            </div>
          )}

          {/* Confirmation Checkpoint Dialog */}
          {response && response.requires_confirmation && (
            <div
              style={{
                padding: '20px',
                background: '#2b2310',
                border: '1px solid #f59e0b',
                borderRadius: 18,
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.3rem' }}>⚠️</span>
                <span style={{ fontWeight: 800, color: '#fbbf24', fontSize: '1rem' }}>
                  Confirmation Required
                </span>
              </div>
              <div style={{ fontSize: '0.95rem', color: '#fef3c7', lineHeight: 1.5 }}>
                {response.text}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '6px' }}>
                <button
                  type="button"
                  onClick={() => handleCommand(transcript || 'Yes', true, response.action_payload)}
                  style={{
                    padding: '12px',
                    borderRadius: 10,
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 800,
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                  }}
                >
                  ✓ {t('yes_confirm', 'Yes, Confirm')}
                </button>
                <button
                  type="button"
                  onClick={() => setResponse(null)}
                  style={{
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
                  background: '#1c1c34',
                  borderRadius: 16,
                  border: '1px solid #3b3b5c',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ fontSize: '0.95rem', color: '#e2e8f0', lineHeight: 1.5 }}>
                    {response.text}
                  </div>
                  <button
                    onClick={() => speakText(response.speech_text || response.text, response.language)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: 10,
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                      color: '#fff',
                      border: 'none',
                      fontWeight: 800,
                      fontSize: '0.82rem',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <span>🔊</span>
                    <span>{t('listen', 'Listen')}</span>
                  </button>
                </div>
              </div>

              {/* DRIVER TRIP CARD */}
              {(response.card_type === 'DRIVER_TRIP_CARD' || response.card_type === 'TRIP_RESULT') && response.card_data && (
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
                      {response.card_data.title || `${response.card_data.origin} ➔ ${response.card_data.destination}`}
                    </h4>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: '#10b98122', color: '#10b981' }}>
                      AI Route Solver
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
                        ~{response.card_data.fuel_required_litres || response.card_data.fuel_litres} L
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
                </div>
              )}

              {/* FACILITIES LIST CARD */}
              {response.card_type === 'FACILITIES_LIST' && response.card_data && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#a5b4fc' }}>
                    {response.card_data.title}
                  </div>
                  {response.card_data.facilities.map((fac) => (
                    <div
                      key={fac.id}
                      style={{
                        padding: '14px',
                        background: '#1a1a30',
                        borderRadius: 12,
                        border: '1px solid #2d2d48',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 800, color: '#fff', fontSize: '0.95rem' }}>{fac.name}</div>
                        <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: '2px' }}>📍 {fac.highway}</div>
                        {fac.cuisine && <div style={{ fontSize: '0.78rem', color: '#38bdf8', marginTop: '2px' }}>🍽️ {fac.cuisine} • {fac.avg_cost}</div>}
                        {fac.fee && <div style={{ fontSize: '0.78rem', color: '#34d399', marginTop: '2px' }}>🏷️ {fac.fee} ({fac.capacity})</div>}
                        {fac.cleanliness_score && <div style={{ fontSize: '0.78rem', color: '#a78bfa', marginTop: '2px' }}>✨ {fac.cleanliness_score}</div>}
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 800, padding: '4px 8px', borderRadius: 6, background: '#10b98122', color: '#34d399' }}>
                          {fac.distance_km} km
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* PUNCTURE ASSISTANCE CARD */}
              {response.card_type === 'PUNCTURE_ASSISTANCE' && response.card_data && (
                <div style={{ padding: '18px', background: '#251a24', border: '1px solid #ef444466', borderRadius: 16 }}>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: '#f87171', marginBottom: '10px' }}>
                    {response.card_data.title}
                  </div>
                  <div style={{ background: '#18121a', padding: '12px', borderRadius: 10, marginBottom: '12px' }}>
                    <div style={{ fontWeight: 800, color: '#fff' }}>{response.card_data.nearest_shop?.name}</div>
                    <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>📍 {response.card_data.nearest_shop?.highway} ({response.card_data.nearest_shop?.distance_km} km away)</div>
                    <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 700, marginTop: '4px' }}>📞 {response.card_data.nearest_shop?.phone}</div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => {
                        setCommTarget(response.card_data.nearest_shop)
                        setIsCommOpen(true)
                      }}
                      style={{
                        flex: 1,
                        padding: '10px',
                        background: 'linear-gradient(135deg, #10b981, #059669)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 10,
                        fontWeight: 800,
                        cursor: 'pointer',
                      }}
                    >
                      📞 Call Shop
                    </button>
                    <button
                      onClick={() => alert('Incident recovery created in Phase 5 Incident Engine.')}
                      style={{
                        flex: 1,
                        padding: '10px',
                        background: '#dc2626',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 10,
                        fontWeight: 800,
                        cursor: 'pointer',
                      }}
                    >
                      🚨 Create Incident
                    </button>
                  </div>
                </div>
              )}

              {/* FUEL STATUS CARD */}
              {response.card_type === 'FUEL_STATUS' && response.card_data && (
                <div style={{ padding: '18px', background: '#1c1c34', border: '1px solid #f59e0b44', borderRadius: 16 }}>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: '#fbbf24', marginBottom: '10px' }}>
                    ⛽ Vehicle Fuel Level & Telemetry
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                    <div style={{ padding: '10px', background: '#121222', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Fuel Level</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fbbf24' }}>{response.card_data.fuel_pct}%</div>
                    </div>
                    <div style={{ padding: '10px', background: '#121222', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Remaining Litres</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>{response.card_data.fuel_litres || response.card_data.fuel_level_l} L</div>
                    </div>
                    <div style={{ padding: '10px', background: '#121222', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Estimated Range</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34d399' }}>~{response.card_data.range_km} km</div>
                    </div>
                  </div>
                </div>
              )}

              {/* OWNER FINANCIAL SUMMARY CARD */}
              {response.card_type === 'OWNER_FINANCIAL_SUMMARY' && response.card_data && (
                <div style={{ padding: '18px', background: '#1c1c34', border: '1px solid #6366f144', borderRadius: 16 }}>
                  <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginBottom: '14px' }}>
                    {response.card_data.title}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '12px' }}>
                    <div style={{ padding: '10px', background: '#121222', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Revenue</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34d399' }}>₹{response.card_data.revenue_inr?.toLocaleString?.()}</div>
                    </div>
                    <div style={{ padding: '10px', background: '#121222', borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Expenses</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f87171' }}>₹{response.card_data.expenses?.total_expense_inr?.toLocaleString?.()}</div>
                    </div>
                    <div style={{ padding: '10px', background: '#10b98122', borderRadius: 8, textAlign: 'center', border: '1px solid #10b98144' }}>
                      <div style={{ fontSize: '0.7rem', color: '#10b981' }}>Est. Net Profit</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10b981' }}>₹{response.card_data.estimated_profit_inr?.toLocaleString?.()}</div>
                    </div>
                  </div>
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
            borderTop: '1px solid #2d2d44',
            background: '#19192b',
            display: 'flex',
            gap: '10px',
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={t('search_placeholder', 'Ask anything... e.g. Route Delhi to Hyderabad, food, parking...')}
            style={{
              flex: 1,
              background: '#121220',
              border: '1px solid #3b3b54',
              borderRadius: 12,
              padding: '12px 16px',
              color: '#fff',
              fontSize: '0.95rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            style={{
              padding: '12px 20px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              borderRadius: 12,
              fontWeight: 800,
              cursor: 'pointer',
            }}
          >
            Send ➔
          </button>
        </form>
      </div>

      {/* Communication Bridge Modal */}
      <CommunicationModal
        isOpen={isCommOpen}
        onClose={() => setIsCommOpen(false)}
        contactData={commTarget}
      />
    </div>
  )
}
