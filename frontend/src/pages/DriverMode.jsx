import React, { useState } from 'react'
import { useI18nStore } from '../services/i18n'
import VoiceAssistantModal from '../components/voice/VoiceAssistantModal'
import UniversalSearchBar from '../components/common/UniversalSearchBar'
import DriverAssistant from '../components/voice/DriverAssistant'

export default function DriverMode() {
  const { language, t } = useI18nStore()
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)
  const [initialVoiceQuery, setInitialVoiceQuery] = useState('')

  const handleSearchSubmit = (query) => {
    setInitialVoiceQuery(query)
    setIsVoiceOpen(true)
  }

  return (
    <div
      style={{
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '24px 16px',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* 1. Large Universal Search Bar with embedded mic */}
      <UniversalSearchBar
        onSearch={handleSearchSubmit}
        onOpenVoice={() => {
          setInitialVoiceQuery('')
          setIsVoiceOpen(true)
        }}
      />

      {/* 2. Driver Assistant Cockpit */}
      <DriverAssistant
        onOpenVoice={() => {
          setInitialVoiceQuery('')
          setIsVoiceOpen(true)
        }}
        onPlanTrip={(orig, dest) => {
          setInitialVoiceQuery(`Plan trip from ${orig} to ${dest}`)
          setIsVoiceOpen(true)
        }}
      />

      {/* 3. Universal Voice & Search Modal */}
      <VoiceAssistantModal
        isOpen={isVoiceOpen}
        onClose={() => {
          setIsVoiceOpen(false)
          setInitialVoiceQuery('')
        }}
        initialQuery={initialVoiceQuery}
      />
    </div>
  )
}
