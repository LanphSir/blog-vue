<template>
  <div class="card about-card">
    <h2>关于我</h2>
    <p>{{ configStore.configs.site_description || '记录技术、生活与思考' }}</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

onMounted(() => {
  configStore.fetchConfig()
})
</script>