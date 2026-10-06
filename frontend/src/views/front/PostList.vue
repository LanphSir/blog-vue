<template>
  <div class="list-layout">
    <div class="list-main">
      <div class="filter-bar card">
        <div class="search-group">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="keyword"
            class="search-input"
            type="search"
            placeholder="搜索文章标题或内容…"
            @keyup.enter="load(1)"
          />
          <button v-if="keyword" class="search-clear" aria-label="清空" @click="keyword = ''; load(1)">
            <el-icon><Close /></el-icon>
          </button>
          <button class="search-btn" @click="load(1)">搜索</button>
        </div>
        <span v-if="activeTag" class="tag-filter">
          <ColoredTag :text="`标签：${activeTag.name}`" :color="activeTag.color" @click="clearTag" />
        </span>
      </div>

    <div v-if="roots.length" class="card category-nav">
      <div class="cat-level">
        <button class="cat-item" :class="{ active: activeCategory === null && !activeTag }" @click="pickCategory(null)">
          全部
        </button>
        <button
          v-for="root in roots"
          :key="root.id"
          class="cat-item"
          :class="{ active: activeCategory === root.id }"
          @click="pickCategory(root.id)"
        >
          {{ root.name }}
          <span class="count">{{ root.post_count }}</span>
        </button>
      </div>
      <div v-if="currentRoot?.children?.length" class="cat-level sub">
        <button class="cat-item" :class="{ active: activeCategory === currentRoot.id }" @click="pickCategory(currentRoot.id)">
          全部子栏目
        </button>
        <button
          v-for="child in currentRoot.children"
          :key="child.id"
          class="cat-item"
          :class="{ active: activeCategory === child.id }"
          @click="pickCategory(child.id)"
        >
          {{ child.name }}
          <span class="count">{{ child.post_count }}</span>
        </button>
      </div>
      <nav v-if="activeCategory !== null || activeTag" class="breadcrumb">
        <button class="crumb" @click="pickCategory(null)">全部</button>
        <template v-if="currentRoot">
          <span class="sep">›</span>
          <button class="crumb" :class="{ current: activeCategory === currentRoot.id }" @click="pickCategory(currentRoot.id)">
            {{ currentRoot.name }}
          </button>
          <template v-if="currentChild">
            <span class="sep">›</span>
            <button class="crumb current" @click="pickCategory(currentChild.id)">{{ currentChild.name }}</button>
          </template>
        </template>
        <template v-if="activeTag">
          <span class="sep">›</span>
          <span class="crumb current">标签：{{ activeTag.name }}</span>
        </template>
      </nav>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
      <el-empty v-if="!posts.length" description="暂无文章" />
      <div class="pager">
        <el-pagination
          v-if="total > pageSize"
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="load"
        />
      </div>
      </template>
    </div>

    <aside class="list-side">
      <HomeSidebar />
    </aside>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, Search } from '@element-plus/icons-vue'
import PostCard from '@/components/PostCard.vue'
import ColoredTag from '@/components/ColoredTag.vue'
import HomeSidebar from '@/components/HomeSidebar.vue'
import { getPosts } from '@/api/posts'
import { getCategoryTree, getTags } from '@/api/categories'

const route = useRoute()
const router = useRouter()
const posts = ref([])
const tree = ref([])
const allTags = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const loading = ref(true)

const roots = computed(() => tree.value)

const activeCategory = computed(() => {
  const cid = Number(route.query.category_id)
  return Number.isFinite(cid) && cid > 0 ? cid : null
})

const activeTag = computed(() => {
  const tid = Number(route.query.tag_id)
  if (!Number.isFinite(tid) || tid <= 0) return null
  return allTags.value.find((t) => t.id === tid) || null
})

const currentRoot = computed(() => {
  if (activeCategory.value === null) return null
  for (const root of tree.value) {
    if (root.id === activeCategory.value) return root
    if (root.children.some((c) => c.id === activeCategory.value)) return root
  }
  return null
})

const currentChild = computed(() => {
  if (activeCategory.value === null) return null
  return currentRoot.value?.children.find((c) => c.id === activeCategory.value) || null
})

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (activeCategory.value !== null) params.category_id = activeCategory.value
    if (activeTag.value) params.tag_id = activeTag.value.id
    const res = await getPosts(params)
    posts.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function pickCategory(id) {
  router.replace({ query: { ...route.query, category_id: id || undefined } })
}

function clearTag() {
  router.replace({ query: { ...route.query, tag_id: undefined } })
}

onMounted(async () => {
  const [treeRes, tagRes] = await Promise.all([getCategoryTree(), getTags()])
  tree.value = treeRes.data
  allTags.value = tagRes.data
  load()
})

watch(
  () => route.query,
  () => load(1),
)
</script>

<style scoped>
.list-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.list-main {
  flex: 1;
  min-width: 0;
}

.list-side {
  width: 240px;
  flex-shrink: 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  flex-wrap: wrap;
}

.search-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 220px;
  max-width: 480px;
  padding: 6px 8px 6px 12px;
  border: 1.5px solid var(--blog-border);
  border-radius: 999px;
  background: var(--blog-bg);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-group:focus-within {
  border-color: var(--blog-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--blog-primary) 14%, transparent);
}

.search-icon {
  color: var(--blog-text-secondary);
  font-size: 16px;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--blog-text);
}

.search-input::placeholder {
  color: var(--blog-text-secondary);
}

.search-clear {
  border: none;
  background: transparent;
  color: var(--blog-text-secondary);
  display: inline-flex;
  align-items: center;
  padding: 2px;
  cursor: pointer;
  flex-shrink: 0;
}

.search-clear:hover {
  color: var(--blog-primary);
}

.search-btn {
  padding: 6px 20px;
  border: none;
  border-radius: 999px;
  background: var(--blog-primary);
  color: #fff;
  font-size: 13.5px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s, transform 0.2s;
}

.search-btn:hover {
  opacity: 0.9;
  transform: scale(1.03);
}

.tag-filter {
  cursor: pointer;
}

.category-nav {
  margin-bottom: 16px;
}

.cat-level {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cat-level.sub {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--blog-border);
}

.cat-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--blog-border);
  border-radius: 999px;
  background: transparent;
  color: var(--blog-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.cat-item:hover {
  color: var(--blog-primary);
  border-color: color-mix(in srgb, var(--blog-primary) 40%, transparent);
}

.cat-item.active {
  color: #fff;
  background: var(--blog-primary);
  border-color: var(--blog-primary);
}

.cat-item .count {
  font-size: 11px;
  opacity: 0.75;
}

.breadcrumb {
  display: flex;
  align-items: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.crumb {
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  color: var(--blog-text-secondary);
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
  margin: 0 8px;
  opacity: 0.5;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .list-layout {
    flex-direction: column;
  }

  .list-side {
    width: 100%;
  }
}
</style>