<template>
  <div class="site">
    <NoticeBar />

    <header class="site-header">
      <div class="container header-inner">
        <router-link to="/" class="logo">{{ configStore.siteName() }}</router-link>

        <nav ref="navRef" class="nav">
          <template v-for="menu in visibleItems" :key="menu._key">
            <el-dropdown v-if="menu.type === 'category' && categoryTree.length" trigger="hover">
              <span class="nav-link" :class="{ active: isCategoryActive() }">
                <el-icon v-if="resolveIcon(menu.icon)" class="nav-icon"><component :is="resolveIcon(menu.icon)" /></el-icon>
                {{ menu.label }}
                <el-icon class="caret"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goCategory(null)">
                    <span class="cat-root-label">全部栏目</span>
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-for="root in categoryTree"
                    :key="root.id"
                    @click="goCategory(root.id)"
                  >
                    <span class="cat-root-label" :style="root.color ? { color: root.color } : {}">
                      {{ root.name }}
                    </span>
                    <template v-if="root.children.length">
                      <div class="cat-children">
                        <button
                          v-for="child in root.children"
                          :key="child.id"
                          class="cat-child"
                          @click.stop="goCategory(child.id)"
                        >
                          {{ child.name }}
                        </button>
                      </div>
                    </template>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-dropdown v-else-if="menu.children && menu.children.length" trigger="hover">
              <span class="nav-link" :class="{ active: isChildActive(menu.children) }">
                <el-icon v-if="resolveIcon(menu.icon)" class="nav-icon"><component :is="resolveIcon(menu.icon)" /></el-icon>
                {{ menu.label }}
                <el-icon class="caret"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="(child, ci) in menu.children"
                    :key="ci + '-' + child.label"
                    @click="goChild(child)"
                  >
                    <el-icon v-if="resolveIcon(child.icon)" class="nav-icon"><component :is="resolveIcon(child.icon)" /></el-icon>
                    {{ child.label }}
                    <el-icon v-if="child.is_external" class="ext-icon"><TopRight /></el-icon>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <a
              v-else-if="menu.is_external"
              :href="menu.path"
              target="_blank"
              rel="noopener"
              class="nav-link"
            >
              <el-icon v-if="resolveIcon(menu.icon)" class="nav-icon"><component :is="resolveIcon(menu.icon)" /></el-icon>
              {{ menu.label }}
              <el-icon class="ext-icon"><TopRight /></el-icon>
            </a>

            <router-link v-else :to="menu.path" class="nav-link" :class="{ active: isLinkActive(menu) }">
              <el-icon v-if="resolveIcon(menu.icon)" class="nav-icon"><component :is="resolveIcon(menu.icon)" /></el-icon>
              {{ menu.label }}
            </router-link>
          </template>

          <el-dropdown v-if="hasHidden" trigger="click" @command="onMoreNav">
            <span class="nav-link nav-more" :class="{ active: moreActive }" aria-label="更多导航">
              <el-icon class="nav-more-icon"><MoreFilled /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="menu in hiddenItems" :key="menu._key" :command="menu">
                  <el-icon v-if="resolveIcon(menu.icon)" class="nav-icon"><component :is="resolveIcon(menu.icon)" /></el-icon>
                  {{ menu.label }}
                  <el-icon v-if="menu.is_external" class="ext-icon"><TopRight /></el-icon>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </nav>

        <div class="actions">
          <button class="search-btn" aria-label="搜索" @click="searchRef?.open()">
            <el-icon><Search /></el-icon>
          </button>
          <el-switch
            :model-value="themeStore.isDark"
            @change="themeStore.toggle()"
            inline-prompt
            active-text="暗"
            inactive-text="亮"
          />
          <router-link to="/admin/login" class="admin-link">后台</router-link>
        </div>
      </div>
    </header>

    <main class="container site-main">
      <router-view />
    </main>

    <footer class="site-footer">
      <div v-if="friends.length" class="footer-friends">
        <div class="container">
          <span class="friends-label">友情链接</span>
          <a
            v-for="link in friends"
            :key="link.id"
            :href="link.url"
            target="_blank"
            rel="noopener"
            class="friend-link"
          >
            <img v-if="link.icon" :src="link.icon" class="friend-icon" alt="" />{{ link.name }}
          </a>
        </div>
      </div>
      <div class="container">
        <span>{{ configStore.configs.footer_text }}</span>
        <span v-if="configStore.configs.icp" class="icp">{{ configStore.configs.icp }}</span>
      </div>
    </footer>

    <transition name="fade">
      <button v-if="showTop" class="back-top" aria-label="回到顶部" @click="scrollTop">
        <el-icon><Top /></el-icon>
      </button>
    </transition>

    <GlobalSearch ref="searchRef" />
    <NoticeDialog />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, MoreFilled, Search, Top, TopRight } from '@element-plus/icons-vue'
