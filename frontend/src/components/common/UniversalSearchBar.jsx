import React, { useState } from 'react'
import { useI18nStore } from '../../services/i18n'

export default function UniversalSearchBar({ onSearch, onOpenVoice }) {
  const { language, t } = useI18nStore()
  const [query, setQuery] = useState('')

  const SUGGESTIONS = [
    { label: 'Delhi to Hyderabad', query: 'Plan trip from Delhi to Hyderabad' },
    { label: '🍛 Food on route', query: 'Where can I eat near my route?' },
    { label: '🅿️ Free Parking', query: 'Find free parking near me' },
    { label: '🚻 Clean Restroom', query: 'Find nearest clean restroom' },
    { label: '⚙️ Puncture Help', query: 'My vehicle has a tyre puncture' },
    { label: '📊 Today\'s Profit', query: 'How much did I earn today and what is my profit?' },
  ]

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return
    if (onSearch) {
      onSearch(query.trim())
    }
  }

  const handleChipClick = (itemQuery) => {
    setQuery(itemQuery)
    if (onSearch) {
      onSearch(itemQuery)
    }
  }

  return (
    <div style={{ width: '100%', marginBottom: '20px' }}>
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#16162a',
          border: '1px solid #3b3b5c',
          borderRadius: 18,
          padding: '6px 10px 6px 18px',
          boxShadow: '0 8px 25px rgba(0,0,0,0.4)',
          transition: 'all 0.2s',
        }}
      >
        <span style={{ fontSize: '1.2rem', marginRight: '10px', color: '#6366f1' }}>🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('search_placeholder', "Ask anything... e.g. 'Route Delhi to Hyderabad', 'Where can I eat?', 'Where are my vehicles?'")}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#fff',
            fontSize: '0.95rem',
            fontWeight: 500,
          }}
        />

        {/* 🎤 Voice Trigger Button */}
        <button
          type="button"
          onClick={onOpenVoice}
          title="Speak via Microphone"
          style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none',
            borderRadius: 12,
            width: 42,
            height: 42,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
            cursor: 'pointer',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
            marginLeft: '8px',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          🎤
        </button>

        {/* Search Submit Button */}
        <button
          type="submit"
          style={{
            background: '#2d2d48',
            border: '1px solid #4a4a6e',
            borderRadius: 12,
            padding: '10px 16px',
            color: '#fff',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer',
            marginLeft: '8px',
          }}
        >
          Search ➔
        </button>
      </form>

      {/* Suggestion Chips */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
        <span style={{ fontSize: '0.72rem', color: '#6b7280', alignSelf: 'center', whiteSpace: 'nowrap' }}>
          💡 Try asking:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleChipClick(s.query)}
            style={{
              background: '#1c1c34',
              border: '1px solid #2d2d48',
              borderRadius: 20,
              padding: '4px 12px',
              color: '#cbd5e1',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#6366f122'
              e.currentTarget.style.borderColor = '#6366f1'
              e.currentTarget.style.color = '#fff'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#1c1c34'
              e.currentTarget.style.borderColor = '#2d2d48'
              e.currentTarget.style.color = '#cbd5e1'
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}
