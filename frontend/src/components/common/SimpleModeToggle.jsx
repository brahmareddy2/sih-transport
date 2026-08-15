import React from 'react'
import { useI18nStore } from '../../services/i18n'

export default function SimpleModeToggle({ style = {} }) {
  const { simpleMode, setSimpleMode, t } = useI18nStore()

  return (
    <button
      onClick={() => setSimpleMode(!simpleMode)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        background: simpleMode ? '#10b98122' : '#6366f122',
        color: simpleMode ? '#10b981' : '#a5b4fc',
        border: `1px solid ${simpleMode ? '#10b98166' : '#6366f166'}`,
        borderRadius: 8,
        padding: '6px 12px',
        fontSize: '0.82rem',
        fontWeight: 700,
        cursor: 'pointer',
        transition: 'all 0.2s',
        ...style,
      }}
      title="Toggle Simple / Normal Mode"
    >
      <span>{simpleMode ? '✨' : '⚙️'}</span>
      <span>{simpleMode ? t('simple_mode', 'Simple Mode') : t('normal_mode', 'Enterprise')}</span>
    </button>
  )
}
