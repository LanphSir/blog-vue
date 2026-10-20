<template>
  <div class="comment-avatar" :style="style">{{ text }}</div>
</template>

<script setup>
// 评论头像：昵称哈希色块 + 首字符，无图片依赖（纯 CSS 即可稳定渲染）。
import { computed } from 'vue'
import { avatarColor, avatarText } from '@/utils/commentAvatar'

const props = defineProps({
  nickname: { type: String, default: '' },
  size: { type: Number, default: 40 },
})
const style = computed(() => ({
  background: avatarColor(props.nickname),
  width: `${props.size}px`,
  height: `${props.size}px`,
  'font-size': `${Math.max(12, Math.round(props.size * 0.42))}px`,
}))
const text = computed(() => avatarText(props.nickname))
</script>

<style scoped>
.comment-avatar {
  border-radius: 50%;
  color: #fff;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  user-select: none;
}
</style>
