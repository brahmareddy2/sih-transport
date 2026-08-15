import en from './en.json'
import te from './te.json'
import hi from './hi.json'
import pa from './pa.json'
import mr from './mr.json'

export const translations = { en, te, hi, pa, mr }

export function getNestedTranslation(obj, keyPath) {
  if (!obj || !keyPath) return null
  const keys = keyPath.split('.')
  let curr = obj
  for (const k of keys) {
    if (curr && typeof curr === 'object' && k in curr) {
      curr = curr[k]
    } else {
      return null
    }
  }
  return typeof curr === 'string' ? curr : null
}

export function translate(keyPath, lang = 'en', fallback = '') {
  const dict = translations[lang] || translations.en
  const res = getNestedTranslation(dict, keyPath)
  if (res) return res
  const enRes = getNestedTranslation(translations.en, keyPath)
  return enRes || fallback || keyPath
}
