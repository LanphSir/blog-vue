<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="name" placeholder="友链名称" style="width: 180px" />
      <el-input v-model="url" placeholder="链接地址" style="width: 240px" />
      <el-button type="primary" @click="handleAdd">新增友链</el-button>
    </div>

    <el-table :data="links" stripe v-loading="loading">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="url" label="地址" min-width="200">
        <template #default="{ row }">
          <a :href="row.url" target="_blank" rel="noopener" class="link">{{ row.url }}</a>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="startEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  adminCreateFriend,
  adminDeleteFriend,
  adminUpdateFriend,
  getFriends,
} from '@/api/site'

const links = ref([])
const loading = ref(false)
const name = ref('')
const url = ref('')
const editingId = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await getFriends()
    links.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!name.value || !url.value) {
    ElMessage.warning('请填写名称和地址')
    return
  }
  if (editingId.value) {
    await adminUpdateFriend(editingId.value, { name: name.value, url: url.value })
    ElMessage.success('已更新')
  } else {
    await adminCreateFriend({ name: name.value, url: url.value, sort_order: 0 })
    ElMessage.success('已创建')
  }
  name.value = ''
  url.value = ''
  editingId.value = null
  load()
}

function startEdit(row) {
  editingId.value = row.id
  name.value = row.name
  url.value = row.url
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除友链「${row.name}」？`, '提示', { type: 'warning' })
  await adminDeleteFriend(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.link {
  color: var(--blog-primary);
}
</style>