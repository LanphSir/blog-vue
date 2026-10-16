<template>
  <!-- 勾选后浮现的批量操作条：选中数 + 插槽按钮 + 取消选择 -->
  <div v-if="count > 0" class="batch-bar">
    <span class="batch-count">已选 {{ count }} 项</span>
    <span class="batch-spacer" />
    <slot />
    <el-button link type="info" :disabled="busy" @click="$emit('clear')">取消选择</el-button>
  </div>
</template>

<script setup>
/* 通用批量操作条：本身不含业务，按钮由父组件插槽决定；
 * busy 时禁用取消，防止循环中途清空选择造成状态错位。 */
defineProps({
  count: { type: Number, default: 0 },
  busy: { type: Boolean, default: false },
})
defineEmits(['clear'])
</script>

<style scoped>
.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  margin-bottom: 12px;
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: 8px;
}

html.dark .batch-bar {
  background: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.batch-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.batch-spacer {
  flex: 1;
}
</style>
