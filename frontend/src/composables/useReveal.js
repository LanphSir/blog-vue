// 滚动入场动画：给 .reveal 元素做「进入视口才显现」的过渡。
// 关键坑：很多文章块是异步（v-for / 懒加载图片）才挂到 DOM 上的，
// 所以除了挂载时观察一次，还挂了一个 MutationObserver 持续监听 body 的
// 子节点新增——否则后渲染的 .reveal 永远不会被观察，永远停在 opacity:0。
import { onBeforeUnmount, onMounted } from 'vue'

const supported = typeof IntersectionObserver !== 'undefined'

export function useReveal() {
  let observer = null
  let mutationObserver = null

  function observeAll() {
    document.querySelectorAll('.reveal:not(.revealed)').forEach((el) => observer?.observe(el))
  }

  onMounted(() => {
    if (!supported) {
      document.querySelectorAll('.reveal').forEach((el) => el.classList.add('revealed'))
      return
    }
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed')
            observer.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.08 },
    )
    mutationObserver = new MutationObserver(observeAll)
    mutationObserver.observe(document.body, { childList: true, subtree: true })
    observeAll()
  })

  onBeforeUnmount(() => {
    mutationObserver?.disconnect()
    observer?.disconnect()
  })

  return { observe: observeAll }
}