// 全局“请求活动中”总线（0.14.0）：页面加载动画的数据源。
// axios 拦截器 beginActivity/endActivity 计数；PageLoading 订阅。
// 与路由事件的区别：路由 afterEach 只代表地址变了，页面真正的空白期是
// “数据还没回来”，所以动画必须跟着请求走而不是跟着地址栏走。
const listeners = new Set()
let pending = 0

export function beginActivity() {
  pending += 1
  if (pending === 1) {
    for (const fn of listeners) fn(true)
  }
}

export function endActivity() {
  pending = Math.max(0, pending - 1)
  if (pending === 0) {
    for (const fn of listeners) fn(false)
  }
}

/** 订阅活动状态变化，返回退订函数。 */
export function onActivityChange(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}
