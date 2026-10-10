const PREFIX = 'blog_notice_dismissed:'

export function isNoticeDismissed(id, version) {
  return localStorage.getItem(PREFIX + id) === String(version)
}

export function dismissNotice(id, version) {
  localStorage.setItem(PREFIX + id, String(version))
}
