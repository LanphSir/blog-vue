<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索标题" clearable style="width: 240px" @clear="load(1)" @keyup.enter="load(1)" />
      <el-select v-model="status" placeholder="状态" clearable style="width: 140px" @change="load(1)">
        <el-option label="已发布" value="published" />
        <el-option label="草稿" value="draft" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button type="success" @click="goCreate">新建文章</el-button>
    </div>

    <el-table :data="posts" stripe v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
            {{ row.status === 'published' ? '已发布' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="置顶" width="70" align="center">
        <template #default="{ row }">
          <el-switch :model-value="row.is_top" size="small" @change="toggleFlag(row, 'is_top')" />
        </template>
      </el-table-column>
      <el-table-column label="推荐" width="70" align="center">
        <template #default="{ row }">
          <el-switch :model-value="row.is_featured" size="small" @change="toggleFlag(row, 'is_featured')" />
        </template>
      </el-table-column>
      <el-table-column label="发布" width="70" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 'published'"
            size="small"
            @change="togglePublish(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="权重" width="110">
        <template #default="{ row }">
          <el-input-number
            :model-value="row.sort_weight"
            :min="0"
            size="small"
            controls-position="right"
            @change="changeWeight(row, $event)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="view_count" label="阅读" width="90" />
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ new Date(row.updated_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goEdit(row.id)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="load"
      />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminDeletePost, adminGetPosts, adminUpdatePost } from '@/api/posts'

const router = useRouter()
const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const status = ref('')
const loading = ref(false)

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (status.value) params.status = status.value
    const res = await adminGetPosts(params)
    posts.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function goCreate() {
  router.push({ name: 'admin-post-create' })
}

function goEdit(id) {
  router.push({ name: 'admin-post-edit', params: { id } })
}

async function toggleFlag(row, field) {
  await adminUpdatePost(row.id, { [field]: !row[field] })
  row[field] = !row[field]
  ElMessage.success('已更新')
}

async function togglePublish(row) {
  const newStatus = row.status === 'published' ? 'draft' : 'published'
  await adminUpdatePost(row.id, { status: newStatus })
  row.status = newStatus
  ElMessage.success(newStatus === 'published' ? '已发布' : '已取消发布')
}

async function changeWeight(row, value) {
  await adminUpdatePost(row.id, { sort_weight: value || 0 })
  row.sort_weight = value || 0
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除文章「${row.title}」？`, '提示', { type: 'warning' })
  await adminDeletePost(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => load())
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>