// 页面标题拼装：`路由标题 · 站点名`，缺站点名回退到默认名。
// 路由标题与站点名是分开设置的（路由守卫 + 站点配置各自写入），
// 所以 apply() 读的是两份状态而非直接拼一次。
const DEFAULT_NAME = '个人博客'

let routeTitle = ''
let siteName = ''

function apply() {
  const name = siteName || DEFAULT_NAME
  document.title = routeTitle ? `${routeTitle} · ${name}` : name
}

export function setSiteName(name) {
  siteName = (name || '').trim()
  apply()
}

export function setRouteTitle(title) {
  routeTitle = (title || '').trim()
  apply()
}
