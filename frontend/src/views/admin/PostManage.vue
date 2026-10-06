<template>
  <el-card>
    <div class="toolbar">
      <el-radio-group v-model="recycleMode" size="default" @change="recycleMode = $event; load(1)">
        <el-radio-button :value="false">文章列表</el-radio-button>
        <el-radio-button :value="true">回收站</el-radio-button>
      </el-radio-group>
      <el-input v-model="keyword" placeholder="搜索标题" clearable style="width: 220px" @clear="load(1)" @keyup.enter="load(1)" />
      <el-select v-if="!recycleMode" v-model="status" placeholder="状态" clearable style="width: 130px" @change="load(1)">
        <el-option label="已发布" value="published" />
        <el-option label="草稿" value="draft" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button v-if="!recycleMode" type="success" @click="goCreate">新建文章</el-button>
      <el-button v-else type="danger" plain @click="emptyRecycle">清空回收站</el-button>
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

      <template v-if="!recycleMode">
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
            <el-switch :model-value="row.status === 'published'" size="small" @change="togglePublish(row)" />
          </template>
        </el-table-column>
        <el-table-column label="权重" width="110">
          <template #default="{ row }">
            <el-input-number :model-value="row.sort_weight" :min="0" size="small" controls-position="right" @change="changeWeight(row, $event)" />
          </template>
        </el-table-column>
      </template>

      <el-table-column prop="view_count" label="阅读" width="90" />
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ new Date(row.updated_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="recycleMode ? 160 : 200" fixed="right">
        <template #default="{ row }">
          <template v-if="recycleMode">
            <el-button link type="primary" @click="handleRestore(row)">恢复</el-button>
            <el-button link type="danger" @click="handlePermanentDelete(row)">彻底删除</el-button>
          </template>
          <template v-else>
            <el-button link type="primary" @click="goEdit(row.id)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
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
import {
  adminDeletePost,
  adminGetPosts,
  adminPermanentDeletePost,
  adminRestorePost,
  adminUpdatePost,
} from '@/api/posts'

const router = useRouter()
const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const status = ref('')
const loading = ref(false)
const recycleMode = ref(false)

async function load(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize.value, deleted: recycleMode.value }
    if (keyword.value) params.keyword = keyword.value
    if (!recycleMode.value && status.value) params.status = status.value
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
  try {
    await ElMessageBox.confirm(`确认删除文章「${row.title}」？删除后进入回收站，可恢复。`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  await adminDeletePost(row.id)
  ElMessage.success('已移入回收站')
  load()
}

async function handleRestore(row) {
  await adminRestorePost(row.id)
  ElMessage.success(`已恢复「${row.title}」`)
  load()
}

async function handlePermanentDelete(row) {
  try {
    await ElMessageBox.confirm(
      `彻底删除「${row.title}」？该操作不可恢复！`,
      '危险操作',
      { type: 'error', confirmButtonText: '彻底删除', confirmButtonClass: 'el-button--danger' },
    )
  } catch {
    return
  }
  await adminPermanentDeletePost(row.id)
  ElMessage.success('已彻底删除')
  load()
}

async function emptyRecycle() {
  try {
    await ElMessageBox.confirm(
      `确定清空回收站（${total.value} 篇文章将彻底删除，不可恢复）？`,
      '危险操作',
      { type: 'error', confirmButtonText: '清空', confirmButtonClass: 'el-button--danger' },
    )
  } catch {
    return
  }
  const items = posts.value
  for (const post of items) {
    await adminPermanentDeletePost(post.id)
  }
  ElMessage.success('回收站已清空')
  load()
}

onMounted(() => load())
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>