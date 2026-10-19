<template>
  <el-card>
    <div class="page-toolbar">
      <el-button type="primary" @click="openCreate">新增友链</el-button>
    </div>

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <el-button size="small" type="primary" plain :disabled="batchBusy" @click="batchToggle(true)">批量显示</el-button>
      <el-button size="small" type="info" plain :disabled="batchBusy" @click="batchToggle(false)">批量隐藏</el-button>
    </BatchBar>

    <el-table ref="tableRef" :data="links" stripe v-loading="loading" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
      <el-table-column label="图标" width="72" align="center">
        <template #default="{ row }">
          <el-avatar v-if="row.icon" :src="row.icon" :size="32" shape="square" />
          <span v-else class="no-icon">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="url" label="地址" min-width="220">
        <template #default="{ row }">
          <a :href="row.url" target="_blank" rel="noopener" class="link">{{ row.url }}</a>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
      <el-table-column label="显示" width="80" align="center">
        <template #default="{ row }">
          <el-switch :model-value="row.visible" @change="(v) => toggleVisible(row, v)" />
        </template>
      </el-table-column>
      <el-table-column label="排序" width="110" align="center">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" class="inline-sort" @change="updateSort(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑友链' : '新增友链'" width="520px" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" label-width="80px" :model="form" :rules="rules">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="友链名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="地址" prop="url">
          <el-input v-model="form.url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="255" placeholder="选填，显示在前台卡片" />
        </el-form-item>
        <el-form-item label="图标">
          <MediaPicker v-model="form.icon" tip="方形小图效果最佳" :preview-width="56" :preview-height="56" />
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
/* 友链管理：列表 + 新增/编辑弹窗。图片经 MediaPicker；地址强制 http(s):// 开头。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BatchBar from '@/components/admin/BatchBar.vue'
import { runBatch, reportBatch } from '@/utils/batch'
import {
  adminCreateFriend,
  adminDeleteFriend,
  adminGetFriends,
  adminUpdateFriend,
} from '@/api/site'
import MediaPicker from '@/components/admin/MediaPicker.vue'

const links = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const emptyForm = () => ({ id: null, name: '', url: '', description: '', icon: null, visible: true, sort_order: 0 })
const form = ref(emptyForm())
const formRef = ref(null)
const rules = {
  name: [{ required: true, whitespace: true, message: '请输入名称', trigger: 'blur' }],
  url: [
    { required: true, whitespace: true, message: '请输入地址', trigger: 'blur' },
    { pattern: /^https?:\/\//, message: '地址需以 http:// 或 https:// 开头', trigger: 'blur' },
  ],
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
      (id) => adminUpdateFriend(id, { visible: value }),
    )
    reportBatch(result, value ? '批量显示' : '批量隐藏')
    clearSelection()
    await load()
  } finally {
    batchBusy.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await adminGetFriends()
    links.value = res.data
  } finally {
    loading.value = false
  }
}

async function updateSort(row) {
  try {
    await adminUpdateFriend(row.id, { sort_order: row.sort_order })
  } catch {
    load()
  }
}

async function toggleVisible(row, value) {
  await adminUpdateFriend(row.id, { visible: value })
  row.visible = value
  ElMessage.success(value ? `「${row.name}」已显示` : `「${row.name}」已隐藏`)
}

function openCreate() {
  form.value = { ...emptyForm(), sort_order: links.value.length }
  dialogVisible.value = true
}

function openEdit(row) {
  form.value = { ...emptyForm(), ...row, description: row.description || '', icon: row.icon || null }
  dialogVisible.value = true
}

async function handleSave() {
  // 必填/格式校验交给 el-form 规则（label 红星 + 表下红字）；formRef 意外缺失时放行，后端 422 兜底
  if (formRef.value && !(await formRef.value.validate().catch(() => false))) return
  const name = (form.value.name || '').trim()
  const url = (form.value.url || '').trim()
  const payload = {
    name,
    url,
    description: (form.value.description || '').trim() || null,
    icon: form.value.icon || null,
    visible: form.value.visible,
    sort_order: form.value.sort_order || 0,
  }
  saving.value = true
  try {
    if (form.value.id) {
      // 排序只在行内即改即存，编辑弹窗不回写
      delete payload.sort_order
      await adminUpdateFriend(form.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await adminCreateFriend(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
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

.link {
  color: var(--blog-primary);
}

.no-icon {
  color: var(--blog-text-secondary);
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--blog-text-secondary);
}
</style>
