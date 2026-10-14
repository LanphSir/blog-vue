<template>
  <div>
    <h2 class="page-title">友情链接</h2>
    <div class="friend-grid">
      <a v-for="link in links" :key="link.id" :href="link.url" target="_blank" rel="noopener" class="card friend-card">
        <div class="name">
          <img v-if="link.icon" :src="link.icon" class="friend-icon" alt="" />
          {{ link.name }}
        </div>
        <div class="desc">{{ link.description || link.url }}</div>
      </a>
    </div>
    <el-empty v-if="!links.length" description="暂无友链" />
  </div>
</template>

<script setup>
/* 友链页：展示启用的友链卡片，点击新窗口打开。
 */
import { onMounted, ref } from 'vue'
import { getFriends } from '@/api/site'

const links = ref([])

onMounted(async () => {
  const res = await getFriends()
  links.value = res.data
})
</script>

<style scoped>
.page-title {
  margin-bottom: 16px;
}

.friend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.friend-card {
  display: block;
  transition: transform 0.2s;
}

.friend-card:hover {
  transform: translateY(-2px);
}

.name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 6px;
}

.friend-icon {
  width: 24px;
  height: 24px;
  border-radius: 5px;
  object-fit: cover;
  flex-shrink: 0;
}

.desc {
  color: var(--blog-text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>