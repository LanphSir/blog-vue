<template>
  <el-card>
    <el-alert type="info" :closable="false" class="tip">
      横幅公告显示在站点顶部（同类型按排序取第一条）；弹窗公告对未读用户弹出一次；单页公告通过
      “导航菜单”添加入口（路径填 /notice/公告ID）。内容变更会自动升版本，已关闭的用户会重新收到。
    </el-alert>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增公告</el-button>
    </div>

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <el-button size="small" type="primary" plain :disabled="batchBusy" @click="batchToggle(true)">批量启用</el-button>
      <el-button size="small" type="info" plain :disabled="batchBusy" @click="batchToggle(false)">批量停用</el-button>
    </BatchBar>

    <el-table ref="tableRef" :data="notices" stripe v-loading="loading" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="TYPE_TAG[row.type]" size="small">{{ TYPE_LABEL[row.type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="70" />
      <el-table-column label="启用" width="80" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="patch(row, { enabled: row.enabled })" />
        </template>
      </el-table-column>
      <el-table-column label="排序" width="110" align="center">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" class="inline-sort" @change="patch(row, { sort_order: row.sort_order })" />
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="150">
        <template #default="{ row }">{{ fmt(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190" align="center" class-name="ops-col" fixed="right">
        <template #default="{ row }">
          <el-tooltip :content="row.enabled ? '前台查看' : '启用后可查看'" placement="top">
            <span>
              <el-button link type="primary" :disabled="!row.enabled" @click="viewNotice(row)">查看</el-button>
            </span>
          </el-tooltip>
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑公告' : '新增公告'" :width="form.type === 'banner' ? '560px' : '860px'" :close-on-click-modal="false" top="6vh" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio-button value="banner">小 · 横幅</el-radio-button>
            <el-radio-button value="dialog">中 · 弹窗</el-radio-button>
            <el-radio-button value="page">大 · 单页</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="公告标题" maxlength="200" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-if="form.type === 'banner'" v-model="form.content" type="textarea" :rows="3" placeholder="横幅公告为纯文本，建议一句话" />
          <MarkdownEditor v-else v-model="form.content" class="notice-editor" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
/* 公告管理：三种类型（横幅/弹窗/单页）。横幅纯文本、弹窗/单页走 MarkdownEditor。
 * 内容变更后端自动升版本，已关闭的公告用户会重新看到（dismiss 记忆按版本比对）。
 * 单页公告入口需用户手动在导航菜单里加 /notice/{id} 链接，这里提供「复制链接」。
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BatchBar from '@/components/admin/BatchBar.vue'
import { runBatch, reportBatch } from '@/utils/batch'
import { adminCreateNotice, adminDeleteNotice, adminGetNotices, adminUpdateNotice } from '@/api/site'

const router = useRouter()
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const TYPE_LABEL = { banner: '横幅', dialog: '弹窗', page: '单页' }
const TYPE_TAG = { banner: 'info', dialog: 'warning', page: 'primary' }

const notices = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const emptyForm = () => ({ id: null, title: '', content: '', type: 'banner' })
const form = ref(emptyForm())
const formRef = ref(null)
const rules = {
  title: [{ required: true, whitespace: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, whitespace: true, message: '请输入内容', trigger: 'blur' }],
}

const selected = ref([])
const batchBusy = ref(false)
const tableRef = ref(null)

function onSelectionChange(rows) {
  selected.value = rows
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selected.value = []
}

async function batchToggle(value) {
  const rows = [...selected.value]
  if (!rows.length) return
  batchBusy.value = true
  try {
    const result = await runBatch(
      rows.map((r) => r.id),
      (id) => adminUpdateNotice(id, { enabled: value }),
    )
    reportBatch(result, value ? '批量启用' : '批量停用')
    clearSelection()
    await load()
  } finally {
    batchBusy.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await adminGetNotices()
    notices.value = res.data
  } finally {
    loading.value = false
  }
}

function fmt(raw) {
  return raw ? String(raw).replace('T', ' ').slice(0, 16) : '-'
}

function openDialog(row) {
  form.value = row
    ? { id: row.id, title: row.title, content: row.content || '', type: row.type }
    : emptyForm()
  dialogVisible.value = true
}

async function handleSave() {
  // 必填校验交给 el-form 规则（label 红星 + 表下红字）；formRef 意外缺失时放行，后端 422 兜底
  if (formRef.value && !(await formRef.value.validate().catch(() => false))) return
  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      content: form.value.content,
      type: form.value.type,
    }
    if (form.value.id) {
      await adminUpdateNotice(form.value.id, payload)
    } else {
      await adminCreateNotice(payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } catch {
    /* Error message is handled by the axios interceptor */
  } finally {
    saving.value = false
  }
}

async function patch(row, data) {
  try {
    await adminUpdateNotice(row.id, data)
  } catch {
    load()
  }
}

function noticeHref(row) {
  return router.resolve({ name: 'notice', params: { id: row.id } }).href
}

function viewNotice(row) {
  window.open(noticeHref(row), '_blank')
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除公告「${row.title}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminDeleteNotice(row.id)
    ElMessage.success('已删除')
  } catch {
    /* handled */
  }
  load()
}

onMounted(load)
</script>

<style scoped>
.tip {
  margin-bottom: 14px;
}
</style>
