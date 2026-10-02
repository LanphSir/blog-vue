<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <el-carousel
        v-if="banners.length"
        :interval="5000"
        height="380px"
        arrow="hover"
        class="hero-carousel"
      >
        <el-carousel-item v-for="banner in banners" :key="banner.id">
          <div class="hero-slide">
            <div v-if="banner.image" class="hero-bg" :style="{ backgroundImage: `url(${banner.image})` }" />
            <div class="hero-overlay" />
            <div class="hero-content">
              <h1 class="hero-title">{{ banner.title }}</h1>
              <p v-if="banner.subtitle" class="hero-subtitle">{{ banner.subtitle }}</p>
              <router-link v-if="banner.link" :to="banner.link" class="hero-cta">前往阅读</router-link>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>

      <div v-else class="hero-fallback">
        <div class="hero-content">
          <h1 class="hero-title">{{ configStore.siteName() }}</h1>
          <p v-if="slogan" class="hero-subtitle">{{ slogan }}</p>
          <router-link to="/posts" class="hero-cta">开始阅读</router-link>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="stats container reveal">
      <button
        v-for="stat in statItems"
        :key="stat.label"
        class="stat"
        :class="{ clickable: !!stat.to }"
        @click="stat.to && $router.push(stat.to)"
      >
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">
          {{ stat.label }}
          <el-icon v-if="stat.to" class="stat-arrow"><Right /></el-icon>
        </div>
      </button>
    </section>

    <!-- Tag tabs + article list -->
    <div class="container feed-layout">
      <div class="feed-main reveal">
        <div class="card feed-toolbar">
          <div class="tabs" :class="{ expanded: tabsExpanded }" ref="tabsEl">
            <button
              class="tab"
              :class="{ active: activeTagId === null }"
              @click="switchTag(null)"
            >
              全部
            </button>
            <button
              v-for="tag in visibleTags"
              :key="tag.id"
              class="tab"
              :class="{ active: activeTagId === tag.id }"
              @click="switchTag(tag.id)"
            >
              {{ tag.name }}
            </button>
          </div>
          <button
            v-if="showTabsToggle"
            class="tabs-toggle"
            @click="tabsExpanded = !tabsExpanded"
          >
            {{ tabsExpanded ? '收起 ▲' : '展开 ▼' }}
          </button>
        </div>

        <el-skeleton v-if="loading" :rows="6" animated />
        <template v-else>
          <PostCard v-for="post in posts" :key="post.id" :post="post" />
          <el-empty v-if="!posts.length" description="该栏目暂无文章" />
          <div class="pager">
            <el-pagination
              v-if="total > pageSize"
              background
              layout="prev, pager, next"
              :total="total"
              :page-size="pageSize"
              :current-page="page"
              @current-change="load"
            />
          </div>
        </template>
      </div>

      <aside class="home-side reveal">
        <HomeSidebar />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Right } from '@element-plus/icons-vue'
import PostCard from '@/components/PostCard.vue'
import HomeSidebar from '@/components/HomeSidebar.vue'
import { useReveal } from '@/composables/useReveal'
import { getPosts } from '@/api/posts'
import { getTags } from '@/api/categories'
import { getBanners, getSiteStats } from '@/api/site'
import { useConfigStore } from '@/stores/config'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()

const posts = ref([])
const allTags = ref([])
const banners = ref([])
const stats = ref({ post_count: 0, tag_count: 0, total_views: 0, days_since_launch: 0 })
const total = ref(0)
const page = ref(1)
const pageSize = ref(6)
const loading = ref(true)
const tabsEl = ref(null)
const tabsExpanded = ref(false)
const showTabsToggle = ref(false)

useReveal()

const slogan = computed(() => configStore.configs.site_description || '')

const visibleTags = computed(() => allTags.value.filter((t) => t.visible !== false))

const activeTagId = computed(() => {
  const tid = Number(route.query.tag_id)
  return Number.isFinite(tid) && tid > 0 && visibleTags.value.some((t) => t.id === tid) ? tid : null
})

const statItems = computed(() => [
  { label: '文章总数', value: stats.value.post_count, to: { name: 'posts' } },
  { label: '标签数', value: stats.value.tag_count, to: { name: 'tags' } },
  { label: '总阅读量', value: stats.value.total_views.toLocaleString(), to: null },
  { label: '运行天数', value: stats.value.days_since_launch, to: null },
])

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize.value }
    if (activeTagId.value !== null) {
      params.tag_id = activeTagId.value
    }
    const res = await getPosts(params)
    posts.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function switchTag(id) {
  router.replace({ query: { tag_id: id || undefined } })
  load(1)
}

function goDetail(slug) {
  router.push({ name: 'post-detail', params: { slug } })
}

function checkTabsOverflow() {
  nextTick(() => {
    const el = tabsEl.value
    if (el) {
      showTabsToggle.value = el.scrollHeight > el.clientHeight + 4
      if (!showTabsToggle.value) tabsExpanded.value = false
    }
  })
}

