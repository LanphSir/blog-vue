<template>
  <transition name="notice">
    <div v-if="visible" class="notice-bar" :style="{ background: `color-mix(in srgb, var(--blog-primary) 10%, var(--blog-card))` }">
      <div class="container notice-inner">
        <span class="notice-icon">📢</span>
        <span class="notice-text">{{ text }}</span>
        <button class="notice-close" aria-label="关闭公告" @click="dismiss">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

const STORAGE_KEY = 'blog_notice_dismissed'

const text = computed(() => configStore.configs.notice_text || '')
const enabled = computed(() => {
  const v = configStore.configs.notice_enabled
  return v === undefined || v === '' || v === true || v === 'true' || v === '1'
})
const version = computed(() => configStore.configs.notice_version || '1')

const visible = ref(false)

watch(
  [text, enabled, version],
  () => {
    const dismissed = localStorage.getItem(STORAGE_KEY)
    visible.value =
      enabled.value && Boolean(text.value) && dismissed !== version.value
  },
  { immediate: true },
)

function dismiss() {
  localStorage.setItem(STORAGE_KEY, version.value)
  visible.value = false
}
</script>

<style scoped>
.notice-bar {
  border-bottom: 1px solid var(--blog-border);
  padding: 7px 0;
}

.notice-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.notice-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.notice-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--blog-text);
}

.notice-close {
  border: none;
  background: transparent;
  color: var(--blog-text-secondary);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  padding: 2px;
}

.notice-close:hover {
  color: var(--blog-primary);
}

.notice-enter-active,
.notice-leave-active {
  transition: opacity 0.25s, height 0.25s;
}

.notice-enter-from,
.notice-leave-to {
  opacity: 0;
}
</style>