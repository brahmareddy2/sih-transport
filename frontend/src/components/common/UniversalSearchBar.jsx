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
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 18,
          padding: '6px 10px 6px 18px',
          boxShadow: 'var(--shadow-card)',
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
            color: 'var(--color-text-primary)',
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
          onClick={handleSubmit}
          style={{
            background: 'var(--color-bg-primary)',
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: '10px 16px',
            color: 'var(--color-text-primary)',
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
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', alignSelf: 'center', whiteSpace: 'nowrap' }}>
          💡 Try asking:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleChipClick(s.query)}
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 20,
              padding: '4px 12px',
              color: 'var(--color-text-secondary)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#6366f122'
              e.currentTarget.style.borderColor = '#6366f1'
              e.currentTarget.style.color = 'var(--color-text-primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-bg-secondary)'
              e.currentTarget.style.borderColor = 'var(--color-border)'
              e.currentTarget.style.color = 'var(--color-text-secondary)'
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}
