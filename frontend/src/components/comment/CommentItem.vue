<template>
  <div class="comment-item" :class="{ deleted: comment.deleted, pinned: comment.is_pinned }">
    <CommentAvatar :nickname="comment.nickname" :size="size" />
    <div class="body">
      <div class="head">
        <span class="nick">{{ comment.nickname }}</span>
        <el-tag v-if="comment.is_pinned" size="small" type="danger" effect="light" class="pin-tag">置顶</el-tag>
        <span class="time">{{ fromNow(comment.created_at) }}</span>
      </div>
      <div class="content">
        <span v-if="comment.reply_to_nickname" class="reply-to">回复 @{{ comment.reply_to_nickname }}：</span>
        <!-- 被删占位：纯文本灰显；正常评论：Markdown 渲染（raw HTML 被禁，防 XSS） -->
        <span v-if="comment.deleted" class="deleted-text">{{ comment.content }}</span>
        <MdPreview
          v-else
          :id="previewId"
          :model-value="comment.content"
          :theme="mdTheme"
          no-mermaid
          no-katex
          @on-html-changed="onHtmlChanged"
        />
      </div>
      <div v-if="!comment.deleted" class="actions">
        <el-button link type="primary" size="small" @click="$emit('reply', comment)">回复</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 评论行：头像 + 昵称（可带置顶徽标）+ 相对时间 + 内容。内容按 Markdown 渲染
// （复用 md-editor-v3 懒加载实例与 preview.css，正文区同款），跟随明暗主题；
// 被删占位纯文本灰显且无回复入口。链接新窗口打开。
import 'md-editor-v3/lib/preview.css'
import { computed } from 'vue'
import { defineAsyncComponent } from 'vue'
import { setupMdEditor } from '@/composables/useMdEditor'
import { useThemeStore } from '@/stores/theme'
import CommentAvatar from './CommentAvatar.vue'
import { fromNow } from '@/utils/commentAvatar'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))

const props = defineProps({
  comment: { type: Object, required: true },
  size: { type: Number, default: 40 },
})
defineEmits(['reply'])

const themeStore = useThemeStore()
const mdTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
// MdPreview 的 id 必须全局唯一（内部用它定位 DOM）
const previewId = `comment-preview-${props.comment.id}`

// 评论内容里的链接跳走时别带走当前页（MdPreview 渲染完成后统一加 target）
function onHtmlChanged() {
  const root = document.getElementById(previewId)
  root?.querySelectorAll('.md-editor-preview a').forEach((a) => {
    a.target = '_blank'
    a.rel = 'noopener'
  })
}
</script>

<style scoped>
.comment-item {
  display: flex;
  gap: 12px;
}
.body {
  flex: 1;
  min-width: 0;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nick {
  font-weight: 600;
  font-size: 14px;
  color: var(--blog-text);
}
.pin-tag {
  transform: scale(0.85);
  transform-origin: left center;
}
.time {
  font-size: 12px;
  color: var(--blog-text-secondary);
}
.content {
  margin-top: 4px;
  color: var(--blog-text);
  word-break: break-word;
}
.reply-to {
  color: var(--blog-primary);
  font-size: 14px;
}
.deleted-text {
  color: var(--blog-text-secondary);
  font-style: italic;
  font-size: 14px;
}
.comment-item.deleted .nick {
  color: var(--blog-text-secondary);
}
.actions {
  margin-top: 2px;
}
/* 评论内容复用正文 MdPreview 但压到 14px 无内边距，跟整页排版贴合 */
.content :deep(.md-editor) {
  background: transparent;
  display: inline;
}
.content :deep(.md-editor-preview-wrapper) {
  padding: 0;
}
.content :deep(.md-editor-preview) {
  font-size: 14px;
  line-height: 1.7;
}
.content :deep(.md-editor-preview p) {
  margin: 0.2em 0;
}
.content :deep(.md-editor-preview pre) {
  margin: 8px 0;
  font-size: 13px;
}
.content :deep(.md-editor-preview img) {
  max-width: 100%;
}
</style>
