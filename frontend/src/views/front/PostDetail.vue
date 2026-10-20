<template>
  <div v-if="post" class="post-detail">
    <div class="detail-main">
      <article class="card article">
        <h1 class="title">{{ post.title }}</h1>
        <div class="meta">
          <span class="author">
            <span class="avatar">{{ avatarText }}</span>
            <span class="meta-text">{{ authorName }}</span>
          </span>
          <span class="meta-item" title="发布日期">
            <el-icon><Calendar /></el-icon>
            <span class="meta-text">{{ formatDate(post.published_at) }}</span>
          </span>
          <span class="meta-item" title="阅读量">
            <el-icon><View /></el-icon>
            <span class="meta-text">{{ post.view_count }}</span>
          </span>
          <span class="meta-item" title="预计阅读时长">
            <el-icon><Clock /></el-icon>
            <span class="meta-text">{{ readingMinutes }} 分钟</span>
          </span>
          <span v-if="post.comments_enabled" class="meta-item" title="评论数">
            <el-icon><ChatDotSquare /></el-icon>
            <span class="meta-text">{{ post.comment_count }}</span>
          </span>
          <ColoredTag v-for="tag in post.tags" :key="tag.id" :text="tag.name" :color="tag.color" />
          <span class="spacer" />
          <button class="share-btn" @click="copyLink">复制链接</button>
        </div>

        <div class="md-preview-wrap" :class="'code-' + codeTheme">
          <MdPreview
            :key="previewTheme + codeTheme"
            :id="previewId"
            :model-value="post.content"
            :theme="theme"
            :preview-theme="previewTheme"
            :code-theme="codeTheme"
            :language="'zh-CN'"
          />
        </div>

        <nav v-if="neighbors.previous || neighbors.next" class="neighbors">
          <router-link
            v-if="neighbors.previous"
            :to="{ name: 'post-detail', params: { slug: neighbors.previous.slug } }"
            class="neighbor prev"
          >
            <span class="neighbor-label">上一篇</span>
            {{ neighbors.previous.title }}
          </router-link>
          <span v-else class="neighbor empty" />
          <router-link
            v-if="neighbors.next"
            :to="{ name: 'post-detail', params: { slug: neighbors.next.slug } }"
            class="neighbor next"
          >
            <span class="neighbor-label">下一篇</span>
            {{ neighbors.next.title }}
          </router-link>
        </nav>
      </article>

      <aside class="card toc">
        <h3>目录</h3>
        <MdCatalog
          :editor-id="previewId"
          :theme="theme"
          :scroll-element="scrollElement"
        />
      </aside>
    </div>

    <CommentSection v-if="post.comments_enabled" :key="post.slug" :slug="post.slug" />

      <div class="theme-switch">
        <el-dropdown trigger="hover" :show-timeout="120" :hide-timeout="120" placement="top-end" popper-class="theme-popper" @command="setPreviewTheme">
          <button type="button" class="theme-pill">
            <el-icon class="pill-icon"><Brush /></el-icon>
            <span class="pill-tag">正文主题</span>{{ previewThemeLabel }}
            <el-icon class="pill-caret"><ArrowDown /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="opt in previewThemes"
                :key="opt.key"
                :command="opt.key"
                :class="{ 'theme-active': previewTheme === opt.key }"
              >
                {{ opt.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown trigger="hover" :show-timeout="120" :hide-timeout="120" placement="top-end" popper-class="theme-popper" @command="setCodeTheme">
          <button type="button" class="theme-pill">
            <el-icon class="pill-icon"><Cpu /></el-icon>
            <span class="pill-tag">代码主题</span>{{ codeThemeLabel }}
            <el-icon class="pill-caret"><ArrowDown /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="opt in codeThemes"
                :key="opt.key"
                :command="opt.key"
                :class="{ 'theme-active': codeTheme === opt.key }"
              >
                {{ opt.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
  </div>

  <div v-else-if="!loading" class="card">
    <el-empty description="文章不存在或已删除" />
  </div>
</template>

<script setup>
/* 文章详情页：正文 MdPreview + 右侧目录 MdCatalog。
 * 两个关键点：
 * - 阅读量 5 分钟节流：localStorage blog_viewed:{slug} 记录上次计数的时刻，
 *   5 分钟内再次访问带 ?count_view=false 不重复加阅读；写失败（隐私模式）则不去重照常计数。
 * - 阅读时长估算：中文按 400 字/分钟、英文按 200 词/分钟，取整保底 1 分钟。
 * 组件经 setupMdEditor 懒加载，且先 import 了 preview.css 否则主题样式缺失。
 */
import { computed, defineAsyncComponent, onMounted, ref, watch, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import 'md-editor-v3/lib/preview.css'
import ColoredTag from '@/components/ColoredTag.vue'
import { ArrowDown, Brush, Calendar, ChatDotSquare, Clock, Cpu, View } from '@element-plus/icons-vue'
import CommentSection from '@/components/comment/CommentSection.vue'
import { setupMdEditor } from '@/composables/useMdEditor'
import { getPostBySlug, getPostNeighbors } from '@/api/posts'
import { setRouteTitle } from '@/utils/pageTitle'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))
const MdCatalog = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdCatalog))

const previewId = 'blog-post-preview'

/* 正文风格（阅读偏好，localStorage 记忆）：
 * - 正文主题用 md-editor 内置 previewTheme（样式已随 preview.css 打包，切换即时生效）；
 * - 代码主题：md-editor 预览只输出 .hljs-* 类不注入 token 样式（默认走 CDN，离线不可用），
 *   这里本地静态导入 highlight.js 主题 css 的 URL，用单个 <link> 换 href 实现确定性切换
 *   （多份 hljs css 同时挂在页面上会互相覆盖，顺序不可控）。 */
import hljsAtomCss from 'highlight.js/styles/atom-one-dark.css?url'
import hljsGithubCss from 'highlight.js/styles/github.css?url'
import hljsMonokaiCss from 'highlight.js/styles/monokai.css?url'
import hljsGithubDarkCss from 'highlight.js/styles/github-dark.css?url'

const PREVIEW_THEME_KEYS = ['default', 'github', 'vuepress', 'mk-cute', 'smart-blue', 'cyanosis']
const previewThemes = [
  { key: 'default', label: '默认' },
  { key: 'github', label: 'GitHub' },
  { key: 'vuepress', label: 'VuePress' },
  { key: 'mk-cute', label: '萌系' },
  { key: 'smart-blue', label: '智蓝' },
  { key: 'cyanosis', label: '青蓝' },
]
const CODE_THEME_URLS = {
  atom: hljsAtomCss,
  github: hljsGithubCss,
  monokai: hljsMonokaiCss,
  'github-dark': hljsGithubDarkCss,
}
const codeThemes = [
  { key: 'atom', label: 'Atom' },
  { key: 'github', label: 'GitHub' },
  { key: 'monokai', label: 'Monokai' },
  { key: 'github-dark', label: 'GitHub 暗' },
]

function stored(key, allowed, fallback) {
  const v = localStorage.getItem(key)
  return allowed.includes(v) ? v : fallback
}

const previewTheme = ref(stored('blog_post_preview_theme', PREVIEW_THEME_KEYS, 'github'))
const codeTheme = ref(stored('blog_post_code_theme', Object.keys(CODE_THEME_URLS), 'atom'))

const previewThemeLabel = computed(
  () => previewThemes.find((o) => o.key === previewTheme.value)?.label || '',
)
const codeThemeLabel = computed(
  () => codeThemes.find((o) => o.key === codeTheme.value)?.label || '',
)

function setPreviewTheme(key) {
  previewTheme.value = key
  localStorage.setItem('blog_post_preview_theme', key)
}

function setCodeTheme(key) {
  codeTheme.value = key
  localStorage.setItem('blog_post_code_theme', key)
}

watchEffect(() => {
  let link = document.getElementById('hljs-theme-css')
  if (!link) {
    link = document.createElement('link')
    link.id = 'hljs-theme-css'
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }
  link.href = CODE_THEME_URLS[codeTheme.value]
})

const route = useRoute()
const configStore = useConfigStore()
const themeStore = useThemeStore()
const post = ref(null)
const loading = ref(true)
const neighbors = ref({ previous: null, next: null })

const theme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const scrollElement = computed(() => document.documentElement)

const authorName = computed(() => post.value?.author || configStore.configs.site_author || '站长')
const avatarText = computed(() => authorName.value.slice(0, 1).toUpperCase())

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
}