import { resolveIcon } from '@/utils/navIcons'
import { useNavOverflow } from '@/composables/useNavOverflow'
import NoticeBar from '@/components/NoticeBar.vue'
import NoticeDialog from '@/components/NoticeDialog.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import { getFriends } from '@/api/site'
import { getCategoryTree } from '@/api/categories'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()
const themeStore = useThemeStore()
const showTop = ref(false)
const friends = ref([])
const categoryTree = ref([])
const searchRef = ref(null)
const navRef = ref(null)

const navItems = computed(() =>
  configStore.siteMenus().map((menu, i) => ({ ...menu, _key: `${i}:${menu.label}:${menu.path || menu.type}` }))
)
const { visibleItems, hiddenItems, hasHidden } = useNavOverflow(navRef, navItems)

const moreActive = computed(() =>
  hiddenItems.value.some((menu) => {
    if (menu.type === 'category') return isCategoryActive()
    if (menu.children && menu.children.length) return isChildActive(menu.children)
    return !menu.is_external && isLinkActive(menu)
  })
)

function onMoreNav(menu) {
  if (menu.type === 'category') {
    router.push({ name: 'home' })
    return
  }
  if (menu.is_external && menu.path) {
    window.open(menu.path, '_blank', 'noopener')
    return
  }
  const target = menu.path || menu.children?.[0]?.path
  if (target) router.push(target)
}

function onScroll() {
  showTop.value = window.scrollY > 400
}

function scrollTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function isChildActive(children) {
  return children.some((child) => route.path === child.path)
}

function isCategoryActive() {
  return route.name === 'home' && Boolean(route.query.category_id)
}

function isLinkActive(menu) {
  if (menu.path === '/') return route.path === '/'
  return route.path.startsWith(menu.path)
}

function goChild(child) {
  if (child.is_external) {
    window.open(child.path, '_blank', 'noopener')
    return
  }
  router.push(child.path)
}

function goCategory(id) {
  if (id === null) {
    router.push({ name: 'home' })
    return
  }
  router.push({ name: 'home', query: { category_id: id } })
}

async function loadCategoryMenu() {
  if (!configStore.hasCategoryMenu()) return
  try {
    const res = await getCategoryTree()
    categoryTree.value = res.data
  } catch {
    categoryTree.value = []
  }
}

onMounted(() => {
  configStore.fetchConfig().then(loadCategoryMenu)
  getFriends()
    .then((res) => (friends.value = res.data))
    .catch(() => {})
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.site {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--blog-card);
  border-bottom: 1px solid var(--blog-border);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.logo {
  font-family: var(--blog-font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--blog-primary);
}

.nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
  margin: 0 20px;
  overflow: hidden;
}

.nav-more-icon {
  font-size: 16px;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 6px;
  color: var(--blog-text-secondary);
  font-size: 14px;
  transition: color 0.2s, background 0.2s;
  cursor: pointer;
}

.nav-link:hover,
.nav-link.active {
  color: var(--blog-primary);
  background: color-mix(in srgb, var(--blog-primary) 8%, transparent);
}

.caret {
  font-size: 12px;
}

.nav-icon {
  margin-right: 4px;
  font-size: 14px;
}

.ext-icon {
  margin-left: 2px;
  font-size: 11px;
  opacity: 0.7;
}

.cat-root-label {
  display: block;
  font-weight: 500;
}

.cat-children {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  padding-left: 8px;
}

.cat-child {
  border: 1px solid var(--blog-border);
  background: transparent;
  border-radius: 4px;
  font-size: 12px;
  padding: 2px 8px;
  color: var(--blog-text-secondary);
  cursor: pointer;
}

.cat-child:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--blog-border);
  border-radius: 50%;
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.admin-link {
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.admin-link:hover {
  color: var(--blog-primary);
}

.site-main {
  flex: 1;
  width: 100%;
  padding-top: 20px;
  padding-bottom: 20px;
}

.site-footer {
  border-top: 1px solid var(--blog-border);
  padding: 20px 0;
  text-align: center;
  color: var(--blog-text-secondary);
  font-size: 13px;
}

.icp {
  margin-left: 12px;
}

.footer-friends {
  border-bottom: 1px solid var(--blog-border);
  padding: 14px 0;
  margin-bottom: 14px;
}

.footer-friends .container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px 18px;
}

.friends-label {
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.friend-link {
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  color: var(--blog-text-secondary);
  transition: color 0.2s;
}

.friend-icon {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  object-fit: cover;
  margin-right: 5px;
}

.friend-link:hover {
  color: var(--blog-primary);
}

.back-top {
  position: fixed;
  right: 28px;
  bottom: 40px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid var(--blog-border);
  background: var(--blog-card);
  color: var(--blog-primary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--blog-shadow);
}

.back-top:hover {
  color: #fff;
  background: var(--blog-primary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .nav-link {
    padding: 6px 8px;
  }
}
</style>