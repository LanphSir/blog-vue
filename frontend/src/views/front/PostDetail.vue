<template>
  <div v-if="post" class="post-detail">
    <div class="detail-main">
      <article class="card article">
        <h1 class="title">{{ post.title }}</h1>
        <div class="meta">
          <span class="author">
            <span class="avatar">{{ avatarText }}</span>
            {{ authorName }}
          </span>
          <span class="dot">·</span>
          <span>{{ formatDate(post.published_at) }}</span>
          <span class="dot">·</span>
          <span>{{ post.view_count }} 阅读</span>
          <span class="dot">·</span>
          <span>约 {{ readingMinutes }} 分钟</span>
          <ColoredTag v-for="tag in post.tags" :key="tag.id" :text="tag.name" :color="tag.color" />
          <span class="spacer" />
          <button class="share-btn" @click="copyLink">复制链接</button>
        </div>

        <div class="md-preview-wrap">
          <MdPreview
            :id="previewId"
            :model-value="post.content"
            :theme="theme"
            preview-theme="github"
            code-theme="atom"
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
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import 'md-editor-v3/lib/preview.css'
import ColoredTag from '@/components/ColoredTag.vue'
import { setupMdEditor } from '@/composables/useMdEditor'
import { getPostBySlug, getPostNeighbors } from '@/api/posts'
import { setRouteTitle } from '@/utils/pageTitle'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))
const MdCatalog = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdCatalog))

const previewId = 'blog-post-preview'

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

.meta .dot {
  opacity: 0.5;
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
}
</style>