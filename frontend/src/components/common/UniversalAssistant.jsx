import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { LANGUAGES, useI18nStore } from '../../services/i18n'
import { executeVoiceCommand } from '../../services/voiceApi'
import VoiceAssistantModal from '../voice/VoiceAssistantModal'

export default function UniversalAssistant({ placeholder, autoFocus = false, onResult = null }) {
  const navigate = useNavigate()
  const { language, detectAndSetLanguage, t } = useI18nStore()
  const [query, setQuery] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalQuery, setModalQuery] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  const recognitionRef = useRef(null)

  const currentLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]
  const speechCode = currentLangObj.speechCode || 'en-IN'

  // Initialize Web Speech API
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
          setStatusMessage('🎤 Listening to your voice... Speak now!')
        }

        recognition.onresult = (event) => {
          let interim = ''
          let final = ''
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              final += event.results[i][0].transcript
            } else {
              interim += event.results[i][0].transcript
            }
          }
          if (interim) {
            setQuery(interim)
          }
          if (final) {
            setQuery(final)
            setIsListening(false)
            handleSubmitQuery(final)
          }
        }

        recognition.onerror = (event) => {
          console.warn('Speech recognition error in UniversalAssistant:', event.error)
          setIsListening(false)
          if (event.error === 'not-allowed') {
            setStatusMessage('⚠️ Microphone access blocked. Please type in search bar.')
          } else if (event.error === 'no-speech') {
            setStatusMessage('⚠️ No speech detected. Please tap mic again.')
          }
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        recognitionRef.current = recognition
      } catch (err) {
        console.warn('SpeechRecognition init error:', err)
      }
    }
  }, [speechCode])

  const toggleMic = () => {
    setStatusMessage('')
    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {}
      }
      setIsListening(false)
    } else {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.lang = speechCode
          recognitionRef.current.start()
          setIsListening(true)
        } catch (e) {
          // If already started, open assistant modal
          setIsModalOpen(true)
        }
      } else {
        // Fallback open Voice Assistant Modal
        setIsModalOpen(true)
      }
    }
  }

  const handleSubmitQuery = async (queryText) => {
    const textToRun = (queryText || query).trim()
    if (!textToRun) return

    const activeLang = detectAndSetLanguage(textToRun) || language
    setLoading(true)
    setStatusMessage('⚡ Processing with AI Logistics Engine...')

    try {
      const res = await executeVoiceCommand({
        query: textToRun,
        language: activeLang,
      })

      setLoading(false)
      setStatusMessage('')

      // If user is planning a trip, navigate to full TripPlanner
      const lowered = textToRun.toLowerCase()
      if (
        res.intent === 'TRIP_PLANNING' ||
        lowered.includes('delhi') ||
        lowered.includes('hyderabad') ||
        lowered.includes('vellali') ||
        lowered.includes('వెళ్లాలి') ||
        lowered.includes('route')
      ) {
        navigate('/trip-planner', { state: { initialPlan: res.data || res.card_data, query: textToRun } })
      } else {
        // Open the interactive modal to display the visual card response
        setModalQuery(textToRun)
        setIsModalOpen(true)
      }

      if (onResult) {
        onResult(res)
      }
    } catch (err) {
      setLoading(false)
      setStatusMessage('')
      setModalQuery(textToRun)
      setIsModalOpen(true)
    }
  }

  const onSubmitForm = (e) => {
    e.preventDefault()
    handleSubmitQuery(query)
  }

  const SUGGESTIONS = [
    { label: 'Delhi to Hyderabad', query: 'Route from Delhi to Hyderabad' },
    { label: 'ఢిల్లీ నుండి హైదరాబాద్', query: 'నేను ఢిల్లీ నుండి హైదరాబాద్ వెళ్లాలి' },
    { label: 'నా లారీ పంక్చర్ అయ్యింది', query: 'నా లారీ టైర్ పంక్చర్ అయ్యింది' },
    { label: 'ఈరోజు నా లాభం ఎంత?', query: 'ఈరోజు నా లాభం ఎంత?' },
    { label: 'దగ్గరలో మంచి రెస్టారెంట్', query: 'నాకు దగ్గరలో మంచి రెస్టారెంట్ ఎక్కడ ఉంది?' },
    { label: 'నా వాహనాలు ఎక్కడ ఉన్నాయి?', query: 'నా వాహనాలు ఎక్కడ ఉన్నాయి?' },
  ]

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <form
        onSubmit={onSubmitForm}
        style={{
          display: 'flex',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #1b1b30, #141424)',
          border: isListening ? '2px solid #ef4444' : '1px solid #3b3b5c',
          borderRadius: 16,
          padding: '6px 8px',
          boxShadow: isListening
            ? '0 0 25px rgba(239, 68, 68, 0.4)'
            : '0 8px 30px rgba(0, 0, 0, 0.35)',
          gap: '8px',
          transition: 'all 0.25s',
        }}
      >
        {/* 🎤 Microphone Button */}
        <button
          type="button"
          onClick={toggleMic}
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: isListening
              ? 'linear-gradient(135deg, #ef4444, #dc2626)'
              : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none',
            color: '#fff',
            fontSize: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: isListening ? '0 0 20px rgba(239, 68, 68, 0.7)' : '0 0 15px rgba(99, 102, 241, 0.4)',
            transition: 'all 0.2s',
          }}
          title={isListening ? 'Stop Recording' : 'Start Voice Recording'}
        >
          {isListening ? '🛑' : '🎤'}
        </button>

        {/* Search Input */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            placeholder ||
            (language === 'te'
              ? 'ఏదైనా అడగండి... ఉదా: ఢిల్లీ నుండి హైదరాబాద్, భోజనం, పంక్చర్...'
              : language === 'hi'
              ? 'कुछ भी पूछें... जैसे: दिल्ली से हैदराबाद रूट, खाना, ढाबा...'
              : 'Search or Ask anything... e.g. Delhi to Hyderabad, food, puncture, today\'s profit...')
          }
          autoFocus={autoFocus}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            color: '#fff',
            fontSize: '0.95rem',
            outline: 'none',
            padding: '8px',
          }}
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={loading || !query.trim()}
          style={{
            padding: '10px 18px',
            borderRadius: 12,
            background: query.trim() ? 'linear-gradient(135deg, #10b981, #059669)' : '#27273a',
            color: query.trim() ? '#fff' : '#6b7280',
            border: 'none',
            fontWeight: 800,
            fontSize: '0.9rem',
            cursor: query.trim() ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s',
          }}
        >
          <span>{loading ? '⏳' : 'Send'}</span>
          <span>➔</span>
        </button>
      </form>

      {/* Live Status Message & Suggestions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px', padding: '0 4px' }}>
        {statusMessage ? (
          <div style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 700 }}>
            {statusMessage}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 700 }}>Quick Ask:</span>
            {SUGGESTIONS.slice(0, 3).map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(s.query)
                  handleSubmitQuery(s.query)
                }}
                style={{
                  background: '#19192b',
                  border: '1px solid #2e2e48',
                  borderRadius: 14,
                  padding: '3px 10px',
                  color: '#a5b4fc',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#818cf8',
            fontSize: '0.75rem',
            fontWeight: 700,
            cursor: 'pointer',
            textDecoration: 'underline',
          }}
        >
          Open Voice Assistant ➔
        </button>
      </div>

      {/* Universal Voice Assistant Modal */}
      <VoiceAssistantModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setModalQuery('')
        }}
        initialQuery={modalQuery}
      />
    </div>
  )
}
