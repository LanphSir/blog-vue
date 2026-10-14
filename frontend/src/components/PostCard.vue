<template>
  <article class="post-card" @click="goDetail">
    <div v-if="post.cover_image" class="thumb">
      <img :src="post.cover_image" :alt="post.title" loading="lazy" />
    </div>

    <div class="body">
      <div class="badges">
        <el-tag v-if="post.is_top" type="danger" size="small" effect="dark" class="badge">置顶</el-tag>
        <span v-if="post.is_featured" class="badge featured">推荐</span>
        <span
          v-if="post.category?.name"
          class="badge category"
          :style="categoryStyle"
          @click.stop="goCategory"
        >
          <span class="cat-dot" :style="categoryDotStyle" />
          {{ post.category.name }}
        </span>
      </div>

      <h3 class="title">{{ post.title }}</h3>

      <p class="summary">{{ post.summary || '暂无摘要' }}</p>

      <div class="tags">
        <ColoredTag
          v-for="tag in post.tags"
          :key="tag.id"
          :text="tag.name"
          :color="tag.color"
          class="tag"
          @click.stop="goTag(tag.id)"
        />
      </div>

      <div class="meta">
        <span class="author">
          <span class="avatar">{{ avatarText }}</span>
          {{ authorName }}
        </span>
        <span class="dot">·</span>
        <span>{{ formatDate(post.published_at) }}</span>
        <span class="dot">·</span>
        <span>{{ post.view_count }} 阅读</span>
      </div>
    </div>
  </article>
</template>

<script setup>
/* 文章卡片：列表里每篇文章的封面/置顶推荐/分类/标签/元信息展示。
 * 整个卡片可点进入详情；分类徽章与标签都带 @click.stop 阻断卡片跳转、
 * 各自跳去对应分类/标签列表，避免事件冒泡触发 goDetail。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import ColoredTag from '@/components/ColoredTag.vue'
import { useConfigStore } from '@/stores/config'

const props = defineProps({
  post: { type: Object, required: true },
})

const router = useRouter()
const configStore = useConfigStore()

const authorName = computed(() => props.post.author || configStore.configs.site_author || '站长')
const avatarText = computed(() => authorName.value.slice(0, 1).toUpperCase())

const categoryColor = computed(() => props.post.category?.color || 'var(--blog-primary)')

const categoryStyle = computed(() => ({
  color: categoryColor.value,
  background: `color-mix(in srgb, ${categoryColor.value} 12%, transparent)`,
  border: `1px solid color-mix(in srgb, ${categoryColor.value} 38%, transparent)`,
}))

const categoryDotStyle = computed(() => ({ background: categoryColor.value }))

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : ''
}

function goDetail() {
  router.push({ name: 'post-detail', params: { slug: props.post.slug } })
}

function goCategory() {
  if (props.post.category?.id) {
    router.push({ name: 'posts', query: { category_id: props.post.category.id } })
  }
}

function goTag(id) {
  router.push({ name: 'posts', query: { tag_id: id } })
}
</script>

<style scoped>
.post-card {
  background: var(--blog-card);
  border: 1px solid var(--blog-border);
  border-radius: 12px;
  box-shadow: var(--blog-shadow);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 16px;
}

.post-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.08);
}

.thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 6;
  overflow: hidden;
  background: linear-gradient(120deg, color-mix(in srgb, var(--blog-primary) 30%, #111827), #111827);
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s;
}

.post-card:hover .thumb img {
  transform: scale(1.03);
}

.body {
  padding: 18px 20px 16px;
}

.badges {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.badge {
  font-size: 12px;
  line-height: 1.6;
  padding: 1px 8px;
  border-radius: 6px;
}

.badge.featured {
  color: var(--blog-primary);
  background: color-mix(in srgb, var(--blog-primary) 12%, transparent);
}

.badge.category {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 10px;
  border-radius: 999px;
  font-weight: 500;
  cursor: pointer;
}

.cat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.title {
  font-family: var(--blog-font-display);
  font-size: 19px;
  line-height: 1.4;
  margin-bottom: 8px;
  transition: color 0.2s;
}

.post-card:hover .title {
  color: var(--blog-primary);
}

.summary {
  color: var(--blog-text-secondary);
  font-size: 13.5px;
  line-height: 1.7;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.tag {
  cursor: pointer;
}

.meta {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--blog-text-secondary);
  font-size: 12.5px;
}

.author {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--blog-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dot {
  opacity: 0.6;
}
</style>