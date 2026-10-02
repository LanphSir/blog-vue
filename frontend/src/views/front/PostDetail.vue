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
          <ColoredTag v-for="tag in post.tags" :key="tag.id" :text="tag.name" :color="tag.color" />
          <span class="spacer" />
          <button class="share-btn" @click="copyLink">复制链接</button>
        </div>
        <div class="markdown-body" v-html="html" ref="articleRef" />

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

      <aside v-if="toc.length" class="card toc">
        <h3>目录</h3>
        <ul>
          <li v-for="item in toc" :key="item.id" :class="['lvl-' + item.depth, { active: item.id === activeHeading }]">
            <a :href="'#' + item.id" @click.prevent="scrollTo(item.id)">{{ item.text }}</a>
          </li>
        </ul>
      </aside>
    </div>
  </div>

  <div v-else-if="!loading" class="card">
    <el-empty description="文章不存在或已删除" />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import 'highlight.js/styles/github-dark.min.css'
import ColoredTag from '@/components/ColoredTag.vue'
import { extractHeadingsAsync, useMarkdown } from '@/composables/useMarkdown'
import { getPostBySlug, getPostNeighbors } from '@/api/posts'
import { useConfigStore } from '@/stores/config'

const route = useRoute()
const configStore = useConfigStore()
const post = ref(null)
const loading = ref(true)
const neighbors = ref({ previous: null, next: null })
const articleRef = ref(null)
const activeHeading = ref(null)
const toc = ref([])

const content = computed(() => post.value?.content || '')
const { html } = useMarkdown(content)

const authorName = computed(() => post.value?.author || configStore.configs.site_author || '站长')
const avatarText = computed(() => authorName.value.slice(0, 1).toUpperCase())

async function copyLink() {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏链接')
  }
}

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function onScroll() {
  if (!articleRef.value) return
  const headings = articleRef.value.querySelectorAll('h1, h2, h3')
  let current = activeHeading.value
  for (const h of headings) {
    if (h.getBoundingClientRect().top <= 80) current = h.id
  }
  activeHeading.value = current
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
}

async function load() {
  loading.value = true
  activeHeading.value = null
  try {
    const slug = route.params.slug
    const [detailRes, neighborsRes] = await Promise.all([
      getPostBySlug(slug),
      getPostNeighbors(slug),
    ])
    post.value = detailRes.data
    neighbors.value = neighborsRes.data
    toc.value = await extractHeadingsAsync(post.value.content)
    await nextTick()
    const headings = articleRef.value?.querySelectorAll('h1, h2, h3')
    headings?.forEach((h, i) => {
      h.id = h.id || toc.value[i]?.id
    })
    addCodeCopyButtons()
  } catch {
    post.value = null
  } finally {
    loading.value = false
  }
}

function addCodeCopyButtons() {
  const blocks = articleRef.value?.querySelectorAll('pre')
  blocks?.forEach((pre) => {
    if (pre.querySelector('.code-copy')) return
    const lang = pre.querySelector('code')?.className.match(/language-(\w+)/)?.[1]
    pre.dataset.lang = lang || 'code'
    const btn = document.createElement('button')
    btn.className = 'code-copy'
    btn.textContent = '复制'
    btn.addEventListener('click', () => {
      navigator.clipboard
        ?.writeText(pre.textContent || '')
        .then(() => {
          btn.textContent = '已复制'
          setTimeout(() => (btn.textContent = '复制'), 1500)
        })
        .catch(() => {})
    })
    pre.appendChild(btn)
  })
}

onMounted(() => {
  load()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
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

.toc ul {
  list-style: none;
}

.toc li {
  margin-bottom: 6px;
}

.toc li.lvl-2 {
  padding-left: 12px;
}

.toc li.lvl-3 {
  padding-left: 24px;
}

.toc a {
  color: var(--blog-text-secondary);
}

.toc li.active a {
  color: var(--blog-primary);
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