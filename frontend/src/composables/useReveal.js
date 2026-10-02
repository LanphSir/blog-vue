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