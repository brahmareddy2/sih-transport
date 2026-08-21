import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { LANGUAGES, useI18nStore } from '../../services/i18n'
import { executeVoiceCommand, transcribeAudio } from '../../services/voiceApi'
import CommunicationModal from './CommunicationModal'

// Helper function to encode AudioBuffer to standard 16-bit WAV format
function bufferToWav(buffer) {
  let numOfChan = buffer.numberOfChannels,
      length = buffer.length * numOfChan * 2 + 44,
      bufferArr = new ArrayBuffer(length),
      view = new DataView(bufferArr),
      channels = [], i, sample,
      offset = 0,
      pos = 0;

  // write WAV header
  setUint32(0x46464952);                         // "RIFF"
  setUint32(length - 8);                         // file length - 8
  setUint32(0x45564157);                         // "WAVE"

  setUint32(0x20746d66);                         // "fmt " chunk
  setUint32(16);                                 // chunk length
  setUint16(1);                                  // sample format (raw)
  setUint16(numOfChan);
  setUint32(buffer.sampleRate);
  setUint32(buffer.sampleRate * 2 * numOfChan); // byte rate
  setUint16(numOfChan * 2);                      // block align
  setUint16(16);                                 // bits per sample

  setUint32(0x61746164);                         // "data" chunk
  setUint32(length - pos - 4);                   // chunk length

  // write interleaved channels
  for(i=0; i<buffer.numberOfChannels; i++)
    channels.push(buffer.getChannelData(i));

  while(pos < length) {
    for(i=0; i<numOfChan; i++) {             // interleave channels
      sample = Math.max(-1, Math.min(1, channels[i][offset])); // clamp
      sample = (sample < 0 ? sample * 0x8000 : sample * 0x7FFF); // scale to 16-bit signed int
      view.setInt16(pos, sample, true);          // write 16-bit sample
      pos += 2;
    }
    offset++;
  }

  return new Blob([bufferArr], {type: 'audio/wav'});

  function setUint16(data) {
    view.setUint16(pos, data, true);
    pos += 2;
  }

  function setUint32(data) {
    view.setUint32(pos, data, true);
    pos += 4;
  }
}

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
  const [selectedRouteId, setSelectedRouteId] = useState('best_route')
  const [mapProgress, setMapProgress] = useState(0)

  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunksRef = useRef([])

  // Get active speech code
  const currentLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]
  const speechCode = currentLangObj.speechCode || 'en-IN'

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        console.log('[Voice Assistant] Initializing SpeechRecognition engine...');
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = true
        recognition.lang = speechCode

        recognition.onstart = () => {
          console.log('[Voice Assistant] SpeechRecognition.onstart fired: Recording started successfully.');
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
          console.log(`[Voice Assistant] SpeechRecognition.onresult fired. Interim: "${interim}", Final: "${finalTranscript}"`);
          if (interim) {
            setInterimText(interim)
          }
          if (finalTranscript) {
            setTranscript(finalTranscript)
            setInterimText('')
            setIsListening(false)
            console.log(`[Voice Assistant] Sending final transcribed text to backend: "${finalTranscript}"`);
            handleCommand(finalTranscript, false)
          }
        }

        recognition.onerror = (event) => {
          console.warn('[Voice Assistant] SpeechRecognition.onerror fired:', event.error)
          setIsListening(false)
          if (event.error === 'not-allowed') {
            setErrorMessage('⚠️ Microphone permission is blocked. Please allow mic access in your browser or type below.')
          } else if (event.error === 'no-speech') {
            setErrorMessage('⚠️ No speech detected. Please tap the mic and speak clearly.')
          } else if (event.error === 'network') {
            setErrorMessage('⚠️ Speech network timeout. You can use the instant voice test buttons or type below.')
          } else {
            setErrorMessage(`⚠️ Speech recognition error: ${event.error}`)
          }
        }

        recognition.onend = () => {
          console.log('[Voice Assistant] SpeechRecognition.onend fired: Recording stopped.');
          setIsListening(false)
        }

        recognitionRef.current = recognition
        setVoiceAvailable(true)
      } catch (e) {
        console.error('[Voice Assistant] SpeechRecognition instantiation error:', e);
        setVoiceAvailable(false)
      }
    } else {
      console.warn('[Voice Assistant] SpeechRecognition is not supported in this browser.');
      setVoiceAvailable(false)
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop(); } catch {}
      }
      if (mediaStreamRef.current) {
        try { mediaStreamRef.current.getTracks().forEach(track => track.stop()); } catch {}
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
  }, [isOpen, initialQuery])  // Handle live progress bar map animation
  useEffect(() => {
    let interval
    if (isOpen) {
      interval = setInterval(() => {
        setMapProgress((prev) => (prev >= 100 ? 0 : prev + 2))
      }, 150)
    } else {
      setMapProgress(0)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isOpen])

  // Lock body and html scroll when modal is open, restore on close/unmount
  useEffect(() => {
    if (isOpen) {
      const originalBodyOverflow = document.body.style.overflow
      const originalHtmlOverflow = document.documentElement.style.overflow
      
      document.body.style.overflow = 'hidden'
      document.documentElement.style.overflow = 'hidden'

      // Prevent scroll event bubbling to background on desktop/mobile
      const preventDefaultScroll = (e) => {
        const scrollableContent = document.getElementById('modal-scrollable-content')
        if (scrollableContent && scrollableContent.contains(e.target)) {
          return // Allow scrolling inside the assistant modal content
        }
        // Block scrolling on backdrop / background page
        if (e.cancelable) {
          e.preventDefault()
        }
      }

      window.addEventListener('wheel', preventDefaultScroll, { passive: false })
      window.addEventListener('touchmove', preventDefaultScroll, { passive: false })
      
      return () => {
        document.body.style.overflow = originalBodyOverflow
        document.documentElement.style.overflow = originalHtmlOverflow
        window.removeEventListener('wheel', preventDefaultScroll)
        window.removeEventListener('touchmove', preventDefaultScroll)
      }
    }
  }, [isOpen])


  const startListening = () => {
    setErrorMessage('')
    setResponse(null)
    setTranscript('')
    setInterimText('')

    // 1. Check for secure origin
    const isSecure = window.location.protocol === 'https:' || 
                     window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1';
    
    if (!isSecure) {
      const secureMsg = '⚠️ Microphone capture is blocked on non-secure (HTTP) origins in modern browsers. Please use localhost or connect via HTTPS.';
      console.error('[Voice Assistant] Secure origin requirement failed:', window.location.origin);
      setErrorMessage(secureMsg);
      return;
    }

    // 2. Request microphone stream via getUserMedia explicitly
    console.log('[Voice Assistant] Requesting getUserMedia microphone permission...');
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        console.log('[Voice Assistant] Microphone stream acquired successfully. Permission granted.');
        
        if (recognitionRef.current) {
          // Stop the temp stream tracks immediately to release device for SpeechRecognition
          stream.getTracks().forEach(track => track.stop());

          try {
            console.log('[Voice Assistant] Starting SpeechRecognition instance...');
            recognitionRef.current.lang = speechCode
            recognitionRef.current.start()
            setIsListening(true)
          } catch (e) {
            console.warn('[Voice Assistant] SpeechRecognition start caught exception, attempting stop & restart:', e);
            // If already started, stop and restart
            try {
              recognitionRef.current.stop()
              setTimeout(() => {
                recognitionRef.current.start()
                setIsListening(true)
              }, 200)
            } catch (err) {
              console.error('[Voice Assistant] Restart SpeechRecognition failed:', err);
              setIsListening(false)
              setErrorMessage('⚠️ Could not start speech recording device.')
            }
          }
        } else {
          // Server-side MediaRecorder fallback for Firefox/Safari
          console.log('[Voice Assistant] SpeechRecognition not supported. Using MediaRecorder fallback...');
          mediaStreamRef.current = stream;
          audioChunksRef.current = [];
          
          let mediaRecorder;
          try {
            mediaRecorder = new MediaRecorder(stream);
          } catch (err) {
            console.error('[Voice Assistant] MediaRecorder instantiation failed:', err);
            setErrorMessage('⚠️ Audio recording is not supported in this browser.');
            stream.getTracks().forEach(track => track.stop());
            setIsListening(false);
            return;
          }

          mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
              audioChunksRef.current.push(event.data);
            }
          };

          mediaRecorder.onstop = async () => {
            console.log('[Voice Assistant] MediaRecorder stopped. Processing audio chunks...');
            const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
            setLoading(true);
            try {
              let finalWavBlob = audioBlob;
              try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const arrayBuf = await audioBlob.arrayBuffer();
                const audioBuf = await audioContext.decodeAudioData(arrayBuf);
                finalWavBlob = bufferToWav(audioBuf);
                console.log('[Voice Assistant] Audio successfully decoded and converted to WAV.');
              } catch (decErr) {
                console.warn('[Voice Assistant] Audio Context decode failed, using raw recorded blob:', decErr);
              }

              const reader = new FileReader();
              reader.readAsDataURL(finalWavBlob);
              reader.onloadend = async () => {
                const base64Data = reader.result.split(',')[1];
                try {
                  console.log('[Voice Assistant] Sending audio base64 payload to backend transcribe...');
                  const transRes = await transcribeAudio(base64Data, language);
                  console.log('[Voice Assistant] Transcription response:', transRes);
                  if (transRes && transRes.text) {
                    setTranscript(transRes.text);
                    handleCommand(transRes.text, false);
                  } else {
                    setErrorMessage('⚠️ Could not transcribe speech. Try speaking louder or typing.');
                  }
                } catch (apiErr) {
                  console.error('[Voice Assistant] Transcription API failed:', apiErr);
                  setErrorMessage('⚠️ Speech transcription failed server-side.');
                } finally {
                  setLoading(false);
                }
              };
            } catch (err) {
              console.error('[Voice Assistant] Error handling recorded audio:', err);
              setErrorMessage('⚠️ Error processing voice recording.');
              setLoading(false);
            }
          };

          mediaRecorderRef.current = mediaRecorder;
          mediaRecorder.start(200); // slice chunks every 200ms
          setIsListening(true);
          setErrorMessage('');
        }
      })
      .catch((err) => {
        console.error('[Voice Assistant] getUserMedia permission check failed:', err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setErrorMessage('⚠️ Microphone permission denied. Please allow mic access in your browser settings.');
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setErrorMessage('⚠️ No microphone detected. Please plug in a microphone.');
        } else {
          setErrorMessage(`⚠️ Microphone access failed: ${err.message}`);
        }
        setIsListening(false);
      });
  }

  const stopListening = () => {
    console.log('[Voice Assistant] Stopping mic capture manually...');
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch (e) {
        console.warn('[Voice Assistant] Error calling SpeechRecognition.stop:', e);
      }
    }
    
    // Stop MediaRecorder if active
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn('[Voice Assistant] Error stopping MediaRecorder:', e);
      }
    }
    
    // Stop media stream tracks
    if (mediaStreamRef.current) {
      try {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      } catch (e) {
        console.warn('[Voice Assistant] Error stopping media stream tracks:', e);
      }
      mediaStreamRef.current = null;
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
      if (res && res.card_data && res.card_data.route_options) {
        setSelectedRouteId('best_route')
      }

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
    if (e) e.preventDefault()
    if (!inputText.trim()) return
    const query = inputText.trim()
    setInputText('')
    setTranscript(query)
    handleCommand(query, false)
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

  // Bezier calculator for dynamic lorry coordinates
  const getBezierPoint = (t, p0, p1, p2) => {
    const x = (1 - t) * (1 - t) * p0.x + 2 * (1 - t) * t * p1.x + t * t * p2.x;
    const y = (1 - t) * (1 - t) * p0.y + 2 * (1 - t) * t * p1.y + t * t * p2.y;
    return { x, y };
  };

  return createPortal(
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
          id="modal-scrollable-content"
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
          {response && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Text Summary + Speech Button */}
              {!response.requires_confirmation && (
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
              )}

              {/* DRIVER TRIP CARD */}
              {(response.card_type === 'DRIVER_TRIP_CARD' || response.card_type === 'TRIP_RESULT') && response.card_data && (() => {
                const routeOptions = response.card_data.route_options || [
                  {
                    id: 'best_route',
                    name: response.card_data.corridor_name 
                      ? `Best Route (${response.card_data.corridor_name})` 
                      : 'Best Route (NH44 Main Freight Corridor)',
                    distance_km: response.card_data.distance_km,
                    duration_hours: response.card_data.driving_hours || response.card_data.duration_hours,
                    fuel_litres: response.card_data.fuel_required_litres || response.card_data.fuel_litres,
                    fuel_cost_inr: response.card_data.fuel_cost_inr,
                    toll_cost_inr: response.card_data.toll_cost_inr,
                    total_cost_inr: response.card_data.total_cost_inr,
                    highlights: response.card_data.corridor_name?.toLowerCase()?.includes('nh16')
                      ? ['Coastal NH16 Section', 'Coastal Highway']
                      : ['Smooth 4-lane NH44', 'High Dhaba Density'],
                  }
                ];

                const activeRoute = routeOptions.find(r => r.id === selectedRouteId) || routeOptions[0];
                const activeTollsCount = response.card_data.toll_plazas && response.card_data.toll_plazas.length > 0
                  ? response.card_data.toll_plazas.length
                  : (activeRoute.id === 'best_route' ? 6 : activeRoute.id === 'fastest_route' ? 7 : 3);

                const originName = response.card_data.origin || 'Origin';
                const destName = response.card_data.destination || 'Destination';
                const isVijayawadaToVizag = 
                  (originName.toLowerCase().includes('vijayawada') && (destName.toLowerCase().includes('visakhapatnam') || destName.toLowerCase().includes('vizag'))) ||
                  ((originName.toLowerCase().includes('visakhapatnam') || originName.toLowerCase().includes('vizag')) && destName.toLowerCase().includes('vijayawada'));
                const isMumbaiPune = 
                  (originName.toLowerCase().includes('mumbai') && destName.toLowerCase().includes('pune')) ||
                  (originName.toLowerCase().includes('pune') && destName.toLowerCase().includes('mumbai'));
                const isDelhiHyd = 
                  (originName.toLowerCase().includes('delhi') && destName.toLowerCase().includes('hyderabad')) ||
                  (originName.toLowerCase().includes('hyderabad') && destName.toLowerCase().includes('delhi'));

                let tollPlazasList = [];
                
                if (selectedRouteId === 'best_route') {
                  if (response.card_data.toll_plazas && response.card_data.toll_plazas.length > 0) {
                    tollPlazasList = response.card_data.toll_plazas;
                  } else if (isVijayawadaToVizag) {
                    tollPlazasList = [
                      {"name": "Kalaparru Toll Plaza", "location": "NH-16 Section", "cost_inr": 120},
                      {"name": "Veeravalli Toll Plaza", "location": "NH-16 Section", "cost_inr": 110},
                      {"name": "Kovvuru Toll Plaza", "location": "Godavari Fourth Bridge", "cost_inr": 100},
                      {"name": "Krishnavaram Toll Plaza", "location": "NH-16 Section", "cost_inr": 120},
                      {"name": "Vempadu Toll Plaza", "location": "NH-16 Section", "cost_inr": 140},
                      {"name": "Panchvati Colony Toll Plaza", "location": "NH-516C, Visakhapatnam", "cost_inr": 130}
                    ];
                  } else if (isMumbaiPune) {
                    tollPlazasList = [
                      {"name": "Khalapur Toll Plaza", "location": "Mumbai-Pune Expressway", "cost_inr": 320},
                      {"name": "Talegaon Toll Plaza", "location": "Mumbai-Pune Expressway", "cost_inr": 280},
                      {"name": "Pune Entrance Toll Gate", "location": "Pune Bypass", "cost_inr": 150}
                    ];
                  } else if (isDelhiHyd) {
                    tollPlazasList = [
                      {"name": "Yamuna Expressway Toll Gate", "location": "Agra-Mathura Section", "cost_inr": 650},
                      {"name": "Gwalior Bypass Toll Plaza", "location": "NH44 Mile 320", "cost_inr": 380},
                      {"name": "Babina Toll Plaza", "location": "Jhansi-Lalitpur Section", "cost_inr": 320},
                      {"name": "Nagpur Outer Ring Toll Plaza", "location": "NH44 Nagpur Hub", "cost_inr": 540},
                      {"name": "Pimpalgaon Border Toll Plaza", "location": "Maharashtra-Telangana Border", "cost_inr": 480},
                      {"name": "Medchal Outer Toll Plaza", "location": "Hyderabad Entrance", "cost_inr": 480}
                    ];
                  } else {
                    tollPlazasList = [
                      {"name": `${originName} Bypass Toll Gate`, "location": "National Highway Section", "cost_inr": 380},
                      {"name": `${destName} Entrance Toll Plaza`, "location": "National Highway Section", "cost_inr": 420}
                    ];
                  }
                } else if (selectedRouteId === 'fastest_route') {
                  if (isVijayawadaToVizag) {
                    tollPlazasList = [
                      {"name": "Kalaparru Bypass Toll", "location": "NH-16 Section", "cost_inr": 150},
                      {"name": "Veeravalli Expressway Toll", "location": "NH-16 Section", "cost_inr": 160},
                      {"name": "Rajahmundry Ring Toll", "location": "NH-16 Bypass", "cost_inr": 140},
                      {"name": "Kovvuru Bridge Toll", "location": "Godavari Fourth Bridge", "cost_inr": 120},
                      {"name": "Tuni Express Bypass", "location": "NH-16 Section", "cost_inr": 180},
                      {"name": "Visakhapatnam Port Express", "location": "NH-516C, Visakhapatnam", "cost_inr": 200}
                    ];
                  } else if (isMumbaiPune) {
                    tollPlazasList = [
                      {"name": "Mumbai Port Trust Expressway Toll", "location": "Port Trust Road", "cost_inr": 420},
                      {"name": "Khalapur Express Toll Plaza", "location": "Expressway Section", "cost_inr": 380},
                      {"name": "Talegaon Express Toll Plaza", "location": "Expressway Section", "cost_inr": 320},
                      {"name": "Pune Ring Express Gate", "location": "Pune Bypass", "cost_inr": 180}
                    ];
                  } else if (isDelhiHyd) {
                    tollPlazasList = [
                      {"name": "Yamuna Expressway Toll Gate", "location": "Agra-Mathura Section", "cost_inr": 650},
                      {"name": "Agra-Lucknow Expressway Plaza", "location": "Expressway Section", "cost_inr": 780},
                      {"name": "Jhansi Link Expressway Gate", "location": "Expressway Section", "cost_inr": 420},
                      {"name": "Nagpur Outer Ring Expressway", "location": "NH44 Nagpur Hub", "cost_inr": 680},
                      {"name": "Pimpalgaon Bypass Toll", "location": "Maharashtra-Telangana Border", "cost_inr": 520},
                      {"name": "Medchal Express Toll Gate", "location": "Hyderabad Entrance", "cost_inr": 650}
                    ];
                  } else {
                    tollPlazasList = [
                      {"name": `${originName} Port Expressway Toll`, "location": "Expressway Corridor", "cost_inr": 450},
                      {"name": "Midway Express Highway Toll", "location": "Expressway Corridor", "cost_inr": 500},
                      {"name": `${destName} Outer Ring Toll Gate`, "location": "Expressway Corridor", "cost_inr": 480}
                    ];
                  }
                } else { // lowest_cost_route (Economy)
                  if (isVijayawadaToVizag) {
                    tollPlazasList = [
                      {"name": "Eluru Local NH-Pass", "location": "State Highway Bypass", "cost_inr": 80},
                      {"name": "Rajahmundry Local Pass", "location": "State Highway Bypass", "cost_inr": 70},
                      {"name": "Tuni Town Toll", "location": "State Highway Bypass", "cost_inr": 90}
                    ];
                  } else if (isMumbaiPune) {
                    tollPlazasList = [
                      {"name": "Panvel Old Highway Gate", "location": "Old Highway NH4", "cost_inr": 80},
                      {"name": "Khopoli Old Highway Gate", "location": "Old Highway NH4", "cost_inr": 90}
                    ];
                  } else if (isDelhiHyd) {
                    tollPlazasList = [
                      {"name": "Gwalior Local Bypass", "location": "State Highway Bypass", "cost_inr": 180},
                      {"name": "Jhansi Local Gate", "location": "State Highway Bypass", "cost_inr": 150},
                      {"name": "Nagpur Local Ring", "location": "State Highway Bypass", "cost_inr": 250},
                      {"name": "Adilabad Local Toll", "location": "State Highway Bypass", "cost_inr": 220}
                    ];
                  } else {
                    tollPlazasList = [
                      {"name": "Local State Highway Bypass Gate", "location": "State Highway Section", "cost_inr": 180}
                    ];
                  }
                }

                // Bezier coordinates logic for live lorry movement
                const tVal = mapProgress / 100;
                const p0 = { x: 40, y: 50 };
                const p2 = { x: 320, y: 50 };
                const p1 = selectedRouteId === 'best_route' 
                  ? { x: 180, y: 15 } 
                  : selectedRouteId === 'fastest_route' 
                  ? { x: 180, y: 85 } 
                  : { x: 180, y: 50 };
                const truckPos = getBezierPoint(tVal, p0, p1, p2);

                return (
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
                        {response.card_data.corridor_name || response.card_data.title || `${response.card_data.origin} ➔ ${response.card_data.destination}`}
                      </h4>
                      <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: '#10b98122', color: '#10b981' }}>
                        AI Route Solver
                      </span>
                    </div>

                    {/* Route Option Tabs Switcher */}
                    <div style={{ display: 'flex', gap: '8px', background: '#141422', padding: '4px', borderRadius: 10 }}>
                      {routeOptions.map((opt) => (
                        <button
                          key={opt.id}
                          onClick={() => setSelectedRouteId(opt.id)}
                          style={{
                            flex: 1,
                            padding: '8px 4px',
                            borderRadius: 8,
                            border: 'none',
                            background: selectedRouteId === opt.id ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                            color: selectedRouteId === opt.id ? '#fff' : '#9ca3af',
                            fontWeight: 800,
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                          }}
                        >
                          {opt.id === 'best_route' ? '⭐ Best' : opt.id === 'fastest_route' ? '⚡ Fastest' : '🪙 Economy'}
                        </button>
                      ))}
                    </div>

                    {/* Map Visualizer */}
                    <div style={{ background: '#0f0f1c', borderRadius: 12, padding: '12px', border: '1px solid #2d2d48' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#9ca3af' }}>🗺️ Live Navigation Route</span>
                        <span style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 800 }}>NH16 Corridor</span>
                      </div>
                      <div style={{ height: '110px', width: '100%', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="100%" height="100%" viewBox="0 0 360 100" style={{ position: 'absolute', top: 0, left: 0 }}>
                          <defs>
                            <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#34d399" />
                              <stop offset="50%" stopColor="#6366f1" />
                              <stop offset="100%" stopColor="#a855f7" />
                            </linearGradient>
                          </defs>
                          <line x1="0" y1="25" x2="360" y2="25" stroke="#1c1c2e" strokeDasharray="4,4" />
                          <line x1="0" y1="50" x2="360" y2="50" stroke="#1c1c2e" strokeDasharray="4,4" />
                          <line x1="0" y1="75" x2="360" y2="75" stroke="#1c1c2e" strokeDasharray="4,4" />
                          
                          <path
                            d={
                              selectedRouteId === 'best_route' 
                                ? "M 40 50 Q 180 15, 320 50" 
                                : selectedRouteId === 'fastest_route'
                                ? "M 40 50 Q 180 85, 320 50"
                                : "M 40 50 L 180 50 L 320 50"
                            }
                            fill="none"
                            stroke="url(#routeGradient)"
                            strokeWidth="4"
                            strokeDasharray="8,4"
                            strokeDashoffset={-mapProgress}
                            style={{ transition: 'all 0.5s ease-in-out' }}
                          />

                          {/* Animated Moving Lorry */}
                          <g transform={`translate(${truckPos.x - 10}, ${truckPos.y - 12})`} style={{ transition: 'transform 0.15s linear' }}>
                            <text fontSize="18">🚚</text>
                          </g>

                          {/* Render Toll Markers (red) */}
                          <circle cx="110" cy={selectedRouteId === 'best_route' ? 36 : selectedRouteId === 'fastest_route' ? 64 : 50} r="4" fill="#ef4444" />
                          <circle cx="180" cy={selectedRouteId === 'best_route' ? 32 : selectedRouteId === 'fastest_route' ? 68 : 50} r="4" fill="#ef4444" />
                          <circle cx="250" cy={selectedRouteId === 'best_route' ? 36 : selectedRouteId === 'fastest_route' ? 64 : 50} r="4" fill="#ef4444" />

                          {/* Render Sleep/Rest Stops (green) */}
                          <circle cx="140" cy={selectedRouteId === 'best_route' ? 34 : selectedRouteId === 'fastest_route' ? 66 : 50} r="4" fill="#10b981" />
                          <circle cx="210" cy={selectedRouteId === 'best_route' ? 34 : selectedRouteId === 'fastest_route' ? 66 : 50} r="4" fill="#10b981" />

                          {/* Start Point */}
                          <circle cx="40" cy="50" r="7" fill="#10b981" stroke="#fff" strokeWidth="1.5" />
                          <text x="40" y="72" fill="#fff" fontSize="9" fontWeight="bold" textAnchor="middle">
                            {response.card_data.origin}
                          </text>

                          {/* End Point */}
                          <circle cx="320" cy="50" r="7" fill="#8b5cf6" stroke="#fff" strokeWidth="1.5" />
                          <text x="320" y="72" fill="#fff" fontSize="9" fontWeight="bold" textAnchor="middle">
                            {response.card_data.destination}
                          </text>
                        </svg>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                      <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }}>Distance</div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
                          ~{activeRoute.distance_km} km
                        </div>
                      </div>
                      <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }}>Driving Time</div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#60a5fa', marginTop: '2px' }}>
                          ~{activeRoute.duration_hours} hrs
                        </div>
                      </div>
                      <div style={{ padding: '12px', background: '#141422', borderRadius: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: '0.68rem', color: '#9ca3af', textTransform: 'uppercase' }}>Est. Diesel</div>
                        <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>
                          ~{activeRoute.fuel_litres} L
                        </div>
                      </div>
                    </div>

                    {/* Cost Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr', gap: '10px' }}>
                      <div style={{ padding: '10px 14px', background: '#141422', borderRadius: 10 }}>
                        <div style={{ fontSize: '0.68rem', color: '#9ca3af' }}>Fuel Cost:</div>
                        <strong style={{ color: '#fff', fontSize: '0.85rem' }}>₹{activeRoute.fuel_cost_inr?.toLocaleString?.()}</strong>
                      </div>
                      <div style={{ padding: '10px 14px', background: '#141422', borderRadius: 10 }}>
                        <div style={{ fontSize: '0.68rem', color: '#9ca3af' }}>Tolls ({activeTollsCount} Plazas):</div>
                        <strong style={{ color: '#fff', fontSize: '0.85rem' }}>₹{activeRoute.toll_cost_inr?.toLocaleString?.()}</strong>
                      </div>
                      <div style={{ padding: '10px 14px', background: '#10b98118', border: '1px solid #10b98144', borderRadius: 10 }}>
                        <div style={{ fontSize: '0.68rem', color: '#10b981' }}>Total Trip Cost:</div>
                        <strong style={{ color: '#10b981', fontSize: '0.95rem' }}>₹{activeRoute.total_cost_inr?.toLocaleString?.()}</strong>
                      </div>
                    </div>

                    {/* Rest Areas & Sleep spots */}
                    {(() => {
                      const isNH16 = 
                        response.card_data.corridor_name?.toLowerCase().includes('nh16') ||
                        response.card_data.origin?.toLowerCase().includes('guntur') ||
                        response.card_data.origin?.toLowerCase().includes('srikakulam') ||
                        response.card_data.origin?.toLowerCase().includes('vijayawada') ||
                        response.card_data.destination?.toLowerCase().includes('guntur') ||
                        response.card_data.destination?.toLowerCase().includes('srikakulam') ||
                        response.card_data.destination?.toLowerCase().includes('vijayawada');

                      const restAreasList = isNH16 
                        ? [
                            {
                              name: "🚚 NH16 Gated Layby (Rajahmundry Bypass)",
                              desc: "Free 24/7 Secure Truck Parking, Clean Washrooms, Benches, and driver resting quarters."
                            },
                            {
                              name: "⛽ BPCL Highway Oasis (Tuni Comfort Station)",
                              desc: "Western/Indian toilets, Bathing facilities, CCTV security, and food stalls."
                            }
                          ]
                        : [
                            {
                              name: "🚚 NH44 Truck Layby & Rest Oasis (Nagpur Bypass)",
                              desc: "Free 24/7 Secure Parking, Public Bathrooms, Sleeping Rooms & Bathing Showers."
                            },
                            {
                              name: "⛽ BPCL Highway Oasis (Adilabad Plaza)",
                              desc: "Clean Restrooms, Driver Rest Quarters, Washrooms, and CCTV Monitored Lorry Parking."
                            }
                          ];

                      return (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            💤 Free Sleep & Bath Rest Areas (For Lorry Drivers):
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {restAreasList.map((area, idx) => (
                              <div key={idx} style={{ padding: '10px 12px', background: '#141422', borderRadius: 10, fontSize: '0.78rem', border: '1px solid #2d2d48' }}>
                                <span style={{ fontWeight: 800, color: '#fff' }}>{area.name}</span>
                                <div style={{ color: '#9ca3af', marginTop: '2px' }}>{area.desc}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })()}

                    {/* Toll Plazas Detailed List */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        🛣️ Toll Plaza Details ({activeTollsCount} Plazas along the Route):
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '150px', overflowY: 'auto', paddingRight: '4px' }}>
                        {tollPlazasList.slice(0, activeTollsCount).map((toll, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: '8px 12px',
                              background: '#141422',
                              borderRadius: 10,
                              fontSize: '0.78rem',
                              border: '1px solid #2d2d48',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center'
                            }}
                          >
                            <div>
                              <span style={{ fontWeight: 800, color: '#fff' }}>📍 {toll.name}</span>
                              <div style={{ color: '#9ca3af', fontSize: '0.72rem', marginTop: '1px' }}>{toll.location}</div>
                            </div>
                            <span style={{ fontWeight: 800, color: '#f87171' }}>₹{toll.cost_inr}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })()}

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
            disabled={loading}
            onClick={handleManualSubmit}
            style={{
              padding: '12px 20px',
              background: loading ? '#4b4b6b' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              borderRadius: 12,
              fontWeight: 800,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Sending...' : 'Send ➔'}
          </button>
        </form>
      </div>

      {/* Communication Bridge Modal */}
      <CommunicationModal
        isOpen={isCommOpen}
        onClose={() => setIsCommOpen(false)}
        contactData={commTarget}
      />
    </div>,
    document.body
  )
}
