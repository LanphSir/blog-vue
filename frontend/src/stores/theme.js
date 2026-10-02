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