// 社交平台预设：名称/品牌色/徽章字母。平台要么是这里的预设 key，要么是 custom（自己填 label）。
// platformMeta 对未知/空平台返回 null，调用方据此回退到中性灰样式。
export const PLATFORMS = {
  github: { name: 'GitHub', color: '#333333', letter: 'G' },
  juejin: { name: '掘金', color: '#1E80FF', letter: '掘' },
  zhihu: { name: '知乎', color: '#0084FF', letter: '知' },
  csdn: { name: 'CSDN', color: '#FC5531', letter: 'C' },
  x: { name: 'X', color: '#000000', letter: 'X' },
  email: { name: '邮箱', color: '#EA4335', letter: '@' },
  wechat: { name: '微信', color: '#07C160', letter: '微' },
  bilibili: { name: 'B 站', color: '#FB7299', letter: 'B' },
}

export const PLATFORM_OPTIONS = Object.entries(PLATFORMS).map(([value, meta]) => ({
  value,
  label: meta.name,
}))

export function platformMeta(platform) {
  return PLATFORMS[String(platform || '').toLowerCase()] || null
}
