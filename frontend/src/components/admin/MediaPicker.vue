<template>
  <div class="media-picker">
    <div v-if="modelValue" class="mp-current">
      <el-image :src="modelValue" :style="previewStyle" fit="cover" class="mp-preview" :preview-src-list="[modelValue]" preview-teleported>
        <template #error><div class="mp-broken">加载失败</div></template>
      </el-image>
      <div class="mp-actions">
        <el-button size="small" plain @click="openDialog('library')">更换图片</el-button>
        <el-button size="small" link type="danger" @click="clear">移除</el-button>
      </div>
    </div>
    <el-button v-else type="primary" plain @click="openDialog('upload')">
      <el-icon class="mp-btn-icon"><Plus /></el-icon>
      选择图片
    </el-button>
    <p v-if="tip" class="mp-tip">{{ tip }}</p>

    <el-dialog v-model="dialogVisible" title="选择图片" width="640px" append-to-body>
      <el-radio-group v-model="tab" size="small" class="mp-tabs">
        <el-radio-button value="upload">本地上传</el-radio-button>
        <el-radio-button value="library">媒体库</el-radio-button>
      </el-radio-group>

      <div v-show="tab === 'upload'">
        <el-upload :show-file-list="false" :auto-upload="false" :accept="accept" :on-change="handleUpload">
          <el-button :loading="uploading">
            <el-icon class="mp-btn-icon"><UploadFilled /></el-icon>
            选择本地文件上传
          </el-button>
        </el-upload>
        <div v-if="uploadPreview" class="mp-upload-preview">
          <el-image :src="uploadPreview" style="width: 100%; max-height: 220px" fit="contain" />
          <el-button type="primary" class="mp-use" @click="choose(uploadPreview)">使用此图片</el-button>
        </div>
        <p class="mp-tip">{{ uploadTip }}</p>
      </div>

      <div v-show="tab === 'library'" class="mp-library">
        <MediaLibraryGrid ref="gridRef" compact :page-size="12" @update:model-value="choose" />
        <p class="mp-tip">点击图片即可选用；库中没有时可切到"本地上传"。</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/* 统一选图入口：所有「站点配置/轮播/友链/文章封面」的图片都必须经此组件选。
 * 它把「本地上传」和「媒体库选取」两个 tab 收敛成一个 modelValue 字符串 URL。
 * 为什么禁用裸 el-upload：后台要求图片一律进媒体库并注册 media_assets 行，
 * 裸上传不经过 MediaLibraryGrid，目录树/引用保护/清理都会失真。
 * 上传成功后除了回填 preview，还要 reload 一次图库让新文件立即可见。
 */
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, UploadFilled } from '@element-plus/icons-vue'
import MediaLibraryGrid from '@/components/admin/MediaLibraryGrid.vue'
import { uploadImage } from '@/api/upload'

const props = defineProps({
  modelValue: { type: String, default: '' },
  tip: { type: String, default: '' },
  accept: { type: String, default: 'image/*' },
  previewWidth: { type: Number, default: 200 },
  previewHeight: { type: Number, default: 110 },
})

const emit = defineEmits(['update:modelValue'])

const dialogVisible = ref(false)
const tab = ref('upload')
const uploading = ref(false)
const uploadPreview = ref('')
const gridRef = ref(null)

const uploadTip = '支持 jpg/png/gif/webp/svg，单个不超过 5MB；上传后自动归入媒体库。'

const previewStyle = computed(() => ({ width: `${props.previewWidth}px`, height: `${props.previewHeight}px` }))

function openDialog(which) {
  tab.value = which
  uploadPreview.value = ''
  dialogVisible.value = true
  if (which === 'library') gridRef.value?.reload(1)
}

async function handleUpload(uploadFile) {
  const raw = uploadFile.raw || uploadFile
  if (!raw) return
  uploading.value = true
  uploadPreview.value = ''
  try {
    const res = await uploadImage(raw)
    uploadPreview.value = res.data
    gridRef.value?.reload(1)
    gridRef.value?.loadFolders?.()
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

function choose(url) {
  if (!url) return
  emit('update:modelValue', url)
  dialogVisible.value = false
}

function clear() {
  emit('update:modelValue', '')
}

defineExpose({ openDialog, notify: ElMessage })
</script>

<style scoped>
.mp-current {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mp-preview {
  border: 1px solid var(--blog-border);
  border-radius: 8px;
  flex-shrink: 0;
}

.mp-broken {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  color: var(--blog-text-secondary);
  background: var(--el-fill-color-lighter);
}

.mp-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.mp-tip {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.mp-btn-icon {
  margin-right: 3px;
}

.mp-tabs {
  margin-bottom: 14px;
}

.mp-upload-preview {
  margin-top: 12px;
}

.mp-use {
  margin-top: 10px;
}

.mp-library {
  max-height: 340px;
  overflow-y: auto;
}
</style>
