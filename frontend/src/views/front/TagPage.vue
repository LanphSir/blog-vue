<template>
  <div class="tag-page">
    <header class="tag-header reveal">
      <h1 class="page-title">标签云</h1>
      <p class="page-subtitle">共 {{ visibleTags.length }} 个标签，点击查看对应文章</p>
    </header>

    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <div class="tag-cloud card reveal">
        <button
          v-for="tag in visibleTags"
          :key="tag.id"
          class="tag-item"
          :style="tagItemStyle(tag)"
          :title="`${tag.name}（${tag.post_count} 篇文章）`"
          @click="goTag(tag.id)"
        >
          <span class="tag-name">{{ tag.name }}</span>
          <span class="count">{{ tag.post_count }}</span>
        </button>
        <el-empty v-if="!visibleTags.length" description="暂无标签" />
      </div>
    </template>
  </div>
</template>

<script setup>
/* 标签云页：全部可见标签，字号/底色随文章数缩放（tagItemStyle 按 maxCount 归一化）。
 * 只展示 visible!==false 的标签；按文章数降序、同名升序排。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useReveal } from '@/composables/useReveal'
import { getTags } from '@/api/categories'

const router = useRouter()
const allTags = ref([])
const loading = ref(true)

useReveal()

const visibleTags = computed(() =>
  allTags.value
    .filter((t) => t.visible !== false)
    .sort((a, b) => (b.post_count || 0) - (a.post_count || 0) || a.name.localeCompare(b.name)),
)

const maxCount = computed(() => Math.max(...visibleTags.value.map((t) => t.post_count || 0), 0) || 1)

function tagItemStyle(tag) {
  const size = 0.9 + ((tag.post_count || 0) / maxCount.value) * 0.8
  const color = tag.color || 'var(--blog-primary)'
  return {
    fontSize: `${(size * 15).toFixed(1)}px`,
    '--tag-fg': color,
    '--tag-bg': `color-mix(in srgb, ${color} 12%, transparent)`,
    '--tag-border': `color-mix(in srgb, ${color} 40%, transparent)`,
  }
}

function goTag(id) {
  router.push({ name: 'posts', query: { tag_id: id } })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getTags()
    allTags.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.tag-page {
  max-width: 820px;
  margin: 0 auto;
  padding: 8px 0 24px;
}

.tag-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-title {
  font-family: var(--blog-font-display);
  font-size: 30px;
  margin-bottom: 8px;
}

.page-subtitle {
  color: var(--blog-text-secondary);
  font-size: 14px;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 14px;
  padding: 36px 28px;
  min-height: 200px;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: 1px solid var(--tag-border, var(--blog-border));
  border-radius: 999px;
  background: var(--tag-bg, transparent);
  color: var(--tag-fg, var(--blog-text));
  cursor: pointer;
  line-height: 1.6;
  font-weight: 500;
  transition: transform 0.2s, box-shadow 0.2s;
}

.tag-item:hover {
  transform: translateY(-3px) scale(1.04);
  box-shadow: 0 6px 16px color-mix(in srgb, var(--tag-fg, #000) 18%, transparent);
}

.count {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tag-fg, #888) 14%, transparent);
  opacity: 0.85;
}
</style>