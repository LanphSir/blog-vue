// 公告关闭记忆：以 localStorage 记录某条公告的「已读版本号」。
// 注意键要带公告 id（blog_notice_dismissed:{id}），且比对的是 version 而非是否有关闭标记——
// 后台改一次内容版本号就 +1，旧版本用户会因此重新看到公告。
const PREFIX = 'blog_notice_dismissed:'

export function isNoticeDismissed(id, version) {
  return localStorage.getItem(PREFIX + id) === String(version)
}

export function dismissNotice(id, version) {
  localStorage.setItem(PREFIX + id, String(version))
}