onMounted(async () => {
  load()
  configStore.fetchConfig()
  const [tagRes, bannerRes, statsRes] = await Promise.all([
    getTags(),
    getBanners(),
    getSiteStats(),
  ])
  allTags.value = tagRes.data
  banners.value = bannerRes.data
  stats.value = statsRes.data
  checkTabsOverflow()
})

watch(visibleTags, checkTabsOverflow)
watch(
  () => route.query,
  () => load(1),
)
</script>

<style scoped>
.hero {
  margin-bottom: 24px;
  border-radius: 14px;
  overflow: hidden;
}

.hero-carousel :deep(.el-carousel__container) {
  border-radius: 14px;
}

.hero-slide {
  position: relative;
  height: 100%;
  background: linear-gradient(120deg, color-mix(in srgb, var(--blog-primary) 82%, #1f2937), #111827);
  display: flex;
  align-items: center;
}

.hero-fallback {
  height: 380px;
  background: linear-gradient(120deg, color-mix(in srgb, var(--blog-primary) 82%, #1f2937), #111827);
  border-radius: 14px;
  display: flex;
  align-items: center;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(17, 24, 39, 0.72), rgba(17, 24, 39, 0.25));
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 0 48px;
  max-width: 640px;
}

.hero-title {
  color: #fff;
  font-family: var(--blog-font-display);
  font-size: 34px;
  line-height: 1.3;
  margin-bottom: 12px;
  animation: fadeUp 0.9s ease both;
}

.hero-subtitle {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  margin-bottom: 20px;
  animation: fadeUp 0.9s 0.25s ease both;
}

.hero-cta {
  display: inline-block;
  padding: 8px 22px;
  border-radius: 999px;
  background: #fff;
  color: var(--blog-primary);
  font-size: 14px;
  font-weight: 600;
  animation: fadeUp 0.9s 0.45s ease both;
  transition: transform 0.2s;
}

.hero-cta:hover {
  transform: translateY(-2px);
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat {
  background: var(--blog-card);
  border: 1px solid var(--blog-border);
  border-radius: 10px;
  padding: 18px;
  text-align: center;
  font-family: inherit;
  color: inherit;
  cursor: default;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.stat.clickable {
  cursor: pointer;
}

.stat.clickable:hover {
  transform: translateY(-2px);
  border-color: var(--blog-primary);
  box-shadow: 0 6px 16px color-mix(in srgb, var(--blog-primary) 12%, transparent);
}

.stat-value {
  font-family: var(--blog-font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--blog-primary);
}

.stat-label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--blog-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stat-arrow {
  font-size: 12px;
  opacity: 0.6;
}

.feed-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.feed-main {
  flex: 1;
  min-width: 0;
}

.feed-toolbar {
  margin-bottom: 16px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 84px; /* two rows */
  overflow: hidden;
  position: relative;
  transition: max-height 0.3s ease;
}

.tabs.expanded {
  max-height: none;
}

.tab {
  padding: 7px 16px;
  border: 1px solid var(--blog-border);
  border-radius: 999px;
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  color: var(--blog-primary);
  border-color: color-mix(in srgb, var(--blog-primary) 40%, transparent);
}

.tab.active {
  color: #fff;
  background: var(--blog-primary);
  border-color: var(--blog-primary);
}

.tabs-toggle {
  margin-top: 10px;
  padding: 5px 18px;
  border: 1px dashed var(--blog-border);
  border-radius: 999px;
  background: transparent;
  color: var(--blog-primary);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s;
}

.tabs-toggle:hover {
  border-color: var(--blog-primary);
  background: color-mix(in srgb, var(--blog-primary) 8%, transparent);
}

.sub-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--blog-border);
}

.chip {
  padding: 4px 12px;
  border: 1px solid var(--blog-border);
  border-radius: 6px;
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s;
}

.chip:hover {
  color: var(--blog-primary);
}

.chip.active {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
  background: color-mix(in srgb, var(--blog-primary) 8%, transparent);
}

.breadcrumb {
  margin-top: 12px;
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.crumb {
  cursor: pointer;
}

.crumb:hover {
  color: var(--blog-primary);
}

.crumb.current {
  color: var(--blog-primary);
  font-weight: 500;
  cursor: default;
}

.sep {
  margin: 0 6px;
  opacity: 0.5;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.home-side {
  width: 240px;
  flex-shrink: 0;
}

.side-card h3 {
  font-size: 14px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--blog-border);
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  cursor: pointer;
}

.side-empty {
  color: var(--blog-text-secondary);
  font-size: 12px;
}

.recent-list {
  list-style: none;
}

.recent-list li {
  margin-bottom: 10px;
  font-size: 13px;
}

.recent-list a {
  color: var(--blog-text-secondary);
}

.recent-list a:hover {
  color: var(--blog-primary);
}

@media (max-width: 768px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .feed-layout {
    flex-direction: column;
  }

  .home-side {
    width: 100%;
  }

  .hero-content {
    padding: 0 24px;
  }

  .hero-title {
    font-size: 26px;
  }
}
</style>