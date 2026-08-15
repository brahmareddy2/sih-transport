import React, { useState } from 'react'

export default function CommunicationModal({ isOpen, onClose, contactData }) {
  const [callState, setCallState] = useState('IDLE') // IDLE, DIALING, CONNECTED, ENDED

  if (!isOpen || !contactData) return null

  const handleStartCall = () => {
    setCallState('DIALING')
    setTimeout(() => {
      setCallState('CONNECTED')
    }, 2000)
  }

  const handleEndCall = () => {
    setCallState('ENDED')
    setTimeout(() => {
      setCallState('IDLE')
      onClose()
    }, 1200)
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 99999,
        background: 'rgba(0,0,0,0.8)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          background: '#16162a',
          border: '1px solid #3b3b5c',
          borderRadius: 24,
          padding: '28px',
          boxShadow: '0 25px 60px rgba(0,0,0,0.7)',
          textAlign: 'center',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase' }}>
            🔒 Safe Telephony Bridge
          </span>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              fontSize: '1.4rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Contact Icon & Name */}
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: '50%',
            background: callState === 'CONNECTED' ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2.2rem',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.4)',
            marginBottom: '16px',
            animation: callState === 'DIALING' ? 'pulse 1.5s infinite' : 'none',
          }}
        >
          {callState === 'CONNECTED' ? '📞' : '📱'}
        </div>

        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', margin: '0 0 6px' }}>
          {contactData.target_name || contactData.name || 'Highway Service Contact'}
        </h3>
        <p style={{ fontSize: '0.82rem', color: '#9ca3af', margin: '0 0 12px' }}>
          {contactData.location || 'Indian Freight Corridor'}
        </p>

        {/* Phone display */}
        <div
          style={{
            background: '#1c1c34',
            padding: '10px 16px',
            borderRadius: 12,
            fontSize: '1rem',
            fontWeight: 700,
            color: '#10b981',
            letterSpacing: '0.05em',
            marginBottom: '16px',
            display: 'inline-block',
          }}
        >
          {contactData.phone_display || contactData.phone || '+91 98765 44210'}
        </div>

        {/* Status indicator */}
        <div style={{ marginBottom: '24px', fontSize: '0.9rem', fontWeight: 600 }}>
          {callState === 'IDLE' && <span style={{ color: '#9ca3af' }}>Ready to connect secure call</span>}
          {callState === 'DIALING' && <span style={{ color: '#f59e0b' }}>Dialing carrier gateway...</span>}
          {callState === 'CONNECTED' && <span style={{ color: '#10b981' }}>🟢 Connected (00:14) • Speaking</span>}
          {callState === 'ENDED' && <span style={{ color: '#ef4444' }}>Call Terminated</span>}
        </div>

        {/* Action buttons */}
        {callState === 'IDLE' ? (
          <button
            onClick={handleStartCall}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 14,
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(16, 185, 129, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <span>📞</span>
            <span>START CALL NOW</span>
          </button>
        ) : (
          <button
            onClick={handleEndCall}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 14,
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(239, 68, 68, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <span>🛑</span>
            <span>END CALL</span>
          </button>
        )}

        <div style={{ marginTop: '16px', fontSize: '0.72rem', color: '#6b7280', lineHeight: 1.4 }}>
          {contactData.disclaimer || 'Demo call mode — configure Twilio/WebRTC provider for production VoIP routing.'}
        </div>
      </div>
    </div>
  )
}
