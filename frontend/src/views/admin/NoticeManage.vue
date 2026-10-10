<template>
  <el-card>
    <el-alert type="info" :closable="false" class="tip">
      横幅公告显示在站点顶部（同类型按排序取第一条）；弹窗公告对未读用户弹出一次；单页公告通过
      “导航菜单”添加入口（路径填 /notice/公告ID）。内容变更会自动升版本，已关闭的用户会重新收到。
    </el-alert>
    <el-button type="primary" @click="openDialog()" class="add-btn">新增公告</el-button>

    <el-table :data="notices" stripe v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="TYPE_TAG[row.type]" size="small">{{ TYPE_LABEL[row.type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="70" />
      <el-table-column label="启用" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="patch(row, { enabled: row.enabled })" />
        </template>
      </el-table-column>
      <el-table-column label="排序" width="90">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" @change="patch(row, { sort_order: row.sort_order })" />
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="150">
        <template #default="{ row }">{{ fmt(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑公告' : '新增公告'" :width="form.type === 'banner' ? '560px' : '860px'" :close-on-click-modal="false" top="6vh">
      <el-form :model="form" label-width="70px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio-button value="banner">小 · 横幅</el-radio-button>
            <el-radio-button value="dialog">中 · 弹窗</el-radio-button>
            <el-radio-button value="page">大 · 单页</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="公告标题" maxlength="200" />
        </el-form-item>
        <el-form-item label="内容">
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
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminCreateNotice, adminDeleteNotice, adminGetNotices, adminUpdateNotice } from '@/api/site'
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const TYPE_LABEL = { banner: '横幅', dialog: '弹窗', page: '单页' }
const TYPE_TAG = { banner: 'info', dialog: 'warning', page: 'primary' }

const notices = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const emptyForm = () => ({ id: null, title: '', content: '', type: 'banner' })
const form = ref(emptyForm())

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
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!form.value.content.trim()) {
    ElMessage.warning('请填写内容')
    return
  }
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

.add-btn {
  margin-bottom: 16px;
}
</style>
