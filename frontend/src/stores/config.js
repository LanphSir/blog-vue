import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getSiteConfig } from '@/api/site'

export const useConfigStore = defineStore('config', () => {
  const configs = ref({})

  const siteName = () => configs.value.site_name || '个人博客'

  const accentColor = () => configs.value.site_accent_color || '#2563eb'

  const siteMenus = () => {
    const raw = configs.value.site_menus
    if (!raw) return defaultMenus()
    try {
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) && parsed.length ? parsed : defaultMenus()
    } catch {
      return defaultMenus()
    }
  }

  const hasCategoryMenu = () => siteMenus().some((m) => m.type === 'category')

  const profileLinks = () => {
    const raw = configs.value.profile_links
    if (!raw) return []
    try {
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }

  const bannerText = () => configs.value.site_slogan || ''

  async function fetchConfig() {
    const res = await getSiteConfig()
    const map = {}
    for (const item of res.data) {
      map[item.key] = item.value
    }
    configs.value = map
    applyAccentColor()
  }

  function applyAccentColor() {
    const color = accentColor()
    document.documentElement.style.setProperty('--blog-primary', color)
  }

  return {
    configs,
    siteName,
    accentColor,
    siteMenus,
    hasCategoryMenu,
    profileLinks,
    bannerText,
    fetchConfig,
    applyAccentColor,
  }
})

function defaultMenus() {
  return [
    { label: '首页', path: '/' },
    { label: '文章', path: '/posts' },
    { label: '标签', path: '/tags' },
    { label: '友链', path: '/friends' },
    { label: '关于', path: '/about' },
  ]
}