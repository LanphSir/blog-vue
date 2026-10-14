<template>
  <transition name="notice">
    <div v-if="visible" class="notice-bar" :style="{ background: `color-mix(in srgb, var(--blog-primary) 10%, var(--blog-card))` }">
      <div class="container notice-inner">
        <span class="notice-icon">📢</span>
        <span class="notice-label">{{ notice.title }}</span>
        <span class="notice-text">{{ notice.content }}</span>
        <router-link v-if="notice.id && notice.content" class="notice-more" :to="{ name: 'notice', params: { id: notice.id } }">
          查看详情 →
        </router-link>
        <button class="notice-close" aria-label="关闭公告" @click="dismiss">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
/* 顶部横幅公告：展示 type=banner 且未关闭的公告。
 * 关闭走 dismissNotice 写入「版本号」，与 notice.js 的 isNoticeDismissed 配套，
 * 这样公告内容更新（版本+1）后关闭用户会重新看到。
 */
import { computed, ref, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { useConfigStore } from '@/stores/config'
import { dismissNotice, isNoticeDismissed } from '@/utils/notice'

const configStore = useConfigStore()

const notice = computed(() => configStore.bannerNotice() || {})

const visible = ref(false)

watch(
  notice,
  (n) => {
    visible.value = Boolean(n.content) && !isNoticeDismissed(n.id, n.version)
  },
  { immediate: true },
)

function dismiss() {
  if (notice.value.id) dismissNotice(notice.value.id, notice.value.version)
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

.notice-label {
  font-weight: 600;
  flex-shrink: 0;
  color: var(--blog-primary);
}

.notice-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--blog-text);
}

.notice-more {
  flex-shrink: 0;
  margin-left: 12px;
  color: var(--blog-primary);
  font-size: 13px;
  white-space: nowrap;
  text-decoration: none;
}

.notice-more:hover {
  text-decoration: underline;
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
