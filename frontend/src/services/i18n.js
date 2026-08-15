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

  // Optimization Dashboard Translations
  opt_engine_title: {
    en: '🛰️ OR-Tools Multi-Vehicle Optimization Engine',
    te: '🛰️ OR-టూల్స్ మల్టీ-వెహికల్ ఆప్టిమైజేషన్ ఇంజిన్',
    hi: '🛰️ ओआर-टूल्स मल्टी-वाहन रूट अनुकूलन इंजन',
    pa: '🛰️ ਓਆਰ-ਟੂਲਸ ਮਲਟੀ-ਵਾਹਨ ਰੂਟ ਅਨੁਕੂਲਨ ਇੰਜਨ',
    mr: '🛰️ ओआर-टूल्स मल्टी-वाहन ऑप्टिमायझेशन इंजिन',
  },
  opt_engine_subtitle: {
    en: 'Automated Load Consolidation, Capacitated VRP solver, and Indian Route Cost Engine',
    te: 'స్వయంచాలక లోడ్ ఏకీకరణ, కెపాసిటేటెడ్ VRP సాల్వర్, మరియు భారతీయ మార్గ వ్యయ ఇంజిన్',
    hi: 'स्वचालित लोड समेकन, क्षमता-आधारित वीआरपी सॉल्वर और भारतीय मार्ग लागत इंजन',
    pa: 'ਆਟੋਮੇਟਿਡ ਲੋਡ ਏਕੀਕਰਨ, ਸਮਰੱਥਾ-ਅਧਾਰਤ ਵੀਆਰਪੀ ਸੋਲਵਰ ਅਤੇ ਭਾਰਤੀ ਰੂਟ ਲਾਗਤ ਇੰਜਨ',
    mr: 'स्वयंचलित लोड एकत्रीकरण, क्षमता-आधारित व्हीआरपी सॉल्व्हर आणि भारतीय मार्ग खर्च इंजिन',
  },
  fleet_status_title: {
    en: '🚛 Real-Time Fleet Status',
    te: '🚛 రియల్-టైమ్ ఫ్లీట్ స్థితి',
    hi: '🚛 रीयल-टाइम फ्लीट स्थिति',
    pa: '🚛 ਰੀਅਲ-ਟਾਈਮ ਫਲੀਟ ਸਥਿਤੀ',
    mr: '🚛 रिअल-टाइम फ्लीट स्थिती',
  },
  fleet_status_sub: {
    en: 'Monitor active transit logs, fuel efficiency levels, low fuel warnings, and operational incidents.',
    te: 'యాక్టివ్ ట్రాన్సిట్ లాగ్‌లు, ఇంధన సామర్థ్య స్థాయిలు, తక్కువ ఇంధన హెచ్చరికలు మరియు కార్యాచరణ సంఘటనలను పర్యవేక్షించండి.',
    hi: 'सक्रिय ट्रांजिट लॉग, ईंधन दक्षता स्तर, कम ईंधन चेतावनी और परिचालन घटनाओं की निगरानी करें।',
    pa: 'ਸਰਗਰਮ ਟਰਾਂਜ਼ਿਟ ਲੌਗ, ਈਂਧਨ ਕੁਸ਼ਲਤਾ ਪੱਧਰ, ਘੱਟ ਈਂਧਨ ਚੇਤਾਵਨੀਆਂ ਅਤੇ ਕਾਰਜਸ਼ੀਲ ਘਟਨਾਵਾਂ ਦੀ ਨਿਗਰਾਨੀ ਕਰੋ।',
    mr: 'सक्रिय ट्रान्झिट लॉग, इंधन कार्यक्षमता पातळी, कमी इंधन चेतावणी आणि ऑपरेशनल घटनांचे निरीक्षण करा.',
  },
  live_fleet_map_link: {
    en: 'Live Fleet Tracking Map ➔',
    te: 'లైవ్ ఫ్లీట్ ట్రాకింగ్ మ్యాప్ ➔',
    hi: 'लाइव फ्लीट ट्रैकिंग मैप ➔',
    pa: 'ਲਾਈਵ ਫਲੀਟ ਟਰੈਕਿੰਗ ਮੈਪ ➔',
    mr: 'लाइव्ह फ्लीट ट्रॅकिंग नकाशा ➔',
  },
  active_vehicles: {
    en: 'Active Vehicles',
    te: 'ప్రయాణంలో ఉన్న వాహనాలు',
    hi: 'सक्रिय वाहन',
    pa: 'ਸਰਗਰਮ ਵਾਹਨ',
    mr: 'सक्रिय वाहने',
  },
  idle_vehicles: {
    en: 'Idle Vehicles',
    te: 'ఖాళీగా ఉన్న వాహనాలు',
    hi: 'उपलब्ध / निष्क्रिय वाहन',
    pa: 'ਵਿਹਲੇ ਵਾਹਨ',
    mr: 'उपलब्ध वाहने',
  },
  low_fuel_vehicles: {
    en: 'Low Fuel Vehicles',
    te: 'తక్కువ ఇంధనం ఉన్న వాహనాలు',
    hi: 'कम ईंधन वाले वाहन',
    pa: 'ਘੱਟ ਈਂਧਨ ਵਾਲੇ ਵਾਹਨ',
    mr: 'कमी इंधन असलेली वाहने',
  },
  active_incidents: {
    en: 'Active Incidents',
    te: 'ప్రస్తుత సంఘటనలు',
    hi: 'सक्रिय घटनाएं',
    pa: 'ਸਰਗਰਮ ਘਟਨਾਵਾਂ',
    mr: 'सक्रिय घटना',
  },
  delayed_vehicles: {
    en: 'Delayed Vehicles',
    te: 'ఆలస్యమైన వాహనాలు',
    hi: 'विलंबित वाहन',
    pa: 'ਦੇਰੀ ਵਾਲੇ ਵਾਹਨ',
    mr: 'विलंबित वाहने',
  },
  total_registered_fleet: {
    en: 'Total Registered Fleet',
    te: 'మొత్తం నమోదైన వాహనాలు',
    hi: 'कुल पंजीकृत फ्लीट',
    pa: 'ਕੁੱਲ ਰਜਿਸਟਰਡ ਫਲੀਟ',
    mr: 'एकूण नोंदणीकृत फ्लीट',
  },
  prebuilt_scenarios_title: {
    en: 'Pre-Built DSS Evaluation Scenarios',
    te: 'సిద్ధంగా ఉన్న DSS మూల్యాంకన దృశ్యాలు (Scenarios)',
    hi: 'पूर्व-निर्मित डीएसएस मूल्यांकन परिदृश्य (Scenarios)',
    pa: 'ਪਹਿਲਾਂ ਤੋਂ ਬਣੇ ਡੀਐਸਐਸ ਮੁਲਾਂਕਣ ਦ੍ਰਿਸ਼',
    mr: 'पूर्व-निर्मित डीएसएस मूल्यमापन परिस्थिती',
  },
  prebuilt_scenarios_sub: {
    en: 'Select and trigger a pre-loaded business VRP scenario. The DSS will filter compatible fleet resources and optimize routing instantly.',
    te: 'ముందుగా లోడ్ చేసిన బిజినెస్ VRP దృశ్యాన్ని ఎంచుకోండి. DSS అనుకూల వనరులను ఫిల్టర్ చేసి రూటింగ్‌ను తక్షణమే ఆప్టిమైజ్ చేస్తుంది.',
    hi: 'प्री-लोडेड बिजनेस वीआरपी परिदृश्य का चयन करें और चलाएं। डीएसएस संगत फ्लीट संसाधनों को फ़िल्टर करेगा और तुरंत रूटिंग को अनुकूलित करेगा।',
    pa: 'ਪਹਿਲਾਂ ਤੋਂ ਲੋਡ ਕੀਤੇ ਕਾਰੋਬਾਰੀ ਵੀਆਰਪੀ ਦ੍ਰਿਸ਼ ਨੂੰ ਚੁਣੋ ਅਤੇ ਚਲਾਓ।',
    mr: 'प्री-लोड केलेले बिझनेस व्हीआरपी परिस्थिती निवडा आणि चालवा. डीएसएस सुसंगत संसाधने फिल्टर करेल आणि त्वरित ऑप्टिमाइझ करेल.',
  },
  tab_scenarios: {
    en: '🧪 5 Preset Scenarios',
    te: '🧪 5 సిద్ధ దృశ్యాలు',
    hi: '🧪 5 पूर्व-निर्धारित परिदृश्य',
    pa: '🧪 5 ਪ੍ਰੀਸੈਟ ਦ੍ਰਿਸ਼',
    mr: '🧪 5 पूर्व-सेट परिस्थिती',
  },
  tab_seed: {
    en: '🌱 Seed Data Hub',
    te: '🌱 సీడ్ డేటా హబ్',
    hi: '🌱 सीड डेटा हब',
    pa: '🌱 ਸੀਡ ਡਾਟਾ ਹਬ',
    mr: '🌱 सीड डेटा हब',
  },
  tab_custom: {
    en: '⚙️ Custom VRP Solver',
    te: '⚙️ కస్టమ్ VRP సాల్వర్',
    hi: '⚙️ कस्टम वीआरपी सॉल्वर',
    pa: '⚙️ ਕਸਟਮ ਵੀਆਰਪੀ ਸੋਲਵਰ',
    mr: '⚙️ सानुकूल व्हीआरपी सॉल्व्हर',
  },
  tab_consolidation: {
    en: '📦 Load Consolidation',
    te: '📦 లోడ్ ఏకీకరణ',
    hi: '📦 लोड समेकन',
    pa: '📦 ਲੋਡ ਏਕੀਕਰਨ',
    mr: '📦 लोड एकत्रीकरण',
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
