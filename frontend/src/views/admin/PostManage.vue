<template>
  <el-card>
    <div class="page-toolbar">
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
      <el-button v-if="!recycleMode" type="primary" @click="goCreate">新建文章</el-button>
      <el-button v-else type="danger" plain @click="emptyRecycle">清空回收站</el-button>
    </div>

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <template v-if="!recycleMode">
        <el-button size="small" type="primary" plain :disabled="batchBusy" @click="openMoveDialog">移动分类</el-button>
        <el-button size="small" type="success" plain :disabled="batchBusy" @click="batchStatus('published')">批量发布</el-button>
        <el-button size="small" plain :disabled="batchBusy" @click="batchStatus('draft')">转为草稿</el-button>
        <el-button size="small" type="danger" plain :disabled="batchBusy" @click="batchDelete">移入回收站</el-button>
      </template>
      <template v-else>
        <el-button size="small" type="primary" plain :disabled="batchBusy" @click="batchRestore">批量恢复</el-button>
        <el-button size="small" type="danger" plain :disabled="batchBusy" @click="batchPermanent">彻底删除</el-button>
      </template>
    </BatchBar>

    <el-table ref="tableRef" :data="posts" stripe v-loading="loading" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
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
        <el-table-column label="权重" width="110" align="center">
          <template #default="{ row }">
            <el-input-number :model-value="row.sort_weight" :min="0" size="small" controls-position="right" class="inline-sort" @change="changeWeight(row, $event)" />
          </template>
        </el-table-column>
      </template>

      <el-table-column prop="view_count" label="阅读" width="90" />
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ new Date(row.updated_at).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="recycleMode ? 150 : 190" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="recycleMode">
            <el-button link type="primary" @click="handleRestore(row)">恢复</el-button>
            <el-button link type="danger" @click="handlePermanentDelete(row)">彻底删除</el-button>
          </template>
          <template v-else>
            <el-tooltip :content="row.status === 'published' ? '前台查看' : '发布后可查看'" placement="top">
              <span>
                <el-button link type="primary" :disabled="row.status !== 'published'" @click="viewPost(row)">查看</el-button>
              </span>
            </el-tooltip>
            <el-button link type="primary" @click="goEdit(row.id)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="moveVisible" title="移动分类" width="380px">
      <el-tree-select
        v-model="moveTarget"
        :data="categoryOptions"
        node-key="id"
        :props="{ label: 'name', children: 'children' }"
        check-strictly
        :render-after-expand="false"
        placeholder="选择目标分类"
        style="width: 100%"
      />
      <template #footer>
        <el-button @click="moveVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchBusy" :disabled="!moveTarget" @click="batchMove">
          移动 {{ selected.length }} 篇
        </el-button>
      </template>
    </el-dialog>

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
/* 文章管理 + 回收站：列表/回收站用同一接口的 deleted 参数区分。
 * 删除 = 软删进回收站（deleted=true 列出）；恢复 = restore；彻底删除 = permanent。
 * 清空回收站会逐条永久删除（不可恢复）。行内置顶/推荐/发布/权重改动即时调接口。
 */
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BatchBar from '@/components/admin/BatchBar.vue'
import { runBatch, reportBatch } from '@/utils/batch'
import {
  adminDeletePost,
  adminGetPosts,
  adminPermanentDeletePost,
  adminRestorePost,
  adminUpdatePost,
} from '@/api/posts'
import { getCategoryTree } from '@/api/categories'

const router = useRouter()
const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const status = ref('')
const loading = ref(false)
const recycleMode = ref(false)
const tableRef = ref(null)
const selected = ref([])
const batchBusy = ref(false)
const moveVisible = ref(false)
const moveTarget = ref(null)
const categoryOptions = ref([])

function onSelectionChange(rows) {
  selected.value = rows
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selected.value = []
}

async function batchRun(label, confirm, fn) {
  const rows = [...selected.value]
  if (!rows.length) return
  if (confirm) {
    try {
      await ElMessageBox.confirm(confirm, '批量操作', { type: 'warning' })
    } catch {
      return
    }
  }
  batchBusy.value = true
  try {
    const result = await runBatch(rows.map((r) => r.id), fn)
    reportBatch(result, label)
    clearSelection()
    await load(page.value)
  } finally {
    batchBusy.value = false
  }
}

function batchStatus(next) {
  const text = next === 'published' ? '批量发布' : '批量转为草稿'
  const tips = {
    published: '草稿发布后 published_at 会自动补全。',
    draft: '转为草稿后文章从前台隐藏，随时可重新发布。',
  }
  return batchRun(text, `将选中的 ${selected.value.length} 篇文章${text.replace('批量', '')}？${tips[next]}`, (id) =>
    adminUpdatePost(id, { status: next }),
  )
}

function batchDelete() {
  return batchRun('已移入回收站', `确认将选中的 ${selected.value.length} 篇文章移入回收站？可随时恢复。`, (id) => adminDeletePost(id))
}

function batchRestore() {
  return batchRun('已恢复', `确认恢复选中的 ${selected.value.length} 篇文章？`, (id) => adminRestorePost(id))
}

function batchPermanent() {
  return batchRun(
    '已彻底删除',
    `确认彻底删除选中的 ${selected.value.length} 篇文章？该操作不可恢复！`,
    (id) => adminPermanentDeletePost(id),
  )
}

async function openMoveDialog() {
  if (!categoryOptions.value.length) {
    try {
      categoryOptions.value = (await getCategoryTree()).data
    } catch {
      return
    }
  }
  moveTarget.value = null
  moveVisible.value = true
}

async function batchMove() {
  if (!moveTarget.value) return
  const target = moveTarget.value
  const rows = [...selected.value]
  batchBusy.value = true
  try {
    const result = await runBatch(rows.map((r) => r.id), (id) => adminUpdatePost(id, { category_id: target }))
    reportBatch(result, '已移动分类')
    moveVisible.value = false
    clearSelection()
    await load(page.value)
  } finally {
    batchBusy.value = false
  }
}

 async function load(p = 1) {
  clearSelectionAfterLoad()
  loading.value = true
  page.value = p
  try {
    const params = { page: p, page_size: pageSize.value, deleted: recycleMode.value }
    if (keyword.value) params.keyword = keyword.value
    if (!recycleMode.value && status.value) params.status = status.value
    const res = await adminGetPosts(params)
    posts.value = res.data.items
    total.value = res.data.total
    nextTick(() => clearSelection())
  } finally {
    loading.value = false
  }
}

// el-table 在数据替换时会自动清空 selection-change，这里只同步本地状态；
// 若仍收到非空的 selection（切换回收站视图时），需手动清空。
function clearSelectionAfterLoad() {
  tableRef.value?.clearSelection()
  selected.value = []
}

function goCreate() {
  router.push({ name: 'admin-post-create' })
}

function viewPost(row) {
  const { href } = router.resolve({ name: 'post-detail', params: { slug: row.slug } })
  window.open(href, '_blank')
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

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>