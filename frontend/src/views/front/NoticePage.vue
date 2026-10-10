<template>
  <div class="notice-page" v-loading="loading">
    <el-card v-if="notice">
      <h1 class="notice-title">{{ notice.title }}</h1>
      <p class="notice-meta">更新于 {{ updatedAt }}</p>
      <div class="md-preview-wrap">
        <MdPreview
          id="notice-page-preview"
          :model-value="notice.content || ''"
          :theme="theme"
          preview-theme="github"
          code-theme="atom"
          language="zh-CN"
        />
      </div>
    </el-card>
    <el-empty v-else-if="!loading" description="公告不存在或已下线">
      <el-button type="primary" @click="$router.push('/')">回到首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getNotice } from '@/api/site'
import { setupMdEditor } from '@/composables/useMdEditor'
import { useThemeStore } from '@/stores/theme'

const MdPreview = defineAsyncComponent(() => setupMdEditor().then((m) => m.MdPreview))

const route = useRoute()
const themeStore = useThemeStore()

const notice = ref(null)
const loading = ref(true)
const theme = computed(() => (themeStore.isDark ? 'dark' : 'light'))

const updatedAt = computed(() => {
  const raw = notice.value?.updated_at
  return raw ? String(raw).replace('T', ' ').slice(0, 16) : ''
})

onMounted(async () => {
  try {
    const res = await getNotice(route.params.id)
    notice.value = res.data
  } catch {
    notice.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.notice-title {
  font-family: var(--blog-font-display);
  font-size: 26px;
  margin-bottom: 8px;
}

.notice-meta {
  color: var(--blog-text-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
</style>
