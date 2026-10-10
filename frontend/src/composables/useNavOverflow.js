import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const CACHE_KEY = 'bl…idths'
const BUFFER = 8
const MORE_FALLBACK = 64
const MORE_KEY = '***'

function loadCache() {
  try {
    const raw = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}')
    return raw && typeof raw === 'object' ? raw : {}
  } catch {
    return {}
  }
}

/**
 * Collapses nav items that exceed the nav width into an overflow list.
 * Item widths come from the rendered DOM (cloned off-screen), cached in
 * localStorage keyed by item.key so revisits settle in one frame.
 * The first item is never hidden.
 */
export function useNavOverflow(navRef, items) {
  const widths = ref(loadCache())
  const navW = ref(0)
  let ro = null
  let fontsRedone = false

  const renderAll = computed(() => items.value.some((item) => widths.value[item.key] == null))

  const visibleCount = computed(() => {
    if (renderAll.value || items.value.length < 2) return items.value.length
    const width = navW.value
    if (!width) return items.value.length
    const gap = gapPx()
    const list = items.value
    const more = widths.value[MORE_KEY] || MORE_FALLBACK
    const avail = width - more - gap - BUFFER
    let total = 0
    for (let i = 0; i < list.length; i++) total += widths.value[list[i].key] + (i > 0 ? gap : 0)
    if (total <= width - BUFFER) return list.length
    let count = 1
    let run = 0
    for (let i = 0; i < list.length; i++) {
      run += widths.value[list[i].key] + (i > 0 ? gap : 0)
      if (run > avail) break
      count = i + 1
    }
    return Math.min(count, list.length - 1)
  })

  const visibleItems = computed(() => {
    const all = renderAll.value || items.value.length < 2
    return all ? items.value : items.value.slice(0, visibleCount.value)
  })

  const hiddenItems = computed(() => {
    const all = renderAll.value || items.value.length < 2
    return all ? [] : items.value.slice(visibleCount.value)
  })

  const hasHidden = computed(() => hiddenItems.value.length > 0)

  function gapPx() {
    const nav = navRef.value
    if (!nav) return 4
    return parseFloat(getComputedStyle(nav).columnGap) || 4
  }

  function measure() {
    const nav = navRef.value
    if (!nav || !document.body) return
    navW.value = nav.getBoundingClientRect().width
    const rendered = renderAll.value ? items.value : [...visibleItems.value, ...(hasHidden.value ? [{ key: MORE_KEY }] : [])]
    const children = Array.from(nav.children).slice(0, rendered.length)
    if (!children.length) return
    const clone = nav.cloneNode(true)
    clone.style.cssText = 'position:fixed;left:-99999px;top:0;width:auto;display:flex;flex:none;overflow:visible;visibility:hidden;'
    document.body.appendChild(clone)
    const next = { ...widths.value }
    children.forEach((_, idx) => {
      const el = clone.children[idx]
      const item = rendered[idx]
      if (!el || !item) return
      const w = Math.round(el.getBoundingClientRect().width)
      if (w > 0) next[item.key] = w
    })
    clone.remove()
    widths.value = next
    const keep = new Set([...items.value.map((item) => item.key), MORE_KEY])
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(Object.fromEntries(Object.entries(next).filter(([k]) => keep.has(k)))))
    } catch {
      /* storage unavailable */
    }
  }

  function remeasure() {
    nextTick(measure)
  }

  watch(() => items.value.map((item) => item.key).join('|'), remeasure)
  watch(hasHidden, remeasure)

  onMounted(() => {
    measure()
    if (navRef.value && typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver((entries) => {
        navW.value = entries[0].contentRect.width
      })
      ro.observe(navRef.value)
    }
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => {
        if (fontsRedone) return
        fontsRedone = true
        widths.value = {}
        remeasure()
      })
    }
  })

  onBeforeUnmount(() => {
    if (ro) ro.disconnect()
  })

  return { visibleItems, hiddenItems, hasHidden }
}
