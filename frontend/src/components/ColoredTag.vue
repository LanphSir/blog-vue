<template>
  <span class="colored-tag" :style="tagStyle"><slot>{{ text }}</slot></span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  color: { type: String, default: '' },
  size: { type: String, default: 'small' },
})

const tagStyle = computed(() => {
  if (!props.color || !/^#([0-9a-fA-F]{3}){1,2}$/.test(props.color)) {
    return { '--tag-bg': 'var(--blog-bg)', '--tag-fg': 'var(--blog-text-secondary)' }
  }
  return {
    '--tag-bg': `color-mix(in srgb, ${props.color} 14%, transparent)`,
    '--tag-fg': props.color,
    '--tag-border': `color-mix(in srgb, ${props.color} 45%, transparent)`,
  }
})
</script>

<style scoped>
.colored-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1.6;
  background: var(--tag-bg, var(--blog-bg));
  color: var(--tag-fg, var(--blog-text-secondary));
  border: 1px solid var(--tag-border, var(--blog-border));
  white-space: nowrap;
}

html.dark .colored-tag {
  background: color-mix(in srgb, var(--tag-fg, #fff) 16%, transparent);
  color: color-mix(in srgb, var(--tag-fg, #9ca3af) 78%, #fff);
  border-color: color-mix(in srgb, var(--tag-fg, #fff) 35%, transparent);
}
</style>