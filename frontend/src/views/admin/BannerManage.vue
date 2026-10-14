<template>
  <el-card>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增轮播图</el-button>
    </div>

    <el-table :data="banners" stripe v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column prop="subtitle" label="副标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="图片" width="120">
        <template #default="{ row }">
          <el-image
            v-if="row.image"
            :src="row.image"
            fit="cover"
            style="width: 64px; height: 36px; border-radius: 4px"
            :preview-src-list="[row.image]"
            preview-teleported
          />
          <span v-else class="no-img">无</span>
        </template>
      </el-table-column>
      <el-table-column label="排序" width="110" align="center">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" size="small" controls-position="right" class="inline-sort" @change="updateSort(row)" />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="toggleEnabled(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑轮播图' : '新增轮播图'" width="520px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="轮播主标题" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subtitle" type="textarea" :rows="2" placeholder="一句话介绍" />
        </el-form-item>
        <el-form-item label="图片">
          <MediaPicker v-model="form.image" tip="建议横幅比例，支持本地上传或从媒体库选取" :preview-width="200" :preview-height="90" />
        </el-form-item>
        <el-form-item label="跳转链接">
          <el-input v-model="form.link" placeholder="如 /posts 或完整 URL（可选）" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
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
/* 轮播图管理：列表 + 新增/编辑弹窗。图片一律经 MediaPicker 选（本地上传或媒体库）。
 * 行内 el-switch 直接改 enabled 即存库；sort_order 决定首页轮播顺序。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  adminCreateBanner,
  adminDeleteBanner,
  adminGetBanners,
  adminUpdateBanner,
} from '@/api/site'
import MediaPicker from '@/components/admin/MediaPicker.vue'

const banners = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = ref({ id: null, title: '', subtitle: '', image: null, link: null, sort_order: 0, enabled: true })

async function load() {
  loading.value = true
  try {
    const res = await adminGetBanners()
    banners.value = res.data
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    form.value = { ...row }
  } else {
    form.value = { id: null, title: '', subtitle: '', image: null, link: null, sort_order: banners.value.length, enabled: true }
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.title) {
    ElMessage.warning('标题不能为空')
    return
  }
  saving.value = true
  try {
    if (form.value.id) {
      // 排序只在行内即改即存，明确字段白名单避免回写 sort_order/id 等
      const partial = { title: '', subtitle: '', image: null, link: null, enabled: true }
      for (const k of Object.keys(partial)) partial[k] = form.value[k]
      await adminUpdateBanner(form.value.id, partial)
    } else {
      const { id, ...rest } = form.value
      await adminCreateBanner(rest)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function updateSort(row) {
  try {
    await adminUpdateBanner(row.id, { sort_order: row.sort_order })
  } catch {
    load()
  }
}

async function toggleEnabled(row) {
  await adminUpdateBanner(row.id, { enabled: row.enabled })
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除轮播图「${row.title}」？`, '提示', { type: 'warning' })
  await adminDeleteBanner(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>

.no-img {
  color: var(--blog-text-secondary);
}
</style>