async function copyLink() {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏链接')
  }
}

const VIEW_THROTTLE_MS = 5 * 60 * 1000

function shouldCountView(slug) {
  const key = `blog_viewed:${slug}`
  try {
    const last = Number(localStorage.getItem(key) || 0)
    if (Date.now() - last < VIEW_THROTTLE_MS) return false
    localStorage.setItem(key, String(Date.now()))
  } catch {
    // 隐私模式等场景不去重，照常计数
  }
  return true
}

const readingMinutes = computed(() => {
  const text = post.value?.content || ''
  const cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length
  const latin = (text.replace(/[\u4e00-\u9fff]/g, '').match(/[A-Za-z0-9]+/g) || []).length
  const minutes = cjk / 400 + latin / 200
  return Math.max(1, Math.round(minutes))
})

async function load() {
  loading.value = true
  try {
    const slug = route.params.slug
    const countView = shouldCountView(slug)
    const [detailRes, neighborsRes] = await Promise.all([
      getPostBySlug(slug, { count_view: countView }),
      getPostNeighbors(slug),
    ])
    post.value = detailRes.data
    setRouteTitle(detailRes.data?.title || '')
    neighbors.value = neighborsRes.data
  } catch {
    post.value = null
    setRouteTitle('')
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.slug, load)
</script>

<style scoped>
.detail-main {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.article {
  flex: 1;
  min-width: 0;
  padding: 32px;
}

.title {
  margin-bottom: 12px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--blog-text-secondary);
  font-size: 13px;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--blog-border);
}

