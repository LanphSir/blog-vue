<template>
  <el-card>
    <el-button type="primary" @click="openDialog()" class="add-btn">新增分类</el-button>

    <el-table :data="tree" stripe v-loading="loading" row-key="id" default-expand-all :tree-props="{ children: 'children' }">
      <el-table-column prop="name" label="名称" min-width="180">
        <template #default="{ row }">
          <span class="tree-name" :style="row.color ? { color: row.color } : {}">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="slug" label="Slug" min-width="140" />
      <el-table-column prop="post_count" label="文章数" width="90" />
      <el-table-column label="排序" width="80">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" @change="updateSort(row)" />
        </template>
      </el-table-column>
      <el-table-column label="显示" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.visible" @change="updateVisible(row)" />
        </template>
      </el-table-column>
      <el-table-column label="颜色" width="80">
        <template #default="{ row }">
          <span v-if="row.color" class="color-dot" :style="{ background: row.color }" />
          <span v-else class="color-none">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑分类' : '新增分类'" width="480px" :close-on-click-modal="false">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="分类名称" />
        </el-form-item>
        <el-form-item label="Slug">
          <el-input v-model="form.slug" placeholder="url 别名" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-select v-model="form.parent_id" placeholder="无（顶级栏目）" clearable style="width: 100%">
            <el-option v-for="root in rootCategories" :key="root.id" :label="root.name" :value="root.id" :disabled="root.id === form.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
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
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

async function load() {
  loading.value = true
  try {
    const res = await getCategoryTree()
    tree.value = res.data
  } finally {
    loading.value = false
  }
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
  if (!form.value.name || !form.value.slug) {
    ElMessage.warning('请填写名称和 Slug')
    return
  }
  saving.value = true
  try {
    if (form.value.id) {
      await adminUpdateCategory(form.value.id, buildPayload())
    } else {
      await adminCreateCategory(buildPayload())
    }
    ElMessage.success('已保存')
    if (form.value.id) {
      dialogVisible.value = false
    } else {
      form.value = { id: null, name: '', slug: '', color: null, parent_id: null, sort_order: tree.value.length, visible: true }
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
  await adminUpdateCategory(row.id, { sort_order: row.sort_order })
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
.add-btn {
  margin-bottom: 16px;
}

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