<template>
  <div class="archive">
    <div class="card head">
      <h1>文章归档</h1>
      <p class="head-hint">
        <template v-if="total">共 {{ total }} 篇文章，按发布时间倒序排列。</template>
        <template v-else>还没有已发布的文章。</template>
      </p>
    </div>

    <section v-for="group in groups" :key="`${group.year}-${group.month}`" class="card year-block">
      <h2 class="month-title">
        {{ group.year }} 年 {{ group.month }} 月
        <span class="month-count">{{ group.posts.length }} 篇</span>
      </h2>
      <router-link
        v-for="post in group.posts"
        :key="post.id"
        class="post-row"
        :to="{ name: 'post-detail', params: { slug: post.slug } }"
      >
        <time class="post-date">{{ dayOf(post.published_at) }}</time>
        <span class="post-title">{{ post.title }}</span>
      </router-link>
    </section>
  </div>
</template>

<script setup>
/* 归档页：按 年/月 分组的文章列表，数据来自 getArchive（后端已按发布时间倒序分组好）。
 * 这里只做展示与总数合计，不自行聚合。
 */
import { computed, onMounted, ref } from 'vue'
import { getArchive } from '@/api/posts'
import { useReveal } from '@/composables/useReveal'

useReveal()

const groups = ref([])

const total = computed(() => groups.value.reduce((sum, g) => sum + g.posts.length, 0))

function dayOf(value) {
  if (!value) return ''
  const d = new Date(value)
  return `${String(d.getDate()).padStart(2, '0')} 日`
}

onMounted(async () => {
  try {
    const res = await getArchive()
    groups.value = res.data || []
  } catch {
    groups.value = []
  }
})
</script>

<style scoped>
.archive {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.head h1 {
  font-family: var(--blog-font-display);
  font-size: 26px;
  margin: 0 0 6px;
}

.head-hint {
  margin: 0;
  color: var(--blog-text-secondary);
  font-size: 14px;
}

.month-title {
  font-family: var(--blog-font-display);
  font-size: 17px;
  margin: 0 0 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--blog-border);
}

.month-count {
  float: right;
  font-size: 12px;
  font-weight: 400;
  color: var(--blog-text-secondary);
}

.post-row {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding: 8px 2px;
  border-radius: 6px;
  color: var(--blog-text);
  text-decoration: none;
  font-size: 14px;
}

.post-row:hover {
  background: color-mix(in srgb, var(--blog-primary) 6%, transparent);
}

.post-row:hover .post-title {
  color: var(--blog-primary);
}

.post-date {
  flex-shrink: 0;
  width: 44px;
  font-size: 12px;
  color: var(--blog-text-secondary);
  font-variant-numeric: tabular-nums;
}

.post-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
