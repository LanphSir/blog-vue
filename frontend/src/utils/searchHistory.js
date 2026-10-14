// 搜索历史：存 localStorage，上限 10 条，新词去重后插到最前。
// 所有读写都 try/catch——隐私模式/存满等场景写不进去也必须静默降级，不能抛错中断搜索。
const STORAGE_KEY = 'blog_search_history'
const MAX_ITEMS = 10

export function loadHistory() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(raw) ? raw.filter((v) => typeof v === 'string' && v.trim()).slice(0, MAX_ITEMS) : []
  } catch {
    return []
  }
}

function save(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch {
    // 隐私模式等写入失败时静默降级
  }
  return list
}

export function addHistory(keyword) {
  const word = String(keyword || '').trim()
  if (!word) return loadHistory()
  const rest = loadHistory().filter((v) => v.toLowerCase() !== word.toLowerCase())
  return save([word, ...rest].slice(0, MAX_ITEMS))
}

export function removeHistory(keyword) {
  return save(loadHistory().filter((v) => v !== keyword))
}

export function clearHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
  return []
}
