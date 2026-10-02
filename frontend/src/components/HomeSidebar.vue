<template>
  <aside class="home-side">
    <ProfileCard v-if="profileVisible" class="reveal" />

    <div v-if="tagsVisible" class="card side-card reveal">
      <h3>标签云</h3>
      <div class="tag-cloud">
        <ColoredTag
          v-for="t in displayTags"
          :key="t.id"
          :text="t.name"
          :color="t.color"
          class="tag-chip"
          @click="filterByTag(t.id)"
        />
        <button
          v-if="hasMoreTags"
          class="more-btn"
          @click="$router.push({ name: 'home', query: { tag_id: allTags[0]?.id || undefined } })"
        >
          更多 +
        </button>
        <span v-if="!allTags.length" class="side-empty">暂无标签</span>
      </div>
    </div>

    <div v-if="recentVisible" class="card side-card reveal">
      <h3>最近发布</h3>
      <ul class="recent-list">
        <li v-for="p in recentPosts" :key="p.id">
          <a href="#" @click.prevent="goDetail(p.slug)">{{ p.title }}</a>
        </li>
        <span v-if="!recentPosts.length" class="side-empty">暂无文章</span>
      </ul>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ProfileCard from '@/components/ProfileCard.vue'
import ColoredTag from '@/components/ColoredTag.vue'
import { useReveal } from '@/composables/useReveal'
import { getTags } from '@/api/categories'
import { getPosts } from '@/api/posts'
import { useConfigStore } from '@/stores/config'

const router = useRouter()
const configStore = useConfigStore()

const allTags = ref([])
const recentPosts = ref([])

useReveal()

function isEnabled(value) {
  return value === undefined || value === '' || value === 'true' || value === '1' || value === true
}

const profileVisible = computed(() => isEnabled(configStore.configs.profile_visible))
const tagsVisible = computed(() => isEnabled(configStore.configs.sidebar_tags_visible))
const recentVisible = computed(() => isEnabled(configStore.configs.sidebar_recent_visible))
const tagLimit = computed(() => {
  const n = Number(configStore.configs.sidebar_tag_count || 8)
  return Number.isFinite(n) && n > 0 ? n : 8
})

const displayTags = computed(() => allTags.value.filter((t) => t.visible !== false).slice(0, tagLimit.value))
const hasMoreTags = computed(() => allTags.value.filter((t) => t.visible !== false).length > tagLimit.value)

function goDetail(slug) {
  router.push({ name: 'post-detail', params: { slug } })
}

function filterByTag(id) {
  router.push({ name: 'posts', query: { tag_id: id } })
}

onMounted(async () => {
  const [tagRes, recentRes] = await Promise.all([
    getTags(),
    getPosts({ page: 1, page_size: 5 }),
  ])
  allTags.value = tagRes.data
  recentPosts.value = recentRes.data.items
})
</script>

<style scoped>
.home-side {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
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

.more-btn {
  width: 100%;
  border: 1px dashed var(--blog-border);
  background: transparent;
  color: var(--blog-primary);
  font-size: 12px;
  border-radius: 999px;
  padding: 4px 0;
  margin-top: 6px;
  cursor: pointer;
}

.more-btn:hover {
  border-color: var(--blog-primary);
  background: color-mix(in srgb, var(--blog-primary) 8%, transparent);
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
  .home-side {
    width: 100%;
  }
}
</style>