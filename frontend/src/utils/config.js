export function isEnabled(value, defaultValue = true) {
  if (value === undefined || value === null || value === '') return defaultValue
  return value === true || value === 'true' || value === '1' || value === 1
}

export function toNumber(value, fallback) {
  const n = Number(value)
  return Number.isFinite(n) && value !== '' && value !== null ? n : fallback
}

export function isPlaceholderUrl(value) {
  return /^(https?:\/\/)?example\./i.test(String(value || '').trim())
}
