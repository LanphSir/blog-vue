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
        :style="badgeStyle(link)"
        :title="badgeTitle(link)"
      >
        <img v-if="link.icon_url" :src="link.icon_url" class="badge-icon" :alt="badgeTitle(link)" />
        <template v-else>{{ badgeLetter(link) }}</template>
      </a>
    </div>
  </div>
</template>

<script setup>
/* 侧边简介卡：头像/昵称/简介 + 社交链接徽章。
 * 徽章样式/字母/标题统一走 platforms 的预设；custom 平台回退用 label 取首字母。
 */
import { computed } from 'vue'
import { useConfigStore } from '@/stores/config'
import { platformMeta } from '@/utils/platforms'

const configStore = useConfigStore()

const avatar = computed(() => configStore.configs.site_avatar || '')
const name = computed(() => configStore.configs.site_author || configStore.siteName())
const bio = computed(() => configStore.configs.site_bio || configStore.configs.site_description || '')
const links = computed(() => configStore.profileLinks())

const initial = computed(() => name.value.slice(0, 1).toUpperCase())

function badgeStyle(link) {
  const meta = platformMeta(link.platform)
  if (link.color) {
    return { background: link.color, color: '#fff' }
  }
  if (!meta) {
    return { background: 'var(--blog-border)', color: 'var(--blog-text-secondary)' }
  }
  return { background: meta.color, color: '#fff' }
}

function badgeTitle(link) {
  const meta = platformMeta(link.platform)
  return meta?.name || link.label || link.platform
}

function badgeLetter(link) {
  const meta = platformMeta(link.platform)
  if (!meta) {
    const seed = link.platform === 'custom' ? link.label : link.platform
    return String(seed || '?').slice(0, 1).toUpperCase()
  }
  return meta.letter
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

.badge-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: inherit;
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