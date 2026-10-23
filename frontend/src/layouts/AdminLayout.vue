<template>
  <el-container class="admin-layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="admin-aside">
      <div class="brand">
        <span v-if="!collapsed">{{ configStore.siteName() }} 后台</span>
        <span v-else class="brand-dot">{{ (configStore.siteName() || 'B').slice(0, 1) }}</span>
      </div>

      <p v-if="sortMode && !collapsed" class="sort-hint">按住顶层菜单拖动排序（分组内部顺序固定），松开即保存</p>

      <!-- key 挂 activeGroup：跨组导航时重挂载菜单，让 default-openeds 生效、当前组自动展开 -->
      <el-menu
        :key="`${sortMode ? 'sort' : 'nav'}-${activeGroup}`"
        :default-active="route.path"
        :default-openeds="sortMode ? [] : [activeGroup]"
        :router="!sortMode"
        :collapse="collapsed"
        :collapse-transition="false"
        unique-opened
        popper-class="admin-submenu-popper"
        class="side-menu"
        :class="{ 'no-submenu-click': sortMode }"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <template v-for="(item, i) in topItems" :key="item.key">
          <el-sub-menu
            v-if="item.children"
            :index="item.key"
            :draggable="sortMode"
            :class="{ 'is-sorting': sortMode, 'is-dragging': sortMode && dragFrom === i }"
            @dragstart="dragFrom = i"
            @dragenter.prevent="moveTo(i)"
            @dragover.prevent
            @drop.prevent="dragFrom = -1"
          >
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </template>
            <el-menu-item v-for="child in item.children" :key="child.index" :index="child.index">
              <el-icon><component :is="child.icon" /></el-icon>
              <template #title>{{ child.label }}</template>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item
            v-else
            :index="item.index"
            :draggable="sortMode"
            :class="{ 'is-sorting': sortMode, 'is-dragging': sortMode && dragFrom === i }"
            @dragstart="dragFrom = i"
            @dragenter.prevent="moveTo(i)"
            @dragover.prevent
            @drop.prevent="dragFrom = -1"
          >
            <el-icon>
              <component :is="item.icon" />
              <span v-if="item.index === '/admin/comments' && pendingCount > 0" class="nav-dot" />
            </el-icon>
            <template #title>
              {{ item.label }}
              <span v-if="item.index === '/admin/comments' && pendingCount > 0" class="nav-badge">{{ pendingCount }}</span>
            </template>
          </el-menu-item>
        </template>
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
import { computed, onBeforeUnmount, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  ChatDotSquare,
  Collection,
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
  Tools,
} from '@element-plus/icons-vue'
import { adminPendingCommentCount } from '@/api/comments'
import { useAuthStore } from '@/stores/auth'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()
// 实例化即应用已保存的明暗主题（watch immediate）——直达/刷新后台时也生效
const themeStore = useThemeStore()

/* ---------------- 侧栏收缩、分组与顶层拖拽排序 ---------------- */
const COLLAPSE_KEY = 'blog_admin_collapse'
const ORDER_KEY = 'blog_admin_nav_order'
// 0.16.1 起侧栏分层：旧版存的是平铺 index 数组，用该标记保证只迁移一次
const GROUPED_KEY = 'blog_admin_nav_grouped'

// 顶层 6 项；children 为收缩栏目内部（顺序固定、不参与拖拽）
const DEFAULT_NAV = [
  { key: '/admin', index: '/admin', label: '仪表盘', icon: Odometer },
  { key: '/admin/posts', index: '/admin/posts', label: '文章管理', icon: Document },
  { key: '/admin/comments', index: '/admin/comments', label: '评论管理', icon: ChatDotSquare },
  {
    key: 'grp-content',
    label: '内容分组',
    icon: Collection,
    children: [
      { index: '/admin/categories', label: '分类管理', icon: Folder },
      { index: '/admin/tags', label: '标签管理', icon: PriceTag },
    ],
  },
  {
    key: 'grp-site',
    label: '网站设置',
    icon: Tools,
    children: [
      { index: '/admin/friends', label: '友链管理', icon: Link },
      { index: '/admin/banners', label: '轮播图', icon: Film },
      { index: '/admin/menus', label: '导航菜单', icon: Menu },
      { index: '/admin/notices', label: '公告管理', icon: Bell },
      { index: '/admin/config', label: '站点配置', icon: Setting },
    ],
  },
  { key: '/admin/media', index: '/admin/media', label: '媒体库', icon: PictureFilled },
]

const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === '1')
const sortMode = ref(false)
const dragFrom = ref(-1)

