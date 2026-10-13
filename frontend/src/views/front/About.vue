<template>
  <div class="about">
    <section class="card hero reveal">
      <div class="hero-id">
        <img v-if="avatar" :src="avatar" class="hero-avatar" :alt="author" />
        <span v-else class="hero-avatar hero-avatar-fallback">{{ initial }}</span>
        <div class="hero-text">
          <h1 class="hero-name">{{ author }}</h1>
          <p class="hero-slogan">{{ slogan }}</p>
        </div>
      </div>
      <div v-if="socialLinks.length" class="hero-links">
        <a
          v-for="link in socialLinks"
          :key="link.platform + link.url"
          :href="link.url"
          target="_blank"
          rel="noopener"
          class="link-badge"
          :style="badgeStyle(link)"
          :title="badgeTitle(link)"
        >
          {{ badgeLetter(link) }}
        </a>
      </div>
    </section>

    <section class="card intro reveal">
      <h2 class="sec-title">我与这个小站</h2>
      <MdPreview
        v-if="aboutMd"
        :id="previewId"
        :model-value="aboutMd"
        :theme="mdTheme"
        preview-theme="github"
        language="zh-CN"
      />
      <p v-else class="intro-fallback">{{ fallbackIntro }}</p>
    </section>

    <section v-if="categoryShares.length" class="card focus reveal">
      <h2 class="sec-title">我写什么</h2>
      <div class="share-bar" role="img" aria-label="各分类文章数量占比">
        <span
          v-for="c in categoryShares"
          :key="c.id"
          class="share-seg"
          :style="{ width: c.pct + '%', background: c.color || 'var(--blog-primary)' }"
          :title="`${c.name} · ${c.post_count} 篇`"
        />
      </div>
      <ul class="legend">
        <li v-for="c in categoryShares" :key="c.id">
          <button class="legend-item" @click="goCategory(c.id)">
            <span class="legend-dot" :style="{ background: c.color || 'var(--blog-primary)' }" />
            <span class="legend-name">{{ c.name }}</span>
            <span class="legend-count">{{ c.post_count }} 篇</span>
          </button>
        </li>
      </ul>
      <div v-if="hotTags.length" class="tag-row">
        <button v-for="t in hotTags" :key="t.id" class="tag-btn" @click="goTag(t.id)">
          <ColoredTag :text="t.name" :color="t.color" />
        </button>
      </div>
    </section>

    <div class="two-col">
      <section v-if="stats" class="card ledger reveal">
        <h2 class="sec-title">小账本</h2>
        <p class="ledger-lead">这个站已经跑了 <strong>{{ stats.days_since_launch }}</strong> 天。</p>
        <dl class="ledger-grid">
          <div class="ledger-cell">
            <dt>文章</dt>
            <dd>{{ stats.post_count }}</dd>
          </div>
          <div class="ledger-cell">
            <dt>分类</dt>
            <dd>{{ stats.category_count }}</dd>
          </div>
          <div class="ledger-cell">
            <dt>标签</dt>
            <dd>{{ stats.tag_count }}</dd>
          </div>
          <div class="ledger-cell">
            <dt>阅读</dt>
            <dd>{{ stats.total_views }}</dd>
          </div>
        </dl>
      </section>

      <section v-if="recent.length" class="card recent reveal">
        <h2 class="sec-title">最近在写</h2>
        <router-link
          v-for="post in recent"
          :key="post.id"
          class="recent-item"
          :to="{ name: 'post-detail', params: { slug: post.slug } }"
        >
          <span class="recent-title">{{ post.title }}</span>
          <time class="recent-date">{{ formatDate(post.published_at) }}</time>
        </router-link>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import 'md-editor-v3/lib/preview.css'
import ColoredTag from '@/components/ColoredTag.vue'
import { setupMdEditor } from '@/composables/useMdEditor'
import { useReveal } from '@/composables/useReveal'
import { getSiteStats } from '@/api/site'
import { getCategories, getTags } from '@/api/categories'
import { getPosts } from '@/api/posts'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'
import { platformMeta } from '@/utils/platforms'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))

const router = useRouter()
const configStore = useConfigStore()
const themeStore = useThemeStore()
useReveal()

const previewId = 'about-md-preview'
const stats = ref(null)
const categories = ref([])
const tags = ref([])
const recent = ref([])

const avatar = computed(() => configStore.configs.site_avatar || '')
const author = computed(() => configStore.configs.site_author || configStore.siteName())
const initial = computed(() => author.value.slice(0, 1).toUpperCase())
const slogan = computed(() => configStore.configs.site_slogan || configStore.configs.site_description || '')
const aboutMd = computed(() => (configStore.configs.site_about_markdown || '').trim())
const fallbackIntro = computed(() => configStore.configs.site_description || '记录技术、生活与思考。')
const mdTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const socialLinks = computed(() => configStore.profileLinks())

