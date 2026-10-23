// 评论者身份记忆：昵称/邮箱存 localStorage，同一浏览器下次评论自动带出，
// 免去重填；「换一个身份」清空并按随机昵称重新开始（无账号体系，纯本机记忆）。
const KEY = 'blog_comment_identity'

export function getIdentity() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || 'null')
    if (raw && typeof raw.nickname === 'string' && raw.nickname) {
      return { nickname: raw.nickname, email: typeof raw.email === 'string' ? raw.email : '' }
    }
  } catch {
    /* 存坏了就当没有 */
  }
  return null
}

export function saveIdentity(nickname, email) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ nickname, email: email || '' }))
  } catch {
    /* 无痕模式等写入失败，忽略 */
  }
}

export function clearIdentity() {
  localStorage.removeItem(KEY)
}
