<template>
  <el-form-item v-for="field in fields" :key="field.key" :label="field.label">
    <el-input v-if="field.type === 'input'" :model-value="form[field.key]" :placeholder="field.placeholder" @update:model-value="(v) => (form[field.key] = v)" />
    <el-input
      v-else-if="field.type === 'textarea'"
      :model-value="form[field.key]"
      type="textarea"
      :rows="field.rows || 3"
      :placeholder="field.placeholder"
      @update:model-value="(v) => (form[field.key] = v)"
    />
    <el-color-picker v-else-if="field.type === 'color'" :model-value="form[field.key]" @update:model-value="(v) => (form[field.key] = v)" />
    <el-switch
      v-else-if="field.type === 'switch'"
      :model-value="form[field.key]"
      active-value="true"
      inactive-value="false"
      active-text="显示"
      inactive-text="隐藏"
      @update:model-value="(v) => (form[field.key] = v)"
    />
  </el-form-item>
</template>

<script setup>
/* 通用配置字段渲染器：按 field.type 把 input/textarea/color/switch 渲染成表单项。
 * 注意 switch 的 active-value="true" / inactive-value="false" 是字符串——
 * 与后端把布尔配置存成字符串 "true"/"false" 保持一致，前端别传布尔。
 */
defineProps({
  fields: { type: Array, required: true },
  form: { type: Object, required: true },
})
</script>
