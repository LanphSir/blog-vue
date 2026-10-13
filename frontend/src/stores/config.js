import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getMenus, getNotices, getSiteConfig, getSocialLinks } from '@/api/site'
import { isNoticeDismissed } from '@/utils/notice'
import { setSiteName } from '@/utils/pageTitle'

export const useConfigStore = defineStore('config', () => {
  const configs = ref({})
  const menus = ref([])
  const socialLinks = ref([])
  const notices = ref([])

  const siteName = () => configs.value.site_name || '个人博客'

  const accentColor = () => configs.value.site_accent_color || '#2563eb'

  const siteMenus = () => (menus.value.length ? menus.value : defaultMenus())

  const hasCategoryMenu = () => siteMenus().some((m) => m.type === 'category')

  const profileLinks = () => socialLinks.value

  const bannerText = () => configs.value.site_slogan || ''

  const bannerNotice = () => notices.value.find((n) => n.type === 'banner') || null

  const dialogNotice = () => {
    const dialogs = notices.value
      .filter((n) => n.type === 'dialog')
      .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)))
    return dialogs.find((n) => !isNoticeDismissed(n.id, n.version)) || null
  }

  async function fetchConfig() {
    const menusReq = getMenus()
      .then((res) => {
        menus.value = Array.isArray(res.data) ? res.data : []
      })
      .catch(() => {
        menus.value = []
      })
    const linksReq = getSocialLinks()
      .then((res) => {
        socialLinks.value = Array.isArray(res.data) ? res.data : []
      })
      .catch(() => {
        socialLinks.value = []
      })
    const noticesReq = getNotices()
      .then((res) => {
        notices.value = Array.isArray(res.data) ? res.data : []
      })
      .catch(() => {
        notices.value = []
      })
    const res = await getSiteConfig()
    const map = {}
    for (const item of res.data) {
      map[item.key] = item.value
    }
    configs.value = map
    applyAccentColor()
    applyBackground()
    setSiteName(map.site_name)
    await Promise.all([menusReq, linksReq, noticesReq])
  }

  function applyAccentColor() {
    const color = accentColor()
    document.documentElement.style.setProperty('--blog-primary', color)
  }

  const BACKGROUND_KEYS = ['none', 'grid', 'aurora', 'dots', 'topo', 'geek', 'line']

  function applyBackground() {
    const key = configs.value.site_background
    document.documentElement.dataset.bg = BACKGROUND_KEYS.includes(key) ? key : 'none'
  }

  return {
    configs,
    menus,
    socialLinks,
    notices,
    siteName,
    accentColor,
    siteMenus,
    hasCategoryMenu,
    profileLinks,
    bannerText,
    bannerNotice,
    dialogNotice,
    fetchConfig,
    applyAccentColor,
    applyBackground,
  }
})

function defaultMenus() {
  return [
    { label: '首页', path: '/', icon: 'HomeFilled', type: 'link', is_external: false, children: [] },
    { label: '文章', path: '/posts', icon: 'Document', type: 'link', is_external: false, children: [] },
    { label: '标签', path: '/tags', icon: 'PriceTag', type: 'link', is_external: false, children: [] },
    { label: '友链', path: '/friends', icon: 'Link', type: 'link', is_external: false, children: [] },
    { label: '关于', path: '/about', icon: 'InfoFilled', type: 'link', is_external: false, children: [] },
  ]
}