const categoryShares = computed(() => {
  const tops = categories.value.filter((c) => !c.parent_id && c.post_count > 0)
  const total = tops.reduce((sum, c) => sum + c.post_count, 0)
  if (!total) return []
  return tops
    .slice()
    .sort((a, b) => b.post_count - a.post_count)
    .map((c) => ({ ...c, pct: Math.max(2, (c.post_count / total) * 100) }))
})

const hotTags = computed(() =>
  tags.value
    .filter((t) => t.visible !== false && t.post_count > 0)
    .sort((a, b) => b.post_count - a.post_count)
    .slice(0, 8),
)

function badgeStyle(link) {
  const meta = platformMeta(link.platform)
  if (!meta) return { background: 'var(--blog-border)', color: 'var(--blog-text-secondary)' }
  return { background: meta.color, color: '#fff' }
}

function badgeTitle(link) {
  const meta = platformMeta(link.platform)
  return meta?.name || link.label || link.platform
}

function badgeLetter(link) {
  const meta = platformMeta(link.platform)
  if (!meta) {
    const seed = link.platform === 'custom' ? link.label : link.platform
    return String(seed || '?').slice(0, 1).toUpperCase()
  }
  return meta.letter
}

function goCategory(id) {
  router.push({ path: '/', query: { category_id: id } })
}

function goTag(id) {
  router.push({ path: '/', query: { tag_id: id } })
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : ''
}

onMounted(async () => {
  if (!Object.keys(configStore.configs).length) await configStore.fetchConfig()
  const [statsRes, catsRes, tagsRes, postsRes] = await Promise.allSettled([
    getSiteStats(),
    getCategories(),
    getTags(),
    getPosts({ page: 1, page_size: 3 }),
  ])
  if (statsRes.status === 'fulfilled') stats.value = statsRes.value.data
  if (catsRes.status === 'fulfilled') categories.value = catsRes.value.data || []
  if (tagsRes.status === 'fulfilled') tags.value = tagsRes.value.data || []
  if (postsRes.status === 'fulfilled') recent.value = postsRes.value.data.items || []
})
</script>

<style scoped>
.about {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sec-title {
  font-family: var(--blog-font-display);
  font-size: 17px;
  margin-bottom: 14px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.hero-id {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.hero-avatar {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blog-primary) 25%, transparent);
}

.hero-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--blog-font-display);
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  background: var(--blog-primary);
}

.hero-name {
  font-family: var(--blog-font-display);
  font-size: 30px;
  line-height: 1.25;
}

.hero-slogan {
  margin-top: 6px;
  color: var(--blog-text-secondary);
  font-size: 14px;
}

.hero-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.link-badge {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  transition: transform 0.2s;
}

.link-badge:hover {
  transform: translateY(-2px) scale(1.06);
}

.intro-fallback {
  color: var(--blog-text-secondary);
  line-height: 1.8;
}

.share-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  background: var(--blog-bg);
}

.share-seg {
  height: 100%;
  min-width: 4px;
}

.share-seg + .share-seg {
  border-left: 2px solid var(--blog-card);
}

.legend {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 22px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: none;
  background: transparent;
  padding: 2px 0;
  font-size: 13px;
  color: var(--blog-text);
  cursor: pointer;
}

.legend-item:hover .legend-name {
  color: var(--blog-primary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-count {
  color: var(--blog-text-secondary);
  font-size: 12px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed var(--blog-border);
}

.tag-btn {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

.ledger-lead {
  font-size: 15px;
  margin-bottom: 14px;
}

.ledger-lead strong {
  font-family: var(--blog-font-display);
  font-size: 22px;
  color: var(--blog-primary);
  padding: 0 2px;
}

.ledger-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 0;
}

.ledger-cell dt {
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.ledger-cell dd {
  margin: 2px 0 0;
  font-size: 17px;
  font-weight: 600;
}

.recent-item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
  padding: 9px 2px;
  border-bottom: 1px dashed var(--blog-border);
  color: var(--blog-text);
  text-decoration: none;
  font-size: 14px;
}

.recent-item:last-child {
  border-bottom: none;
}

.recent-item:hover .recent-title {
  color: var(--blog-primary);
}

.recent-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-date {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--blog-text-secondary);
}

@media (max-width: 768px) {
  .two-col {
    grid-template-columns: 1fr;
  }

  .hero-name {
    font-size: 24px;
  }

  .ledger-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
