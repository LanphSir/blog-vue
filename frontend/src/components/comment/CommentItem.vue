<template>
  <div class="comment-item" :class="{ deleted: comment.deleted }">
    <CommentAvatar :nickname="comment.nickname" :size="size" />
    <div class="body">
      <div class="head">
        <span class="nick">{{ comment.nickname }}</span>
        <span class="time">{{ fromNow(comment.created_at) }}</span>
      </div>
      <p class="content">
        <span v-if="comment.reply_to_nickname" class="reply-to">回复 @{{ comment.reply_to_nickname }}：</span>
        <span :class="{ 'deleted-text': comment.deleted }">{{ comment.content }}</span>
      </p>
      <div v-if="!comment.deleted && !readonly" class="actions">
        <el-button link type="primary" size="small" @click="$emit('reply', comment)">回复</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 评论行：头像 + 昵称 + 相对时间 + 内容。后端把被删评论的 content 换成占位文案并
// 带 deleted=true，这里灰显斜体且不提供回复入口。
import CommentAvatar from './CommentAvatar.vue'
import { fromNow } from '@/utils/commentAvatar'

defineProps({
  comment: { type: Object, required: true },
  size: { type: Number, default: 40 },
  readonly: { type: Boolean, default: false },
})
defineEmits(['reply'])
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
  align-items: baseline;
  gap: 10px;
}
.nick {
  font-weight: 600;
  font-size: 14px;
  color: var(--blog-text);
}
.time {
  font-size: 12px;
  color: var(--blog-text-secondary);
}
.content {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--blog-text);
  white-space: pre-wrap;
  word-break: break-word;
}
.reply-to {
  color: var(--blog-primary);
}
.deleted-text {
  color: var(--blog-text-secondary);
  font-style: italic;
}
.comment-item.deleted .nick {
  color: var(--blog-text-secondary);
}
.actions {
  margin-top: 2px;
}
</style>
