<template>
  <el-card>
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增友链</el-button>
    </div>

    <el-table :data="links" stripe v-loading="loading">
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
      <el-table-column prop="sort_order" label="排序" width="70" align="center" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑友链' : '新增友链'" width="520px">
      <el-form label-width="80px" :model="form">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="友链名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="地址" required>
          <el-input v-model="form.url" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="255" placeholder="选填，显示在前台卡片" />
        </el-form-item>
        <el-form-item label="图标">
          <div class="icon-field">
            <el-avatar v-if="form.icon" :src="form.icon" :size="48" shape="square" class="icon-preview" />
            <el-upload :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="handleIcon">
              <el-button :loading="uploading" type="primary" plain>{{ form.icon ? '更换图标' : '上传图标' }}</el-button>
            </el-upload>
            <el-button v-if="form.icon" link type="danger" @click="form.icon = null">移除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" />
          <span class="hint">数字越小越靠前</span>
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
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  adminCreateFriend,
  adminDeleteFriend,
  adminUpdateFriend,
  getFriends,
} from '@/api/site'
import { uploadImage } from '@/api/upload'

const links = ref([])
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const emptyForm = () => ({ id: null, name: '', url: '', description: '', icon: null, sort_order: 0 })
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await getFriends()
    links.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = emptyForm()
  dialogVisible.value = true
}

function openEdit(row) {
  form.value = { ...emptyForm(), ...row, description: row.description || '', icon: row.icon || null }
  dialogVisible.value = true
}

async function handleIcon(file) {
  const raw = file.raw || file
  if (!raw) return
  uploading.value = true
  try {
    const res = await uploadImage(raw)
    form.value.icon = res.data
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

async function handleSave() {
  const name = (form.value.name || '').trim()
  const url = (form.value.url || '').trim()
  if (!name) return ElMessage.warning('请填写名称')
  if (!/^https?:\/\//.test(url)) return ElMessage.warning('地址需以 http:// 或 https:// 开头')
  const payload = {
    name,
    url,
    description: (form.value.description || '').trim() || null,
    icon: form.value.icon || null,
    sort_order: form.value.sort_order || 0,
  }
  saving.value = true
  try {
    if (form.value.id) {
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
.toolbar {
  margin-bottom: 16px;
}

.link {
  color: var(--blog-primary);
}

.no-icon {
  color: var(--blog-text-secondary);
}

.icon-field {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-preview {
  border: 1px solid var(--blog-border);
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--blog-text-secondary);
}
</style>
