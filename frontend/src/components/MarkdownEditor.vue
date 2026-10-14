<template>
  <div class="md-editor-wrap">
    <div class="md-toolbar">
      <span class="md-title">Markdown 编辑器</span>
      <div class="md-actions">
        <span class="md-count">{{ wordCount }} 字</span>
        <el-button size="small" plain @click="openLibrary">
          <el-icon class="btn-icon"><Picture /></el-icon>
          从图库插入
        </el-button>
        <el-button size="small" plain @click="triggerImport">
          <el-icon class="btn-icon"><Upload /></el-icon>
          导入文件
        </el-button>
      </div>
    </div>

    <input ref="fileInput" type="file" accept=".md,.markdown,.txt,text/markdown,text/plain" class="file-input" @change="onFileChange" />

    <el-dialog v-model="libraryVisible" title="从图库选择图片插入" width="640px" append-to-body>
      <MediaLibraryGrid ref="libraryGridRef" compact :page-size="12" @update:model-value="insertFromLibrary" />
      <p class="md-count" style="margin-top: 10px">点击图片即在光标处插入图片 Markdown；库中没有时可到 后台 → 媒体库 上传。</p>
    </el-dialog>

    <component
      :is="MdEditorComponent"
      ref="editorRef"
      v-model="content"
      class="md-editor-instance"
      :theme="theme"
      :language="'zh-CN'"
      preview-theme="github"
      code-theme="atom"
      :style="{ height: '560px' }"
      @on-save="handleSave"
      @on-upload-img="handleUploadImg"
      @on-error="handleError"
    />
  </div>
</template>

<script setup>
/* Markdown 编辑器：包装 md-editor-v3 的 MdEditor，并加上「从图库插入 / 导入 .md」两个辅助能力。
 * 关键点：
 * - MdEditor 经 useMdEditor 懒加载（动态 import），不进主包；
 * - 图片上传走 handleUploadImg → uploadImage 进媒体库，返回的 URL 回填到光标处；
 * - insertFromLibrary 优先用编辑器实例的 insert() 在光标处插入，否则退化为正文末尾追加。
 */
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Upload } from '@element-plus/icons-vue'
import 'md-editor-v3/lib/style.css'
import { setupMdEditor } from '@/composables/useMdEditor'
import MediaLibraryGrid from '@/components/admin/MediaLibraryGrid.vue'
import { uploadImage } from '@/api/upload'
import { useThemeStore } from '@/stores/theme'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'save'])

const MdEditorComponent = defineAsyncComponent(() =>
  setupMdEditor().then((m) => m.MdEditor),
)

const themeStore = useThemeStore()

const content = ref(props.modelValue)
const fileInput = ref(null)
const editorRef = ref(null)
const libraryVisible = ref(false)
const libraryGridRef = ref(null)

function openLibrary() {
  libraryVisible.value = true
  libraryGridRef.value?.reload(1)
}

function insertFromLibrary(url) {
  if (!url) return
  const snippet = `![图片](${url})`
  const inst = editorRef.value
  if (inst?.insert) {
    inst.insert(() => ({ targetValue: snippet, select: false, deviationStart: 0, deviationEnd: 0 }))
  } else {
    content.value += `\n${snippet}\n`
  }
  libraryVisible.value = false
  ElMessage.success('已插入图片')
}

const theme = computed(() => (themeStore.isDark ? 'dark' : 'light'))

const wordCount = computed(() => {
  const text = content.value || ''
  const cn = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const words = text
    .replace(/[\u4e00-\u9fa5]/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean).length
  return cn + words
})

watch(content, (val) => {
  emit('update:modelValue', val)
})

watch(
  () => props.modelValue,
  (val) => {
    if (val !== content.value) content.value = val
  },
)

function triggerImport() {
  fileInput.value?.click()
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const text = String(reader.result || '')
    const apply = () => {
      content.value = text
      ElMessage.success(`已导入 ${file.name}（${text.length} 字符）`)
    }
    if (content.value.trim()) {
      ElMessageBox.confirm('导入将覆盖当前正文内容，是否继续？', '提示', { type: 'warning' })
        .then(apply)
        .catch(() => {})
    } else {
      apply()
    }
  }
  reader.readAsText(file)
  e.target.value = ''
}

function handleSave() {
  emit('save')
  return true
}

function handleUploadImg(files, callback) {
  const list = Array.isArray(files) ? files : [files]
  const uploads = list
    .filter((f) => f)
    .map(async (file) => {
      try {
        const res = await uploadImage(file)
        return res.data
      } catch {
        ElMessage.error(`图片「${file.name}」上传失败`)
        return ''
      }
    })
  Promise.all(uploads).then((urls) => callback(urls.filter(Boolean)))
}

function handleError(err) {
  const labels = {
    Cropper: '图片裁剪',
    fullscreen: '全屏',
    prettier: '格式化',
    overlength: '内容长度',
    mermaid: 'Mermaid 图表',
    echarts: 'ECharts 图表',
  }
  ElMessage.warning(`${labels[err.name] || err.name} 功能不可用：${err.message}`)
}
</script>

<style scoped>
.md-editor-wrap {
  width: 100%;
}

.md-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.md-title {
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.md-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  margin-right: 2px;
}

.md-count {
  font-size: 12px;
  color: var(--blog-text-secondary);
  white-space: nowrap;
}

.file-input {
  display: none;
}
</style>