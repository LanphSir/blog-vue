<template>
  <div>
    <div class="dashboard-head">
      <h3 class="head-title">数据概览</h3>
      <el-button size="small" :loading="refreshing" @click="load">
        <el-icon class="btn-icon"><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="card in statCards" :key="card.label" :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="recent-card" header="最近发布">
      <el-table :data="recentPosts" stripe v-loading="loading">
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
/* 后台仪表盘：四张统计卡 + 最近发布的文章。刷新按钮重新拉 stats 与最近文章。
 */
import { computed, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { adminGetPosts } from '@/api/posts'
import { getSiteStats } from '@/api/site'

const recentPosts = ref([])
const stats = ref({ post_count: 0, category_count: 0, tag_count: 0, total_views: 0, days_since_launch: 0 })
const loading = ref(false)
const refreshing = ref(false)

const statCards = computed(() => [
  { label: '文章总数', value: stats.value.post_count },
  { label: '分类数', value: stats.value.category_count },
  { label: '标签数', value: stats.value.tag_count },
  { label: '总阅读量', value: stats.value.total_views.toLocaleString() },
])

async function load() {
  refreshing.value = true
  try {
    const [postsRes, statsRes] = await Promise.all([
      adminGetPosts({ page: 1, page_size: 5 }),
      getSiteStats(),
    ])
    recentPosts.value = postsRes.data.items
    stats.value = statsRes.data
  } finally {
    refreshing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.dashboard-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.head-title {
  font-size: 16px;
}

.btn-icon {
  margin-right: 2px;
}

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