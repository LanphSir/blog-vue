// 通用防抖：wait 毫秒内的重复触发按配置合并，避免频繁操作引发冗余请求。
// leading=true 首次立即执行（点击要跟手），trailing=false 期间触发一律忽略；
// 默认是经典尾部防抖（停止 wait 后执行最后一次）。
export function debounce(fn, wait = 300, { leading = false, trailing = true } = {}) {
  let timer = null
  let lastArgs = null
  const debounced = (...args) => {
    lastArgs = args
    if (leading && timer === null) {
      fn(...args)
      lastArgs = null
    }
    if (trailing) {
      clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        if (lastArgs !== null) fn(...lastArgs)
        lastArgs = null
      }, wait)
    } else if (timer === null) {
      // 纯首部模式：wait 窗口内后续触发直接丢弃，窗口结束后重新放行
      timer = setTimeout(() => {
        timer = null
      }, wait)
    }
  }
  debounced.cancel = () => {
    clearTimeout(timer)
    timer = null
    lastArgs = null
  }
  return debounced
}
