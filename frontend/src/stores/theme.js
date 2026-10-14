// 明暗主题 store：初始值来自 localStorage（blog_theme），watch 带 immediate
// 让首帧就同步到 <html>.dark 与 localStorage，避免闪烁。
import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem('blog_theme') === 'dark')

  watch(
    isDark,
    (val) => {
      document.documentElement.classList.toggle('dark', val)
      localStorage.setItem('blog_theme', val ? 'dark' : 'light')
    },
    { immediate: true },
  )

  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
})