<template>
  <div class="card profile-card">
    <div class="avatar-wrap">
      <img v-if="avatar" :src="avatar" class="avatar" :alt="name" />
      <span v-else class="avatar avatar-fallback">{{ initial }}</span>
    </div>
    <h3 class="name">{{ name }}</h3>
    <p v-if="bio" class="bio">{{ bio }}</p>
    <div v-if="links.length" class="links">
      <a
        v-for="link in links"
        :key="link.platform + link.url"
        :href="link.url"
        target="_blank"
        rel="noopener"
        class="link-badge"
        :style="platformStyle(link.platform)"
        :title="platformName(link.platform)"
      >
        {{ platformLetter(link.platform) }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()

const avatar = computed(() => configStore.configs.site_avatar || '')
const name = computed(() => configStore.configs.site_author || configStore.siteName())
const bio = computed(() => configStore.configs.site_bio || configStore.configs.site_description || '')
const links = computed(() => configStore.profileLinks())

const initial = computed(() => name.value.slice(0, 1).toUpperCase())

const PLATFORMS = {
  github: { name: 'GitHub', color: '#333333', letter: 'G' },
  juejin: { name: '掘金', color: '#1E80FF', letter: '掘' },
  zhihu: { name: '知乎', color: '#0084FF', letter: '知' },
  csdn: { name: 'CSDN', color: '#FC5531', letter: 'C' },
  x: { name: 'X', color: '#000000', letter: 'X' },
  email: { name: '邮箱', color: '#EA4335', letter: '@' },
  wechat: { name: '微信', color: '#07C160', letter: '微' },
  bilibili: { name: 'B 站', color: '#FB7299', letter: 'B' },
}

function platformStyle(platform) {
  const key = String(platform || '').toLowerCase()
  const meta = PLATFORMS[key]
  if (!meta) {
    return { background: 'var(--blog-border)', color: 'var(--blog-text-secondary)' }
  }
  if (key === 'x' || key === 'github') {
    return { background: meta.color, color: '#fff' }
  }
  return { background: meta.color, color: '#fff' }
}

function platformName(platform) {
  const key = String(platform || '').toLowerCase()
  return PLATFORMS[key]?.name || platform
}

function platformLetter(platform) {
  const key = String(platform || '').toLowerCase()
  return PLATFORMS[key]?.letter || (platform || '?').slice(0, 1).toUpperCase()
}
</script>

<style scoped>
.profile-card {
  text-align: center;
  padding: 24px 20px;
}

.avatar-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.avatar {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  font-weight: 700;
  color: #fff;
  background: var(--blog-primary);
}

.name {
  font-family: var(--blog-font-display);
  font-size: 18px;
  margin-bottom: 8px;
}

.bio {
  color: var(--blog-text-secondary);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 14px;
}

.links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.link-badge {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  transition: transform 0.2s;
}

.link-badge:hover {
  transform: translateY(-2px) scale(1.06);
}
</style>