// 评论头像：不上传文件，按昵称哈希取色 + 首字符渲染（同昵称全站颜色稳定）。
const PALETTE = [
  '#409eff',
  '#67c23a',
  '#e6a23c',
  '#f56c6c',
  '#909399',
  '#9254de',
  '#13c2c2',
  '#fa8c16',
  '#eb2f96',
  '#52c41a',
]

export function avatarColor(nickname) {
  const name = String(nickname || '?')
  // djb2 哈希：字符串短，取模色板即可稳定分布
  let hash = 5381
  for (let i = 0; i < name.length; i++) hash = ((hash << 5) + hash + name.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
}

export function avatarText(nickname) {
  const name = String(nickname || '').trim()
  return name ? [...name][0].toUpperCase() : '?'
}

// 打开评论表单时的默认昵称：用户_ + 4 位随机数（访客可改）
export function randomNickname() {
  return `用户_${Math.floor(1000 + Math.random() * 9000)}`
}

// 相对时间：刚刚 / x 分钟前 / x 小时前 / x 天前 / YYYY-MM-DD
// 解析方式与 PostDetail 现有 formatDate 一致（后端返回 naive 本地时间串）
export function fromNow(value) {
  if (!value) return ''
  const diff = Date.now() - new Date(value).getTime()
  if (Number.isNaN(diff)) return String(value).slice(0, 10)
  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  if (diff < 30 * 86400_000) return `${Math.floor(diff / 86400_000)} 天前`
  return String(value).slice(0, 10)
}
