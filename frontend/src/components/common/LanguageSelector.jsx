import React from 'react'
import { LANGUAGES, useI18nStore } from '../../services/i18n'

export default function LanguageSelector({ style = {} }) {
  const { language, setLanguage } = useI18nStore()

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', ...style }}>
      <span style={{ fontSize: '0.9rem' }}>🌐</span>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        style={{
          background: '#1a1a2e',
          color: '#e2e8f0',
          border: '1px solid #3b3b54',
          borderRadius: 8,
          padding: '6px 12px',
          fontSize: '0.85rem',
          fontWeight: 600,
          cursor: 'pointer',
          outline: 'none',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} style={{ background: '#13131f', color: '#fff' }}>
            {lang.native} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  )
}
