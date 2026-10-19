<template>
  <el-container class="admin-layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="admin-aside">
      <div class="brand">
        <span v-if="!collapsed">{{ configStore.siteName() }} 后台</span>
        <span v-else class="brand-dot">{{ (configStore.siteName() || 'B').slice(0, 1) }}</span>
      </div>

      <p v-if="sortMode && !collapsed" class="sort-hint">按住菜单项拖动排序，松开即保存</p>

      <el-menu
        :key="sortMode ? 'menu-sort' : 'menu-nav'"
        :default-active="route.path"
        :router="!sortMode"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item
          v-for="(item, i) in navItems"
          :key="item.index"
          :index="item.index"
          :draggable="sortMode"
          :class="{ 'is-sorting': sortMode, 'is-dragging': sortMode && dragFrom === i }"
          @dragstart="dragFrom = i"
          @dragenter.prevent="moveTo(i)"
          @dragover.prevent
          @drop.prevent="dragFrom = -1"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>

      <div class="aside-foot">
        <button type="button" class="foot-btn" :class="{ on: sortMode }" @click="toggleSort">
          <el-icon><Rank /></el-icon>
          <span v-if="!collapsed">{{ sortMode ? '完成排序' : '菜单排序' }}</span>
        </button>
        <button type="button" class="foot-btn" @click="toggleCollapse">
          <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
          <span v-if="!collapsed">收起菜单</span>
        </button>
      </div>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <span class="title">{{ route.meta.title || '管理后台' }}</span>
        <div class="user-info">
          <el-tooltip content="新标签页打开前台首页" placement="bottom">
            <el-button link type="info" @click="openFront">
              <el-icon><HomeFilled /></el-icon>
              <span>前台首页</span>
            </el-button>
          </el-tooltip>
          <el-switch
            :model-value="themeStore.isDark"
            @change="themeStore.toggle()"
            inline-prompt
            active-text="暗"
            inactive-text="亮"
          />
          <span>{{ authStore.user?.username }}</span>
          <el-button link type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/* 后台主布局：左侧菜单 + 顶栏 + 内容区。
 * 侧栏两件套（0.15.0）：
 * - 收缩：el-menu collapse 只留图标，状态记 localStorage(blog_admin_collapse)；
 *   菜单项都带 #icon 插槽，收缩态靠图标识别。
 * - 排序：「菜单排序」模式开启后禁用 router 跳转、菜单项 draggable，
 *   拖拽换位即时写 localStorage(blog_admin_nav_order，存 index 路径数组)；
 *   新增页面按默认顺序追加在末尾，清缓存即回默认。
 * 坑：后台页不需要前台那些花哨背景，进入时强制 data-bg="none"，
 * 离开（onUnmounted）时恢复 applyBackground()——否则会残留「后台无背景」的状态到前台。
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  Document,
  Expand,
  Film,
  Folder,
  Fold,
  HomeFilled,
  Link,
  Menu,
  Odometer,
  PictureFilled,
  PriceTag,
  Rank,
  Setting,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()
// 实例化即应用已保存的明暗主题（watch immediate）——直达/刷新后台时也生效
const themeStore = useThemeStore()

/* ---------------- 侧栏收缩与拖拽排序 ---------------- */
const COLLAPSE_KEY = 'blog_admin_collapse'
const ORDER_KEY = 'blog_admin_nav_order'

const DEFAULT_NAV = [
  { index: '/admin', label: '仪表盘', icon: Odometer },
  { index: '/admin/posts', label: '文章管理', icon: Document },
  { index: '/admin/categories', label: '分类管理', icon: Folder },
  { index: '/admin/tags', label: '标签管理', icon: PriceTag },
  { index: '/admin/friends', label: '友链管理', icon: Link },
  { index: '/admin/banners', label: '轮播图', icon: Film },
  { index: '/admin/media', label: '媒体库', icon: PictureFilled },
  { index: '/admin/menus', label: '导航菜单', icon: Menu },
  { index: '/admin/notices', label: '公告管理', icon: Bell },
  { index: '/admin/config', label: '站点配置', icon: Setting },
]

const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === '1')
const sortMode = ref(false)
const dragFrom = ref(-1)

// 按保存的 index 顺序重排；名单变化时容错：删掉的剔除、新增的按默认顺序补到末尾
function initialOrder() {
  let saved = []
  try {
    saved = JSON.parse(localStorage.getItem(ORDER_KEY) || '[]')
  } catch {
    saved = []
  }
  if (!Array.isArray(saved) || !saved.length) return [...DEFAULT_NAV]
  const byIndex = new Map(DEFAULT_NAV.map((item) => [item.index, item]))
  const ordered = saved.map((idx) => byIndex.get(idx)).filter(Boolean)
  for (const item of DEFAULT_NAV) {
    if (!ordered.includes(item)) ordered.push(item)
  }
  return ordered
}

const navItems = ref(initialOrder())

function toggleCollapse() {
  collapsed.value = !collapsed.value
  localStorage.setItem(COLLAPSE_KEY, collapsed.value ? '1' : '0')
}

function toggleSort() {
  sortMode.value = !sortMode.value
  if (!sortMode.value) saveOrder()
}

function saveOrder() {
  localStorage.setItem(ORDER_KEY, JSON.stringify(navItems.value.map((item) => item.index)))
}

// 拖入目标位置即时换位（el-menu 关闭 router 后点击不会跳转，拖动过程中实时预览顺序）
function moveTo(i) {
  if (dragFrom.value < 0 || dragFrom.value === i) return
  const arr = [...navItems.value]
  const [moved] = arr.splice(dragFrom.value, 1)
  arr.splice(i, 0, moved)
  dragFrom.value = i
  navItems.value = arr
  saveOrder()
}

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser().catch(() => {})
  }
  configStore.fetchConfig().then(() => {
    document.documentElement.dataset.bg = 'none'
  })
})

onUnmounted(() => {
  configStore.applyBackground()
})

function openFront() {
  window.open('/', '_blank')
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.admin-aside {
  background: #1d1e1f;
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
}

.brand {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid #333;
  white-space: nowrap;
  overflow: hidden;
}

.brand-dot {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--blog-primary, #409eff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
}

.sort-hint {
  margin: 8px 12px 0;
  padding: 6px 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.12);
  border: 1px dashed rgba(230, 162, 60, 0.5);
  border-radius: 6px;
}

/* 菜单占满剩余高度，底部按钮贴底 */
.admin-aside :deep(.el-menu) {
  flex: 1;
  overflow-y: auto;
  border-right: none;
}

.admin-aside :deep(.el-menu-item.is-sorting) {
  cursor: grab;
}

.admin-aside :deep(.el-menu-item.is-dragging) {
  opacity: 0.45;
  border-top: 1px dashed #409eff;
}

.aside-foot {
  border-top: 1px solid #333;
  padding: 6px 0;
  flex-shrink: 0;
}

.foot-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: none;
  border: none;
  color: #bfcbd9;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}

.foot-btn:hover {
  color: #fff;
  background: #2b2c2e;
}

.foot-btn.on {
  color: #e6a23c;
}

.admin-header {
  background: var(--blog-card);
  border-bottom: 1px solid var(--blog-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-main {
  background: var(--blog-bg);
}
</style>
