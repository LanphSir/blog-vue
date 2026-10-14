<template>
  <el-dialog
    v-model="visible"
    :title="notice.title"
    width="min(560px, 92vw)"
    :close-on-click-modal="false"
    class="notice-dialog"
    @closed="onClosed"
  >
    <div class="notice-body">
      <MdPreview
        :id="previewId"
        :model-value="notice.content || ''"
        :theme="theme"
        preview-theme="github"
        code-theme="atom"
        language="zh-CN"
      />
    </div>
    <template #footer>
      <el-button @click="visible = false">暂不查看</el-button>
      <el-button type="primary" @click="dismiss">我知道了</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/* 弹窗公告：展示 type=dialog 的最新一条未读公告。
 * dismissedKey 用 id:version 记住「本次会话内已关掉的公告」，
 * 避免 watch 因 notice 对象变化在同一个版本里反复弹。
 */
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { setupMdEditor } from '@/composables/useMdEditor'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'
import { dismissNotice } from '@/utils/notice'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))

const configStore = useConfigStore()
const themeStore = useThemeStore()

const notice = computed(() => configStore.dialogNotice() || {})
const theme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const previewId = 'notice-dialog-preview'

const visible = ref(false)
const dismissedKey = ref('')

watch(
  notice,
  (n) => {
    const key = n.id ? `${n.id}:${n.version}` : ''
    if (n.content && key && key !== dismissedKey.value) {
      visible.value = true
    }
  },
  { immediate: true },
)

function onClosed() {
  visible.value = false
}

function dismiss() {
  if (notice.value.id) {
    dismissNotice(notice.value.id, notice.value.version)
    dismissedKey.value = `${notice.value.id}:${notice.value.version}`
  }
  visible.value = false
}
</script>

<style scoped>
.notice-body {
  max-height: 56vh;
  overflow-y: auto;
}
</style>
