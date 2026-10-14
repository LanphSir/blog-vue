// 站点配置工具。后台配置里的布尔开关以字符串 "true"/"false" 存到数据库，
// 所以这里不能直接拿 truthy 判断——必须统一走 isEnabled/toNumber 解析，
// 否则 `if (config)` 这种写法会把字符串 "false" 也当成开启。
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
