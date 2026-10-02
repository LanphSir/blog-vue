<template>
  <div class="md-editor" :class="{ fullscreen }">
    <div class="md-toolbar">
      <el-tabs v-model="activeTab" class="md-tabs">
        <el-tab-pane label="编辑" name="edit" />
        <el-tab-pane label="预览" name="preview" />
      </el-tabs>

      <div class="md-actions">
        <span class="md-count">{{ wordCount }} 字</span>
        <el-button size="small" plain @click="triggerImport">
          <el-icon class="btn-icon"><Upload /></el-icon>
          导入文件
        </el-button>
        <el-tooltip content="全屏 (Ctrl+Shift+F)" placement="top">
          <el-button size="small" plain :type="fullscreen ? 'primary' : ''" @click="toggleFullscreen">
            <el-icon class="btn-icon"><FullScreen /></el-icon>
          </el-button>
        </el-tooltip>
        <el-switch v-model="split" size="small" active-text="分栏" inactive-text="" class="md-split" />
      </div>
    </div>

    <input ref="fileInput" type="file" accept=".md,.markdown,.txt,text/markdown,text/plain" class="file-input" @change="onFileChange" />

    <div class="md-body">
      <div v-show="activeTab === 'edit' || split" class="md-pane">
        <el-input
          v-model="content"
          type="textarea"
          :rows="18"
          placeholder="使用 Markdown 语法编写正文"
          resize="none"
          class="md-textarea"
        />
      </div>
      <div v-show="activeTab === 'preview' || split" class="md-pane">
        <div class="markdown-body md-preview" v-html="html" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FullScreen, Upload } from '@element-plus/icons-vue'
import { useMarkdown } from '@/composables/useMarkdown'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'save'])

const activeTab = ref('edit')
const split = ref(false)
const fullscreen = ref(false)
const content = ref(props.modelValue)
const fileInput = ref(null)

const { html } = useMarkdown(content)

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

function toggleFullscreen() {
  fullscreen.value = !fullscreen.value
}

function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    emit('save')
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.md-editor {
  width: 100%;
}

.md-editor.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 1500;
  background: var(--blog-bg);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.md-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.md-tabs :deep(.el-tabs__header) {
  margin: 0;
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

.md-split {
  margin-left: 2px;
}

.file-input {
  display: none;
}

.md-body {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.md-pane {
  flex: 1;
  min-width: 0;
}

.md-textarea :deep(textarea) {
  font-family: 'Fira Code', Consolas, monospace;
  line-height: 1.7;
}

.md-preview {
  padding: 12px;
  border: 1px solid var(--blog-border);
  border-radius: 4px;
  min-height: 420px;
  overflow: auto;
}

.fullscreen .md-preview,
.fullscreen .md-textarea {
  min-height: calc(100vh - 120px);
}
</style>