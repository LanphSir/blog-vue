<template>
  <el-card>
    <el-alert type="info" :closable="false" class="tip">
      “首页”由系统固定显示在导航最前，无需配置；导航最多两级；删除父项会连带删除其子项。
    </el-alert>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增菜单</el-button>
    </div>

    <el-table :data="tree" stripe v-loading="loading" row-key="id" default-expand-all :tree-props="{ children: 'children' }">
      <el-table-column label="名称" min-width="180">
        <template #default="{ row }">
          <el-icon v-if="resolveIcon(row.icon)" class="cell-icon"><component :is="resolveIcon(row.icon)" /></el-icon>
          <span class="tree-name">{{ row.label }}</span>
          <el-tag v-if="row.type === 'category'" size="small" class="type-tag">栏目下拉</el-tag>
          <el-tag v-else-if="row.is_external" size="small" type="warning" class="type-tag">外链</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="path" label="路径/URL" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ row.path || '-' }}</template>
      </el-table-column>
      <el-table-column label="排序" width="110" align="center">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" class="inline-sort" @change="patch(row, { sort_order: row.sort_order })" />
        </template>
      </el-table-column>
      <el-table-column label="显示" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.visible" @change="patch(row, { visible: row.visible })" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑菜单' : '新增菜单'" width="520px" :close-on-click-modal="false" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="菜单文字" prop="label">
          <el-input v-model="form.label" placeholder="如：文章" maxlength="50" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.kind">
            <el-radio value="link">内部链接</el-radio>
            <el-radio value="external">外部链接</el-radio>
            <el-radio value="category">栏目下拉</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.kind !== 'category'" :label="form.kind === 'external' ? 'URL' : '路径'" prop="path">
          <el-input v-model="form.path" :placeholder="form.kind === 'external' ? 'https://example.com' : '以 / 开头，如 /posts'" />
        </el-form-item>
        <el-form-item label="上级菜单">
          <el-select v-model="form.parent_id" placeholder="无（顶级导航）" clearable style="width: 100%">
            <el-option
              v-for="root in topOptions"
              :key="root.id"
              :label="root.label"
              :value="root.id"
              :disabled="root.id === form.id || root.type === 'category'"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="图标">
          <el-popover placement="bottom-start" :width="340" trigger="click">
            <template #reference>
              <el-button>
                <el-icon v-if="resolveIcon(form.icon)" class="cell-icon"><component :is="resolveIcon(form.icon)" /></el-icon>
                {{ form.icon || '选择图标' }}
              </el-button>
            </template>
            <div class="icon-grid">
              <button
                v-for="name in ICON_NAMES"
                :key="name"
                class="icon-cell"
                :class="{ selected: form.icon === name }"
                :title="name"
                @click="form.icon = form.icon === name ? null : name"
              >
                <el-icon><component :is="NAV_ICONS[name]" /></el-icon>
              </button>
            </div>
          </el-popover>
          <el-button v-if="form.icon" link type="danger" size="small" @click="form.icon = null">清除</el-button>
        </el-form-item>
        <el-form-item label="显示">
          <el-switch v-model="form.visible" />
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
/* 导航菜单管理：树形展示，最多两级（后端兜底校验）。
 * 前端把平铺列表合成两级树；类型分 内部链接/外部链接/栏目下拉，
 * 其中栏目下拉（category）必须顶级且不填 path/父级。
 * 删除父项会连带删除子项，删除前会提示。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminCreateMenu, adminDeleteMenu, adminGetMenus, adminUpdateMenu } from '@/api/site'
import { ICON_NAMES, NAV_ICONS, resolveIcon } from '@/utils/navIcons'

const flat = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const emptyForm = () => ({ id: null, label: '', kind: 'link', path: '', icon: null, parent_id: null, sort_order: 0, visible: true })
const form = ref(emptyForm())
const formRef = ref(null)
const rules = {
  label: [{ required: true, whitespace: true, message: '请填写菜单文字', trigger: 'blur' }],
  // 栏目下拉类型时该表单项被 v-if 隐藏，不参与校验
  path: [{ required: true, whitespace: true, message: '请输入链接地址', trigger: 'blur' }],
}

const tree = computed(() => {
  const tops = flat.value.filter((m) => !m.parent_id)
  return tops.map((top) => ({ ...top, children: flat.value.filter((m) => m.parent_id === top.id) }))
})
const topOptions = computed(() => flat.value.filter((m) => !m.parent_id))

async function load() {
  loading.value = true
  try {
    const res = await adminGetMenus()
    flat.value = res.data
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    form.value = {
      id: row.id,
      label: row.label,
      kind: row.type === 'category' ? 'category' : row.is_external ? 'external' : 'link',
      path: row.path || '',
      icon: row.icon || null,
      parent_id: row.parent_id || null,
      sort_order: row.sort_order ?? 0,
      visible: row.visible ?? true,
    }
  } else {
    form.value = emptyForm()
    form.value.sort_order = flat.value.filter((m) => !m.parent_id).length
  }
  dialogVisible.value = true
}

function buildPayload() {
  const kind = form.value.kind
  return {
    label: form.value.label.trim(),
    type: kind === 'category' ? 'category' : 'link',
    is_external: kind === 'external',
    path: kind === 'category' ? null : form.value.path.trim() || null,
    icon: form.value.icon || null,
    parent_id: kind === 'category' ? null : form.value.parent_id || null,
    sort_order: form.value.sort_order || 0,
    visible: form.value.visible,
  }
}

function validate() {
  const f = form.value
  if (!f.label.trim()) return '请填写菜单文字'
  if (f.kind === 'category') return null
  const path = f.path.trim()
  if (!path) return f.kind === 'external' ? '请填写外链 URL' : '请填写站内路径'
  if (f.kind === 'external' && !/^https?:\/\//.test(path)) return '外链必须以 http(s):// 开头'
  if (f.kind === 'link' && !path.startsWith('/')) return '站内路径必须以 / 开头'
  return null
}

async function handleSave() {
  // 必填校验交给 el-form 规则（label 红星 + 表下红字）；formRef 意外缺失时放行，后端 422 兜底
  if (formRef.value && !(await formRef.value.validate().catch(() => false))) return
  const error = validate()
  if (error) {
    ElMessage.warning(error)
    return
  }
  saving.value = true
  try {
    const payload = buildPayload()
    if (form.value.id) {
      // 排序只在行内即改即存，编辑弹窗不回写
      delete payload.sort_order
      await adminUpdateMenu(form.value.id, payload)
    } else {
      await adminCreateMenu(payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } catch {
    /* 错误提示已由拦截器处理 */
  } finally {
    saving.value = false
  }
}

async function patch(row, data) {
  try {
    await adminUpdateMenu(row.id, data)
  } catch {
    load()
  }
}

async function handleDelete(row) {
  const hasChildren = flat.value.some((m) => m.parent_id === row.id)
  try {
    await ElMessageBox.confirm(
      hasChildren ? `删除「${row.label}」将连带删除其子菜单，确认？` : `确认删除菜单「${row.label}」？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await adminDeleteMenu(row.id)
    ElMessage.success('已删除')
  } catch {
    /* 拦截器已提示 */
  }
  load()
}

onMounted(load)
</script>

<style scoped>
.tip {
  margin-bottom: 14px;
}

.tree-name {
  font-weight: 600;
}

.cell-icon {
  margin-right: 5px;
  vertical-align: -2px;
}

.type-tag {
  margin-left: 8px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.icon-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  font-size: 17px;
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.icon-cell:hover {
  background: var(--el-fill-color-light);
}

.icon-cell.selected {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
</style>
