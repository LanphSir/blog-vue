<template>
  <div class="category-page">
    <h1 class="page-title">全部分类</h1>

    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <section v-for="group in tree" :key="group.id" class="category-block reveal">
        <h2 class="section-title" :style="{ borderColor: group.color }">
          <router-link :to="{ name: 'posts', query: { category_id: group.id } }">{{ group.name }}</router-link>
          <span class="count">{{ group.post_count }}</span>
        </h2>

        <div v-if="group.children.length" class="sub-categories">
          <router-link
            v-for="child in group.children"
            :key="child.id"
            :to="{ name: 'posts', query: { category_id: child.id } }"
            class="sub-category card"
          >
            <span class="dot" :style="{ background: child.color || 'var(--blog-primary)' }" />
            {{ child.name }}
            <span class="count">{{ child.post_count }}</span>
          </router-link>
        </div>

        <div class="post-list">
          <PostCard v-for="post in postsByGroup[group.id] || []" :key="post.id" :post="post" />
          <span v-if="!postsByGroup[group.id]?.length" class="empty-hint">暂无文章</span>
        </div>
      </section>

      <el-empty v-if="!tree.length" description="暂无分类" />
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import PostCard from '@/components/PostCard.vue'
import { useReveal } from '@/composables/useReveal'
import { getCategoryTree } from '@/api/categories'
import { getPosts } from '@/api/posts'

const tree = ref([])
const postsByGroup = ref({})
const loading = ref(true)

useReveal()

onMounted(async () => {
  loading.value = true
  try {
    const res = await getCategoryTree()
    tree.value = res.data
    const list = [...res.data, ...res.data.flatMap((g) => g.children || [])]
    await Promise.all(
      list.map(async (group) => {
        try {
          const postsRes = await getPosts({ page: 1, page_size: 8, category_id: group.id })
          postsByGroup.value[group.id] = postsRes.data.items
        } catch {
          postsByGroup.value[group.id] = []
        }
      }),
    )
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title {
  font-family: var(--blog-font-display);
  margin-bottom: 20px;
}

.category-block {
  margin-bottom: 24px;
}

.category-block .count {
  font-size: 12px;
  color: var(--blog-text-secondary);
  margin-left: 8px;
}

.sub-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.sub-category {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  margin-bottom: 0;
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.sub-category:hover {
  color: var(--blog-primary);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.post-list {
  display: flex;
  flex-direction: column;
}

.post-list :deep(.post-card) {
  margin-bottom: 12px;
}

.empty-hint {
  color: var(--blog-text-secondary);
  font-size: 13px;
  padding: 8px 0;
}
</style>