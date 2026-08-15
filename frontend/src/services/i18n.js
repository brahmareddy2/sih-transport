/**
 * Internationalization (i18n) Dictionary & Adaptive Language Detection — Phase 8
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
  // Navigation & Top Bar
  app_title: {
    en: 'Logistics DSS',
    te: 'లాజిస్టిక్స్ డీఎస్ఎస్',
    hi: 'लॉजिस्टिक्स डीएसएस',
    pa: 'ਲਾਜਿਸਟਿਕਸ ਡੀਐਸਐਸ',
    mr: 'लॉजिस्टिक्स डीएसएस',
  },
  nav_home: {
    en: '🏠 Home',
    te: '🏠 హోమ్',
    hi: '🏠 होम',
    pa: '🏠 ਹੋਮ',
    mr: '🏠 होम',
  },
  nav_driver: {
    en: '🚛 Driver',
    te: '🚛 డ్రైవర్',
    hi: '🚛 ड्राइवर',
    pa: '🚛 ਡਰਾਈਵਰ',
    mr: '🚛 ड्रायव्हर',
  },
  nav_optimization: {
    en: '🛰️ Optimization',
    te: '🛰️ ఆప్టిమైజేషన్',
    hi: '🛰️ रूट अनुकूलन',
    pa: '🛰️ ਰੂਟ ਅਨੁਕੂਲਨ',
    mr: '🛰️ ऑप्टिमायझेशन',
  },
  nav_gps: {
    en: '📍 Live GPS',
    te: '📍 లైవ్ జీపీఎస్',
    hi: '📍 लाइव जीपीएस',
    pa: '📍 ਲਾਈਵ ਜੀਪੀਐਸ',
    mr: '📍 लाइव्ह जीपीएस',
  },
  nav_incidents: {
    en: '🚨 Incidents',
    te: '🚨 ఇన్సిడెంట్స్',
    hi: '🚨 घटनाएं',
    pa: '🚨 ਘਟਨਾਵਾਂ',
    mr: '🚨 आपत्कालीन घटना',
  },
  nav_return_cargo: {
    en: '🔄 Return Cargo',
    te: '🔄 తిరుగు సరుకు',
    hi: '🔄 वापसी लोड',
    pa: '🔄 ਵਾਪਸੀ ਲੋਡ',
    mr: '🔄 परतीचा माल',
  },
  nav_ml: {
    en: '📊 AI/ML',
    te: '📊 ఏఐ మోడల్స్',
    hi: '📊 एआई/एमएल',
    pa: '📊 ਏਆਈ/ਐਮਐਲ',
    mr: '📊 एआय मॉडेल्स',
  },
  nav_what_if: {
    en: '⚡ What-If',
    te: '⚡ వాట్-ఇఫ్',
    hi: '⚡ वॉट-इफ',
    pa: '⚡ ਵੌਟ-ਇਫ',
    mr: '⚡ व्हॉट-इफ',
  },
  nav_analytics: {
    en: '📈 Analytics',
    te: '📈 అనలిటిక్స్',
    hi: '📈 एनालिटिक्स',
    pa: '📈 ਵਿਸ਼ਲੇਸ਼ਣ',
    mr: '📈 विश्लेषण',
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

  // Login Page Translations
  select_language_title: {
    en: '🌐 Choose Your Preferred Language',
    te: '🌐 మీ ప్రాధాన్య భాషను ఎంచుకోండి',
    hi: '🌐 अपनी पसंदीदा भाषा चुनें',
    pa: '🌐 ਆਪਣੀ ਪਸੰਦੀਦਾ ਭਾਸ਼ਾ ਚੁਣੋ',
    mr: '🌐 तुमची पसंतीची भाषा निवडा',
  },
  select_language_sub: {
    en: 'The application and Voice Assistant will operate in your chosen language.',
    te: 'అప్లికేషన్ మరియు వాయిస్ అసిస్టెంట్ మీరు ఎంచుకున్న భాషలో పనిచేస్తాయి.',
    hi: 'एप्लिकेशन और वॉयस असिस्टेंट आपकी चुनी हुई भाषा में काम करेंगे।',
    pa: 'ਐਪਲੀਕੇਸ਼ਨ ਅਤੇ ਵੌਇਸ ਅਸਿਸਟੈਂਟ ਤੁਹਾਡੀ ਚੁਣੀ ਹੋਈ ਭਾਸ਼ਾ ਵਿੱਚ ਕੰਮ ਕਰਨਗੇ।',
    mr: 'अ‍ॅप्लिकेशन आणि व्हॉइस असिस्टंट तुमच्या निवडलेल्या भाषेत काम करतील.',
  },
  login_portal_title: {
    en: 'Logistics DSS Portal',
    te: 'లాజిస్టిక్స్ డీఎస్ఎస్ పోర్టల్',
    hi: 'लॉजिस्टिक्स डीएसएस पोर्टल',
    pa: 'ਲਾਜਿਸਟਿਕਸ ਡੀਐਸਐਸ ਪੋਰਟਲ',
    mr: 'लॉजिस्टिक्स डीएसएस पोर्टल',
  },
  login_portal_sub: {
    en: 'AI-Powered Multi-Vehicle Logistics Decision Support System',
    te: 'AI ఆధారిత మల్టీ-వెహికల్ లాజిస్టిక్స్ ఆప్టిమైజేషన్ సిస్టమ్',
    hi: 'एआई-संचालित मल्टी-वाहन लॉजिस्टिक्स डिसीजन सपोर्ट सिस्टम',
    pa: 'ਏਆਈ-ਸੰਚਾਲਿਤ ਮਲਟੀ-ਵਾਹਨ ਲੌਜਿਸਟਿਕਸ ਫੈਸਲਾ ਸਹਾਇਤਾ ਪ੍ਰਣਾਲੀ',
    mr: 'एआय-संचलित मल्टी-वाहन लॉजिस्टिक्स निर्णय समर्थन प्रणाली',
  },
  single_click_login: {
    en: '⚡ 1-Click Instant Sign In / Login',
    te: '⚡ 1-క్లిక్ తక్షణ లాగిన్ / సైన్ ఇన్',
    hi: '⚡ 1-क्लिक त्वरित साइन इन / लॉगिन',
    pa: '⚡ 1-ਕਲਿੱਕ ਤੁਰੰਤ ਸਾਈਨ ਇਨ / ਲੌਗਇਨ',
    mr: '⚡ 1-क्लिक झटपट साइन इन / लॉगिन',
  },
  no_typing_needed: {
    en: 'Tap your role to enter',
    te: 'ప్రవేశించడానికి మీ పాత్రను తాకండి',
    hi: 'प्रवेश करने के लिए अपनी भूमिका पर टैप करें',
    pa: 'ਦਾਖਲ ਹੋਣ ਲਈ ਆਪਣੀ ਭੂਮਿਕਾ ਤੇ ਟੈਪ ਕਰੋ',
    mr: 'प्रवेश करण्यासाठी तुमची भूमिका टॅप करा',
  },
  or_enter_credentials: {
    en: 'OR ENTER CREDENTIALS',
    te: 'లేదా వివరాలను నమోదు చేయండి',
    hi: 'या क्रेडेंशियल दर्ज करें',
    pa: 'ਜਾਂ ਵੇਰਵੇ ਦਰਜ ਕਰੋ',
    mr: 'किंवा लॉगिन तपशील प्रविष्ट करा',
  },
  email_label: {
    en: 'Email Address',
    te: 'ఇమెయిల్ చిరునామా',
    hi: 'ईमेल पता',
    pa: 'ਈਮੇਲ ਪਤਾ',
    mr: 'ईमेल पत्ता',
  },
  password_label: {
    en: 'Password',
    te: 'పాస్‌వర్డ్',
    hi: 'पासवर्ड',
    pa: 'ਪਾਸਵਰਡ',
    mr: 'पासवर्ड',
  },
  sign_in_btn: {
    en: 'Sign In / Log In ➔',
    te: 'సైన్ ఇన్ / లాగిన్ ➔',
    hi: 'साइन इन / लॉगिन ➔',
    pa: 'ਸਾਈਨ ਇਨ / ਲੌਗਇਨ ➔',
    mr: 'साइन इन / लॉगिन ➔',
  },

  // Role labels
  role_admin: { en: 'Admin', te: 'అడ్మిన్', hi: 'एडमिन', pa: 'ਐਡਮਿਨ', mr: 'अ‍ॅडमिन' },
  role_operator: { en: 'Operator', te: 'ఆపరేటర్', hi: 'ऑपरेटर', pa: 'ਆਪਰੇਟਰ', mr: 'ऑपरेटर' },
  role_fleet: { en: 'Fleet Mgr', te: 'ఫ్లీట్ మేనేజర్', hi: 'फ्लीट मैनेजर', pa: 'ਫਲੀਟ ਮੈਨੇਜਰ', mr: 'फ्लीट मॅनेजर' },
  role_driver: { en: 'Driver', te: 'డ్రైవర్', hi: 'ड्राइवर', pa: 'ਡਰਾਈਵਰ', mr: 'ड्रायव्हर' },
  role_customer: { en: 'Enterprise Customer', te: 'ఎంటర్‌ప్రైజ్ కస్టమర్', hi: 'एंटरप्राइज कस्टमर', pa: 'ਐਂਟਰਪ੍ਰਾਈਜ਼ ਗਾਹਕ', mr: 'एंटरप्राइज ग्राहक' },

  // Driver Cockpit
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

  // Automatic spoken language detection & dynamic UI switching
  detectAndSetLanguage: (text) => {
    if (!text || typeof text !== 'string') return get().language
    const clean = text.trim()

    // 1. Telugu Unicode Range [\u0C00-\u0C7F]
    if (/[\u0C00-\u0C7F]/.test(clean)) {
      get().setLanguage('te')
      return 'te'
    }
    // 2. Punjabi Unicode Range [\u0A00-\u0A7F]
    if (/[\u0A00-\u0A7F]/.test(clean)) {
      get().setLanguage('pa')
      return 'pa'
    }
    // 3. Devanagari Unicode Range [\u0900-\u097F] (Marathi vs Hindi)
    if (/[\u0900-\u097F]/.test(clean)) {
      const isMarathi = ['आहे', 'नाही', 'कुठे', 'जायचे', 'झाला', 'कसा', 'गाडी', 'तास'].some((w) => clean.includes(w))
      const code = isMarathi ? 'mr' : 'hi'
      get().setLanguage(code)
      return code
    }
    return get().language
  },

  t: (key, fallback = '') => {
    const lang = get().language || 'en'
    const entry = DICTIONARY[key]
    if (!entry) return fallback || key
    return entry[lang] || entry['en'] || fallback || key
  },
}))
