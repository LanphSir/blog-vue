<template>
  <div>
    <el-row :gutter="16">
      <el-col v-for="card in stats" :key="card.label" :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="recent-card" header="最近发布">
      <el-table :data="recentPosts" stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览量" width="100" />
        <el-table-column label="发布时间" width="180">
          <template #default="{ row }">
            {{ row.published_at ? new Date(row.published_at).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { adminGetPosts } from '@/api/posts'
import { getCategories, getTags } from '@/api/categories'

const recentPosts = ref([])
const categoryCount = ref(0)
const tagCount = ref(0)

const stats = computed(() => [
  { label: '文章总数', value: recentPosts.value.length },
  { label: '分类数', value: categoryCount.value },
  { label: '标签数', value: tagCount.value },
  { label: '总阅读量', value: recentPosts.value.reduce((s, p) => s + p.view_count, 0) },
])

onMounted(async () => {
  const [postsRes, catRes, tagRes] = await Promise.all([
    adminGetPosts({ page: 1, page_size: 5 }),
    getCategories(),
    getTags(),
  ])
  recentPosts.value = postsRes.data.items
  categoryCount.value = catRes.data.length
  tagCount.value = tagRes.data.length
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  color: var(--blog-text-secondary);
  margin-top: 4px;
}

.recent-card {
  margin-top: 16px;
}
</style>