.meta .author {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.meta .avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--blog-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--blog-bg, rgba(127, 127, 127, 0.08));
  border: 1px solid var(--blog-border);
  white-space: nowrap;
}

.meta-item .el-icon {
  font-size: 13px;
  color: var(--blog-primary);
}

/* 主题切换：右下角悬浮控件，竖排堆叠在 back-top（bottom:40px + 42px 高）之上；
 * z-index 低于全局搜索面板(110000)。移动端媒体查询里下移避让。 */
.theme-switch {
  position: fixed;
  right: 28px;
  bottom: 44px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.theme-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  font-size: 12px;
  color: var(--blog-text-secondary);
  background: var(--blog-card, #fff);
  border: 1px solid var(--blog-border);
  border-radius: 999px;
  box-shadow: var(--blog-shadow, 0 2px 8px rgba(0, 0, 0, 0.08));
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.theme-pill:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.theme-pill .pill-icon {
  font-size: 13px;
}

.theme-pill .pill-tag {
  opacity: 0.65;
}

.theme-pill .pill-caret {
  font-size: 10px;
  opacity: 0.55;
  /* 下拉向上弹出（placement=top-end），静态即指向上，悬停翻转作动效 */
  transform: rotate(180deg);
  transition: transform 0.2s;
}

.el-dropdown:hover .pill-caret {
  transform: rotate(0deg);
}

/* 窄屏只留图标+数字，隐藏描述性文字 */
@media (max-width: 1020px) {
  .meta {
    flex-wrap: wrap;
  }
}
@media (max-width: 640px) { 

  .meta .author .meta-text {
    display: none;
  }
}

.meta .spacer {
  flex: 1;
}

.share-btn {
  border: 1px solid var(--blog-border);
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}

.share-btn:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.md-preview-wrap {
  margin-top: 16px;
}

/* GitHub 风格的代码块底色：token 用 github.css（浅底），代码块底色同步调浅 */
.md-preview-wrap.code-github :deep(.md-editor-preview) {
  --md-theme-code-block-color: #24292f;
  --md-theme-code-block-bg-color: #f6f8fa;
}

/* 深底代码主题（atom/monokai/github-dark）：token css 假定深色背景，
   而部分正文主题（GitHub/默认浅色）给代码块配了浅底，这里强制压回深色 */
.md-preview-wrap.code-atom :deep(.md-editor-preview),
.md-preview-wrap.code-monokai :deep(.md-editor-preview),
.md-preview-wrap.code-github-dark :deep(.md-editor-preview) {
  --md-theme-code-block-color: #abb2bf;
  --md-theme-code-block-bg-color: #282c34;
  --md-theme-code-before-bg-color: #282c34;
}

.md-preview-wrap :deep(.md-editor-preview-wrapper) {
  background: transparent;
  padding: 0;
}

.toc {
  position: sticky;
  top: 80px;
  width: 220px;
  flex-shrink: 0;
  padding: 16px;
  font-size: 13px;
}

.toc h3 {
  margin-bottom: 10px;
}

.toc :deep(.md-editor-catalog) {
  max-height: 62vh;
  overflow-y: auto;
}

.neighbors {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--blog-border);
}

.neighbor {
  max-width: 48%;
  color: var(--blog-text-secondary);
  font-size: 14px;
}

.neighbor.next {
  text-align: right;
}

.neighbor.empty {
  flex: 1;
}

.neighbor-label {
  display: block;
  color: var(--blog-primary);
  font-size: 12px;
  margin-bottom: 4px;
}

@media (max-width: 768px) {
  .detail-main {
    flex-direction: column;
  }

  .toc {
    position: static;
    width: 100%;
    order: -1;
  }

  /* 窄屏收进 back-top 同侧边距，减少遮挡正文 */
  .theme-switch {
    right: 16px;
    bottom: 32px;
  }

  .theme-pill .pill-tag {
    display: none;
  }
}
</style>