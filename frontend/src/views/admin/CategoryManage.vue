<template>
  <el-card>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增分类</el-button>
    </div>

    <BatchBar :count="selected.length" :busy="batchBusy" @clear="clearSelection">
      <el-button size="small" type="primary" plain :disabled="batchBusy" @click="batchToggle(true)">批量显示</el-button>
      <el-button size="small" type="info" plain :disabled="batchBusy" @click="batchToggle(false)">批量隐藏</el-button>
    </BatchBar>

    <el-table ref="tableRef" :data="tree" stripe v-loading="loading" row-key="id" default-expand-all :tree-props="{ children: 'children' }" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="46" />
      <el-table-column prop="name" label="名称" min-width="180">
        <template #default="{ row }">
          <span class="tree-name" :style="row.color ? { color: row.color } : {}">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="slug" label="Slug" min-width="140" />
      <el-table-column prop="post_count" label="文章数" width="90" />
      <el-table-column label="排序" width="110" align="center">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" class="inline-sort" @change="updateSort(row)" />
        </template>
      </el-table-column>
      <el-table-column label="显示" width="80" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.visible" @change="updateVisible(row)" />
        </template>
      </el-table-column>
      <el-table-column label="颜色" width="80" align="center">
        <template #default="{ row }">
          <span v-if="row.color" class="color-dot" :style="{ background: row.color }" />
          <span v-else class="color-none">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑分类' : '新增分类'" width="480px" :close-on-click-modal="false" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="分类名称" />
        </el-form-item>
        <el-form-item label="Slug" prop="slug">
          <el-input v-model="form.slug" placeholder="url 别名" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-select v-model="form.parent_id" placeholder="无（顶级栏目）" clearable style="width: 100%">
            <el-option v-for="root in rootCategories" :key="root.id" :label="root.name" :value="root.id" :disabled="root.id === form.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" :predefine="colorPresets" />
          <el-button link type="danger" size="small" @click="form.color = null">清除</el-button>
        </el-form-item>
        <el-form-item label="首页显示">
          <el-switch v-model="form.visible" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存并继续</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
/* 分类管理：树形表 + 新增/编辑弹窗。分类可设父级（最多两级，由后端校验）。
 * 编辑时禁选自己作父级；行内改排序/可见性即调接口。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BatchBar from '@/components/admin/BatchBar.vue'
import { runBatch, reportBatch } from '@/utils/batch'
import {
  adminCreateCategory,
  adminDeleteCategory,
  adminUpdateCategory,
  getCategoryTree,
} from '@/api/categories'

const colorPresets = ['#2563EB', '#16A34A', '#DB2777', '#EA580C', '#7C3AED', '#0EA5E9', '#64748B', '#B45309']

const tree = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = ref({ id: null, name: '', slug: '', color: null, parent_id: null, sort_order: 0, visible: true })

const rootCategories = computed(() => tree.value)

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
      (id) => adminUpdateCategory(id, { visible: value }),
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
    const res = await getCategoryTree()
    tree.value = res.data
  } finally {
    loading.value = false
  }
}

const formRef = ref(null)
const rules = {
  name: [{ required: true, whitespace: true, message: '请输入名称', trigger: 'blur' }],
  slug: [{ required: true, whitespace: true, message: '请输入 Slug', trigger: 'blur' }],
}

function openDialog(row) {
  if (row) {
    form.value = {
      id: row.id,
      name: row.name,
      slug: row.slug,
      color: row.color ?? null,
      parent_id: row.parent_id ?? null,
      sort_order: row.sort_order ?? 0,
      visible: row.visible ?? true,
    }
  } else {
    form.value = { id: null, name: '', slug: '', color: null, parent_id: null, sort_order: tree.value.length, visible: true }
  }
  dialogVisible.value = true
}

function buildPayload() {
  return {
    name: form.value.name,
    slug: form.value.slug,
    color: form.value.color || null,
    parent_id: form.value.parent_id || null,
    sort_order: form.value.sort_order || 0,
    visible: form.value.visible,
  }
}

async function handleSave() {
  // 必填校验交给 el-form 规则（label 红星 + 表下红字）；formRef 意外缺失时放行，后端 422 兜底
  if (formRef.value && !(await formRef.value.validate().catch(() => false))) return
  saving.value = true
  try {
    if (form.value.id) {
      // 排序只在行内即改即存，编辑弹窗不回写，避免覆盖最新的行内修改
      const partial = buildPayload()
      delete partial.sort_order
      await adminUpdateCategory(form.value.id, partial)
    } else {
      await adminCreateCategory(buildPayload())
    }
    ElMessage.success('已保存')
    if (form.value.id) {
      dialogVisible.value = false
    } else {
      form.value = { id: null, name: '', slug: '', color: null, parent_id: null, sort_order: tree.value.length, visible: true }
      formRef.value?.clearValidate()
    }
    load()
  } catch {
    /* 错误提示已由拦截器处理 */
  } finally {
    saving.value = false
  }
}

async function updateVisible(row) {
  await adminUpdateCategory(row.id, { visible: row.visible })
}

async function updateSort(row) {
  try {
    await adminUpdateCategory(row.id, { sort_order: row.sort_order })
  } catch {
    load()
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除分类「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminDeleteCategory(row.id)
    ElMessage.success('已删除')
  } catch {
    /* 删除被保护时，错误提示已由拦截器处理 */
  }
  load()
}

onMounted(load)
</script>

<style scoped>
.tree-name {
  font-weight: 600;
}

.color-dot {
  display: inline-block;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  vertical-align: middle;
}

.color-none {
  color: var(--blog-text-secondary);
}
</style>