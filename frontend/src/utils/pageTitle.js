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
