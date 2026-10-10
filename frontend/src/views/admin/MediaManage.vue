<template>
  <el-card>
    <div class="mm-layout">
      <aside class="mm-tree">
        <div class="mm-tree-title">目录</div>
        <el-tree
          :data="treeData"
          node-key="key"
          :expand-on-click-node="false"
          highlight-current
          default-expand-all
          :current-node-key="currentTreeKey"
          @node-click="onNodeClick"
        />
      </aside>
      <div class="mm-main">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-upload :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="handleUpload">
          <el-button type="primary" :loading="uploading">上传图片</el-button>
        </el-upload>
        <span class="tip">文件按 年/月 归档，文件名自动加时间戳与内容哈希；站点名称等配置图片请使用 站点配置 页。</span>
      </div>
      <el-input
        v-model="keyword"
        placeholder="按文件名筛选"
        clearable
        style="width: 200px"
        @keyup.enter="reload"
        @clear="reload"
      >
        <template #append><el-button :icon="Search" @click="reload" /></template>
      </el-input>
    </div>

    <el-table :data="filtered" stripe v-loading="loading" row-key="id">
      <el-table-column label="预览" width="110">
        <template #default="{ row }">
          <el-image :src="row.url" style="width: 84px; height: 52px; border-radius: 4px" fit="cover" :preview-src-list="[row.url]" preview-teleported lazy>
            <template #error><div class="thumb-fallback">{{ row.ext }}</div></template>
          </el-image>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="原始文件名" min-width="180" show-overflow-tooltip />
      <el-table-column prop="stored_name" label="存储文件名" min-width="200" show-overflow-tooltip />
      <el-table-column label="所在目录" width="140">
        <template #default="{ row }">{{ dirLabel(row.rel_path) }}</template>
      </el-table-column>
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ fmtSize(row.size) }}</template>
      </el-table-column>
      <el-table-column label="上传时间" width="150">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="copyUrl(row)">复制链接</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="load"
    />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { adminDeleteMedia, adminListMedia, adminMediaFolders, uploadImage } from '@/api/upload'
import { buildFolderTree } from '@/utils/mediaTree'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const uploading = ref(false)
const keyword = ref('')
const folders = ref([])
const currentDir = ref('')

const treeData = computed(() => buildFolderTree(folders.value))
const currentTreeKey = computed(() => currentDir.value)

function dirLabel(relPath) {
  if (!relPath || !relPath.includes('/')) return '未分类'
  return relPath.split('/').slice(0, -1).join('/')
}

async function loadFolders() {
  try {
    const res = await adminMediaFolders()
    folders.value = res.data
  } catch {
    folders.value = []
  }
}

function onNodeClick(node) {
  currentDir.value = node.dir
  load(1)
}

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((i) => i.name.toLowerCase().includes(kw) || i.stored_name.toLowerCase().includes(kw))
})

async function load(toPage = 1) {
  page.value = toPage
  loading.value = true
  try {
    const params = { page: toPage, page_size: pageSize }
    if (currentDir.value) params.dir = currentDir.value
    const res = await adminListMedia(params)
    items.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function reload() {
  load(1)
}

async function handleUpload(uploadFile) {
  const raw = uploadFile.raw || uploadFile
  if (!raw) return
  uploading.value = true
  try {
    const res = await uploadImage(raw)
    ElMessage.success(`已上传：${res.data}`)
    await Promise.all([load(1), loadFolders()])
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

async function copyUrl(row) {
  try {
    await navigator.clipboard.writeText(row.url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning(`复制失败，请手动复制：${row.url}`)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认后删除「${row.stored_name}」？若文件仍被文章/轮播/页脚引用，删除后相关图片将失效。`,
      '删除图片',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await adminDeleteMedia(row.id)
    ElMessage.success('已删除')
    await Promise.all([load(items.value.length === 1 && page.value > 1 ? page.value - 1 : page.value), loadFolders()])
  } catch (err) {
    const detail = err?.response?.data?.message
    if (err?.response?.status === 409) {
      try {
        await ElMessageBox.confirm(
          `${detail || '该文件仍被引用'}。仍要强制删除吗？`,
          '文件被引用',
          { type: 'warning', confirmButtonText: '强制删除', cancelButtonText: '取消' },
        )
      } catch {
        return
      }
      await adminDeleteMedia(row.id, true)
      ElMessage.success('已强制删除')
      await Promise.all([load(page.value), loadFolders()])
    } else if (detail) {
      ElMessage.warning(detail)
    }
  }
}

function fmtSize(n) {
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(0)} KB`
  return `${n} B`
}

function fmtDate(raw) {
  return raw ? String(raw).replace('T', ' ').slice(0, 16) : ''
}

onMounted(() => {
  loadFolders()
  load()
})
</script>

<style scoped>
.mm-layout {
  display: flex;
  gap: 18px;
  align-items: flex-start;
}

.mm-tree {
  width: 210px;
  flex-shrink: 0;
  border-right: 1px solid var(--blog-border);
  padding-right: 14px;
}

.mm-tree-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 8px;
  color: var(--blog-text-secondary);
}

.mm-main {
  flex: 1;
  min-width: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tip {
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.thumb-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 52px;
  font-size: 11px;
  color: var(--blog-text-secondary);
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
