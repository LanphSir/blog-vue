<template>
  <el-card>
    <div class="page-toolbar">
      <el-radio-group v-model="trashMode" size="default" @change="onModeChange">
        <el-radio-button :value="false">评论列表</el-radio-button>
        <el-radio-button :value="true">回收站</el-radio-button>
      </el-radio-group>
      <el-select v-if="!trashMode" v-model="status" placeholder="状态" clearable style="width: 130px" @change="load(1)">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已隐藏" value="hidden" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索昵称/内容" clearable style="width: 220px" @clear="load(1)" @keyup.enter="load(1)" />
      <el-button type="primary" @click="load(1)">查询</el-button>
    </div>

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <template v-if="!trashMode">
        <el-button size="small" type="success" plain :disabled="batchBusy" @click="runBatchAction('通过', adminApproveComment)">批量通过</el-button>
        <el-button size="small" type="warning" plain :disabled="batchBusy" @click="runBatchAction('隐藏', adminHideComment)">批量隐藏</el-button>
        <el-button size="small" type="danger" plain :disabled="batchBusy" @click="confirmBatchDelete">批量删除</el-button>
      </template>
      <template v-else>
        <el-button size="small" type="primary" plain :disabled="batchBusy" @click="runBatchAction('恢复', adminRestoreComment)">批量恢复</el-button>
      </template>
    </BatchBar>

    <el-table ref="tableRef" :data="comments" stripe v-loading="loading" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
      <el-table-column prop="nickname" label="昵称" width="130" show-overflow-tooltip>
        <template #default="{ row }">
          <el-tag v-if="row.is_pinned" size="small" type="danger" effect="light" class="pin-dot">顶</el-tag>
          {{ row.nickname }}
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="220" show-overflow-tooltip />
      <el-table-column label="所属文章" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <a class="post-link" :href="`/post/${row.post_slug}`" target="_blank" rel="noopener">
            {{ row.post_title || `文章 #${row.post_id}` }}
          </a>
        </template>
      </el-table-column>
      <el-table-column v-if="!trashMode" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="STATUS_TAG[row.status]" size="small">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <!-- 公开显示开关（与分类/标签等列表的显示列同款 el-switch）：开=已通过公开，关=隐藏保留数据 -->
      <el-table-column v-if="!trashMode" label="显示" width="70" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 'approved'"
            :disabled="row.is_deleted"
            @update:model-value="(v) => toggleVisible(row, v)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="ip" label="IP" width="130" show-overflow-tooltip />
      <el-table-column label="时间" width="150">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column :label="'操作'" :width="trashMode ? 90 : 190" align="center" class-name="ops-col" fixed="right">
        <template #default="{ row }">
          <template v-if="trashMode">
            <el-button link type="primary" @click="doAction(row, '恢复', adminRestoreComment)">恢复</el-button>
          </template>
          <template v-else>
            <el-button link type="primary" @click="openDetail(row)">查看</el-button>
            <el-button
              v-if="!row.parent_id"
              link
              :type="row.is_pinned ? 'info' : 'primary'"
              @click="doAction(row, row.is_pinned ? '取消置顶' : '置顶', row.is_pinned ? adminUnpinComment : adminPinComment)"
            >
              {{ row.is_pinned ? '取消置顶' : '置顶' }}
            </el-button>
            <el-button link type="danger" @click="confirmDelete(row)">删除</el-button>
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

    <!-- 完整信息弹窗：邮箱/UA 等隐私字段只在点开单条时随详情接口取回 -->
    <el-dialog v-model="detailVisible" title="评论详情" width="520px">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="昵称">{{ detail.nickname }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detail.email || '—' }}</el-descriptions-item>
        <el-descriptions-item label="IP">{{ detail.ip || '—' }}</el-descriptions-item>
        <el-descriptions-item label="User-Agent">
          <span class="ua-text">{{ detail.user_agent || '—' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">{{ STATUS_LABEL[detail.status] }}</el-descriptions-item>
        <el-descriptions-item v-if="detail.reply_to_nickname" label="回复对象">
          @{{ detail.reply_to_nickname }}
        </el-descriptions-item>
        <el-descriptions-item label="所属文章">
          <a v-if="detail.post_slug" class="post-link" :href="`/post/${detail.post_slug}`" target="_blank" rel="noopener">
            {{ detail.post_title || `文章 #${detail.post_id}` }}
          </a>
          <span v-else>文章 #{{ detail.post_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="评论时间">{{ fmt(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div class="detail-content">{{ detail.content }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-card>
</template>

<script setup>
/* 评论管理：列表/回收站共用接口（deleted 参数区分）。软删除后若有存活回复，
 * 前台会以「该评论已被删除」 placeholder 占位显示；恢复即回到原状态。
 * 批量操作逐条循环单条 API（runBatch 聚合汇报，见 utils/batch.js 约定）。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  adminApproveComment,
  adminDeleteComment,
  adminGetCommentDetail,
  adminGetComments,
  adminHideComment,
  adminPinComment,
  adminRestoreComment,
  adminUnpinComment,
} from '@/api/comments'
import { runBatch, reportBatch } from '@/utils/batch'
import BatchBar from '@/components/admin/BatchBar.vue'

const STATUS_LABEL = { pending: '待审核', approved: '已通过', hidden: '已隐藏' }
const STATUS_TAG = { pending: 'warning', approved: 'success', hidden: 'info' }

const comments = ref([])
const loading = ref(false)
const trashMode = ref(false)
const status = ref('')
const keyword = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 20

const selected = ref([])
const batchBusy = ref(false)
const tableRef = ref(null)

// 详情弹窗：邮箱/IP/UA 随单条详情接口按需取回（列表接口不整页暴露）
const detailVisible = ref(false)
const detail = ref(null)

async function openDetail(row) {
  const req = await adminGetCommentDetail(row.id)
  detail.value = req.data
  detailVisible.value = true
}

// 显示开关：开=approved 公开，关=hidden（数据保留可再开）；交互对齐分类/标签列表
async function toggleVisible(row, visible) {
  await doAction(row, visible ? '通过' : '隐藏', visible ? adminApproveComment : adminHideComment)
}

function fmt(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '-'
}

function onModeChange() {
  status.value = ''
  load(1)
}

function onSelectionChange(rows) {
  selected.value = rows
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selected.value = []
}

async function load(p = page.value) {
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize, deleted: trashMode.value }
    if (!trashMode.value && status.value) params.status = status.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const res = await adminGetComments(params)
    comments.value = res.data.items
    total.value = res.data.total
    page.value = p
    // 通知布局刷新侧栏「待审」红点（处理完评论后立即更新）
    window.dispatchEvent(new Event('blog-comments-changed'))
  } finally {
    loading.value = false
  }
}

async function doAction(row, label, fn) {
  try {
    await fn(row.id)
    ElMessage.success(`已${label}`)
  } finally {
    await load()
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${row.nickname}」的评论？被删评论若有回复会以「该评论已被删除」占位显示。`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await doAction(row, '删除', adminDeleteComment)
}

async function runBatchAction(label, fn) {
  const rows = [...selected.value]
  if (!rows.length) return
  batchBusy.value = true
  try {
    const result = await runBatch(
      rows.map((r) => r.id),
      fn,
    )
    reportBatch(result, label)
    clearSelection()
    await load()
  } finally {
    batchBusy.value = false
  }
}

async function confirmBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.value.length} 条评论？`, '批量删除', { type: 'warning' })
  } catch {
    return
  }
  await runBatchAction('批量删除', adminDeleteComment)
}

onMounted(() => load(1))
</script>

<style scoped>
.post-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
