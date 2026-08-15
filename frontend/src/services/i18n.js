/**
 * Internationalization (i18n) Dictionary — Phase 8
 * Supports 5 Indian Languages:
 * - en: English
 * - te: Telugu (తెలుగు)
 * - hi: Hindi (हिन्दी)
 * - pa: Punjabi (ਪੰਜਾਬੀ)
 * - mr: Marathi (मराठी)
 */
import { create } from 'zustand'

export const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', speechCode: 'en-IN', flag: '🌐' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', speechCode: 'te-IN', flag: '🇮🇳' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', speechCode: 'hi-IN', flag: '🇮🇳' },
  { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', speechCode: 'pa-IN', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', speechCode: 'mr-IN', flag: '🇮🇳' },
]

export const DICTIONARY = {
  // Navigation & Header
  app_title: {
    en: 'Logistics DSS',
    te: 'లాజిస్టిక్స్ డీఎస్ఎస్',
    hi: 'लॉजिस्टिक्स डीएसएस',
    pa: 'ਲਾਜਿਸਟਿਕਸ ਡੀਐਸਐਸ',
    mr: 'लॉजिस्टिक्स डीएसएस',
  },
  voice_assistant: {
    en: 'Voice Assistant',
    te: 'వాయిస్ అసిస్టెంట్',
    hi: 'वॉयस असिस्टेंट',
    pa: 'ਵੌਇਸ ਅਸਿਸਟੈਂਟ',
    mr: 'व्हॉइस असिस्टंट',
  },
  speak: {
    en: 'Speak',
    te: 'మాట్లాడండి',
    hi: 'बोलें',
    pa: 'ਬੋਲੋ',
    mr: 'बोला',
  },
  ask_anything: {
    en: 'Ask anything...',
    te: 'ఏదైనా అడగండి...',
    hi: 'कुछ भी पूछें...',
    pa: 'ਕੁਝ ਵੀ ਪੁੱਛੋ...',
    mr: 'काहीही विचारा...',
  },
  simple_mode: {
    en: 'Simple Mode',
    te: 'సరళ మోడ్',
    hi: 'सरल मोड',
    pa: 'ਸਧਾਰਨ ਮੋਡ',
    mr: 'सोपा मोड',
  },
  normal_mode: {
    en: 'Enterprise Mode',
    te: 'ఎంటర్‌ప్రైజ్ మోడ్',
    hi: 'एंटरप्राइज मोड',
    pa: 'ਐਂਟਰਪ੍ਰਾਈਜ਼ ਮੋਡ',
    mr: 'एंटरप्राइज मोड',
  },
  sign_out: {
    en: 'Sign Out',
    te: 'లాగ్ అవుట్',
    hi: 'साइन आउट',
    pa: 'ਸਾਈਨ ਆਉਟ',
    mr: 'साइन आउट',
  },

  // Driver Mode
  hello_driver: {
    en: '👋 Hello Driver',
    te: '👋 నమస్కారం డ్రైవర్ గారు',
    hi: '👋 नमस्ते ड्राइवर',
    pa: '👋 ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਡਰਾਈਵਰ',
    mr: '👋 नमस्कार ड्रायव्हर',
  },
  tell_me_what_you_need: {
    en: 'Tell me what you need or tap a quick button below.',
    te: 'మీకు ఏమి కావాలో చెప్పండి లేదా క్రింది బటన్‌ను నొక్కండి.',
    hi: 'बताएं आपको क्या चाहिए या नीचे दिए गए बटन को दबाएं।',
    pa: 'ਦੱਸੋ ਤੁਹਾਨੂੰ ਕੀ ਚਾਹੀਦਾ ਹੈ ਜਾਂ ਹੇਠਾਂ ਦਿੱਤੇ ਬਟਨ ਨੂੰ ਦਬਾਓ।',
    mr: 'तुम्हाला काय हवे आहे ते सांगा किंवा खालील बटण दाबा.',
  },
  my_trip: {
    en: '🚛 My Active Trip',
    te: '🚛 నా ప్రయాణం',
    hi: '🚛 मेरी यात्रा',
    pa: '🚛 ਮੇਰਾ ਸਫ਼ਰ',
    mr: '🚛 माझा प्रवास',
  },
  emergency_help: {
    en: '🚨 Emergency Quick Help',
    te: '🚨 అత్యవసర సహాయం',
    hi: '🚨 आपातकालीन त्वरित सहायता',
    pa: '🚨 ਐਮਰਜੈਂਸੀ ਮਦਦ',
    mr: '🚨 तातडीची मदत',
  },
  breakdown: {
    en: 'Breakdown',
    te: 'బ్రేక్‌డౌన్',
    hi: 'गाड़ी खराब',
    pa: 'ਬ੍ਰੇਕਡਾਊਨ',
    mr: 'गाडी बिघाड',
  },
  accident: {
    en: 'Accident',
    te: 'ప్రమాదం',
    hi: 'दुर्घटना',
    pa: 'ਹਾਦਸਾ',
    mr: 'अपघात',
  },
  low_fuel: {
    en: 'Low Fuel',
    te: 'తక్కువ ఇంధనం',
    hi: 'कम ईंधन',
    pa: 'ਘੱਟ ਈਂਧਨ',
    mr: 'कमी इंधन',
  },
  tyre_problem: {
    en: 'Tyre Problem',
    te: 'టైర్ సమస్య',
    hi: 'टायर समस्या',
    pa: 'ਟਾਇਰ ਸਮੱਸਿਆ',
    mr: 'टायर समस्या',
  },
  check_return_load: {
    en: '🔄 Check Return Load',
    te: '🔄 తిరుగు ప్రయాణ లోడ్ తనిఖీ',
    hi: '🔄 वापसी लोड चेक करें',
    pa: '🔄 ਵਾਪਸੀ ਲੋਡ ਚੈੱਕ ਕਰੋ',
    mr: '🔄 परतीचा माल तपासा',
  },

  // Confirmation dialog
  yes_confirm: {
    en: 'Yes, Confirm',
    te: 'అవును, నిర్ధారించండి',
    hi: 'हाँ, पुष्टि करें',
    pa: 'ਹਾਂ, ਪੁਸ਼ਟੀ ਕਰੋ',
    mr: 'होय, पुष्टी करा',
  },
  no_change: {
    en: 'No, Change',
    te: 'కాదు, మార్చండి',
    hi: 'नहीं, बदलें',
    pa: 'ਨਹੀਂ, ਬਦਲੋ',
    mr: 'नाही, बदला',
  },
  listen: {
    en: '🔊 Listen',
    te: '🔊 వినండి',
    hi: '🔊 सुनें',
    pa: '🔊 ਸੁਣੋ',
    mr: '🔊 ऐका',
  },
}

export const useI18nStore = create((set, get) => ({
  language: localStorage.getItem('app_language') || 'en',
  simpleMode: localStorage.getItem('app_simple_mode') === 'true',

  setLanguage: (langCode) => {
    localStorage.setItem('app_language', langCode)
    set({ language: langCode })
  },

  setSimpleMode: (enabled) => {
    localStorage.setItem('app_simple_mode', String(enabled))
    set({ simpleMode: enabled })
  },

  t: (key, fallback = '') => {
    const lang = get().language || 'en'
    const entry = DICTIONARY[key]
    if (!entry) return fallback || key
    return entry[lang] || entry['en'] || fallback || key
  },
}))
