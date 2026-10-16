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
        <el-radio-group v-model="recycleMode" @change="reload">
          <el-radio-button :value="false">媒体库</el-radio-button>
          <el-radio-button :value="true">回收站</el-radio-button>
        </el-radio-group>
        <el-upload v-if="!recycleMode" :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="handleUpload">
          <el-button type="primary" :loading="uploading">上传图片</el-button>
        </el-upload>
        <span v-if="!recycleMode" class="tip">文件按 年/月 归档，文件名自动加时间戳与内容哈希；站点名称等配置图片请使用 站点配置 页。</span>
        <span v-else class="tip">删除的图片保留在此，可恢复；彻底删除才会移除磁盘文件，被引用时需强制確認。</span>
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

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <template v-if="!recycleMode">
        <el-button size="small" type="danger" plain :disabled="batchBusy" @click="batchTrash">移入回收站</el-button>
      </template>
      <template v-else>
        <el-button size="small" type="primary" plain :disabled="batchBusy" @click="batchRestoreMedia">批量恢复</el-button>
        <el-button size="small" type="danger" plain :disabled="batchBusy" @click="batchPermanentMedia">彻底删除</el-button>
      </template>
    </BatchBar>

    <el-table ref="tableRef" :data="filtered" stripe v-loading="loading" row-key="id" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
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
      <el-table-column :label="recycleMode ? '删除时间' : '上传时间'" width="150">
        <template #default="{ row }">{{ fmtDate(recycleMode ? row.deleted_at : row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190" align="center" class-name="ops-col" fixed="right">
        <template #default="{ row }">
          <template v-if="recycleMode">
            <el-button link type="primary" @click="handleRestore(row)">恢复</el-button>
            <el-button link type="danger" @click="handlePermanent(row)">彻底删除</el-button>
          </template>
          <template v-else>
            <el-button link type="primary" @click="copyUrl(row)">复制链接</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
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
/* 媒体库：左侧目录树 + 右侧图片列表，附「回收站」视图（与文章管理同款交互）。
 * 删除=软删进回收站（文件保留、前台引用不失效）；「彻底删除」才物理删文件，
 * 后端 409 表示被引用，需二次确认走 force=true 强制删除；
 * 删除最后一页最后一条时回退一页，避免空页。上传用 el-upload 仅在此页做
 * 「图片入库」主入口，其余页面选图统一走 MediaPicker。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  adminDeleteMedia,
  adminListMedia,
  adminMediaFolders,
  adminPermanentDeleteMedia,
  adminRestoreMedia,
  uploadImage,
} from '@/api/upload'
import { buildFolderTree } from '@/utils/mediaTree'
import BatchBar from '@/components/admin/BatchBar.vue'
import { runBatch, reportBatch } from '@/utils/batch'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const uploading = ref(false)
const keyword = ref('')
const folders = ref([])
const currentDir = ref('')
const recycleMode = ref(false)
const tableRef = ref(null)
const selected = ref([])
const batchBusy = ref(false)

function onSelectionChange(rows) {
  selected.value = rows
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selected.value = []
}

async function batchTrash() {
  const rows = [...selected.value]
  try {
    await ElMessageBox.confirm(`确认将选中的 ${rows.length} 张图片移入回收站？前台已引用的图片不受影响。`, '移入回收站', { type: 'warning' })
  } catch {
    return
  }
  batchBusy.value = true
  try {
    reportBatch(await runBatch(rows.map((r) => r.id), (id) => adminDeleteMedia(id)), '已移入回收站')
    clearSelection()
    await Promise.all([load(page.value), loadFolders()])
  } finally {
    batchBusy.value = false
  }
}

async function batchRestoreMedia() {
  const rows = [...selected.value]
  batchBusy.value = true
  try {
    reportBatch(await runBatch(rows.map((r) => r.id), (id) => adminRestoreMedia(id)), '已恢复')
    clearSelection()
    await Promise.all([load(page.value), loadFolders()])
  } finally {
    batchBusy.value = false
  }
}

async function batchPermanentMedia() {
  const rows = [...selected.value]
  try {
    await ElMessageBox.confirm(`确认彻底删除 ${rows.length} 张图片？磁盘文件将被移除，不可恢复！若仍被引用将跳过并汇总。`, '危险操作', { type: 'error', confirmButtonText: '彻底删除', confirmButtonClass: 'el-button--danger' })
  } catch {
    return
  }
  batchBusy.value = true
  try {
    reportBatch(await runBatch(rows.map((r) => r.id), (id) => adminPermanentDeleteMedia(id)), '已彻底删除')
    clearSelection()
    await Promise.all([load(items.value.length === rows.length && page.value > 1 ? page.value - 1 : page.value), loadFolders()])
  } finally {
    batchBusy.value = false
  }
}


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
    const params = { page: toPage, page_size: pageSize, deleted: recycleMode.value }
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
      `将「${row.stored_name}」移入回收站？前台已引用的图片不受影响，可随时恢复。`,
      '移入回收站',
      { type: 'warning', confirmButtonText: '移入回收站', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await adminDeleteMedia(row.id)
    ElMessage.success('已移入回收站')
    await Promise.all([load(items.value.length === 1 && page.value > 1 ? page.value - 1 : page.value), loadFolders()])
  } catch {
    /* 拦截器已提示 */
  }
}

async function handleRestore(row) {
  try {
    await adminRestoreMedia(row.id)
    ElMessage.success('已恢复')
    await Promise.all([load(page.value), loadFolders()])
  } catch {
    /* 磁盘文件丢失等错误由拦截器提示 */
  }
}

async function handlePermanent(row) {
  try {
    await ElMessageBox.confirm(
      `彻底删除「${row.stored_name}」？磁盘文件将被移除，该操作不可恢复！`,
      '危险操作',
      { type: 'error', confirmButtonText: '彻底删除', confirmButtonClass: 'el-button--danger' },
    )
  } catch {
    return
  }
  try {
    await adminPermanentDeleteMedia(row.id)
    ElMessage.success('已彻底删除')
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
      await adminPermanentDeleteMedia(row.id, true)
      ElMessage.success('已强制删除')
      await Promise.all([load(items.value.length === 1 && page.value > 1 ? page.value - 1 : page.value), loadFolders()])
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