function topLevelKeyOf(index) {
  const hit = DEFAULT_NAV.find(
    (item) => item.index === index || item.children?.some((c) => c.index === index),
  )
  return hit ? hit.key : null
}

// 顶层条目顺序：优先读保存的 key 数组；首次（或旧版平铺数组）按「子项→所属组」
// 折算出组间顺序后迁移一次；名单变化容错——删掉的剔除、新增的按默认顺序补末尾
function initialTopOrder() {
  const byKey = new Map(DEFAULT_NAV.map((item) => [item.key, item]))
  let saved = []
  try {
    saved = JSON.parse(localStorage.getItem(ORDER_KEY) || '[]')
  } catch {
    saved = []
  }
  if (localStorage.getItem(GROUPED_KEY) !== '1') {
    if (Array.isArray(saved) && saved.length) {
      // 旧格式存量迁移：顶层存的是 index 路径，子页面折算成所属组（首次出现序）
      const seen = []
      for (const idx of saved) {
        const key = topLevelKeyOf(idx)
        if (key && !seen.includes(key)) seen.push(key)
      }
      saved = seen
    }
    localStorage.setItem(GROUPED_KEY, '1')
    localStorage.setItem(ORDER_KEY, JSON.stringify(Array.isArray(saved) ? saved : []))
  }
  const valid = (Array.isArray(saved) ? saved : []).filter((k) => byKey.has(k))
  const ordered = valid.map((k) => byKey.get(k))
  for (const item of DEFAULT_NAV) {
    if (!ordered.includes(item)) ordered.push(item)
  }
  return ordered
}

const topItems = ref(initialTopOrder())

// 当前路由所在的顶层组（不在任何组则为 ''），用作 el-menu :key 触发重挂载自动展开；
// 详情页等子路由（/admin/posts/:id）exact 不中时按前缀归属顶层项
const activeGroup = computed(() => {
  const exact = topLevelKeyOf(route.path)
  if (exact !== null) return exact
  if (route.path.startsWith('/admin/')) return '/admin/posts'
  return ''
})

function toggleCollapse() {
  collapsed.value = !collapsed.value
  localStorage.setItem(COLLAPSE_KEY, collapsed.value ? '1' : '0')
}

function toggleSort() {
  sortMode.value = !sortMode.value
  if (!sortMode.value) saveOrder()
}

function saveOrder() {
  localStorage.setItem(ORDER_KEY, JSON.stringify(topItems.value.map((item) => item.key)))
}

// 顶层项拖入目标位置即时换位（el-menu 关闭 router 后点击不会跳转，拖动实时预览）
function moveTo(i) {
  if (dragFrom.value < 0 || dragFrom.value === i) return
  const arr = [...topItems.value]
  const [moved] = arr.splice(dragFrom.value, 1)
  arr.splice(i, 0, moved)
  dragFrom.value = i
  topItems.value = arr
  saveOrder()
}

// 待审评论红点：进入后台时拉一次，之后每次路由变化刷新（审完评论回到菜单即见）
const pendingCount = ref(0)

async function refreshPending() {
  try {
    const res = await adminPendingCommentCount()
    pendingCount.value = res.data ?? 0
  } catch {
    /* 未登录等场景静默，角标不是关键路径 */
  }
}

watch(() => route.path, refreshPending)

// 评论管理页处理完（同一路由内操作）通过全局事件触发刷新
window.addEventListener('blog-comments-changed', refreshPending)
onBeforeUnmount(() => window.removeEventListener('blog-comments-changed', refreshPending))

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser().catch(() => {})
  }
  configStore.fetchConfig().then(() => {
    document.documentElement.dataset.bg = 'none'
  })
  refreshPending()
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

/* 待审评论红点：收缩态显示在图标右上角；展开态显示为数字徽标 */
.el-menu-item .el-icon {
  position: relative;
}
.nav-dot {
  position: absolute;
  top: -1px;
  right: -1px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-danger);
}
.nav-badge {
  margin-left: 8px;
  padding: 0 6px;
  border-radius: 8px;
  font-size: 11px;
  line-height: 16px;
  color: #fff;
  background: var(--el-color-danger);
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

.admin-aside :deep(.el-menu-item.is-sorting),
.admin-aside :deep(.el-sub-menu.is-sorting > .el-sub-menu__title) {
  cursor: grab;
}

.admin-aside :deep(.el-menu-item.is-dragging),
.admin-aside :deep(.el-sub-menu.is-dragging) {
  opacity: 0.45;
  border-top: 1px dashed #409eff;
}

/* 排序模式：子栏目标题不可点（防拖动误触展开弹层），拖动落点在其 li 上不受影响 */
.admin-aside :deep(.no-submenu-click .el-sub-menu__title) {
  pointer-events: none;
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
