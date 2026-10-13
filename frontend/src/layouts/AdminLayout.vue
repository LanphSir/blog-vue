<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="admin-aside">
      <div class="brand">{{ configStore.siteName() }} 后台</div>
      <el-menu :default-active="route.path" router background-color="#1d1e1f" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item index="/admin">仪表盘</el-menu-item>
        <el-menu-item index="/admin/posts">文章管理</el-menu-item>
        <el-menu-item index="/admin/categories">分类管理</el-menu-item>
        <el-menu-item index="/admin/tags">标签管理</el-menu-item>
        <el-menu-item index="/admin/friends">友链管理</el-menu-item>
        <el-menu-item index="/admin/banners">轮播图</el-menu-item>
        <el-menu-item index="/admin/media">媒体库</el-menu-item>
        <el-menu-item index="/admin/menus">导航菜单</el-menu-item>
        <el-menu-item index="/admin/notices">公告管理</el-menu-item>
        <el-menu-item index="/admin/config">站点配置</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <span class="title">{{ route.meta.title || '管理后台' }}</span>
        <div class="user-info">
          <span>{{ authStore.user?.username }}</span>
          <el-button link type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useConfigStore } from '@/stores/config'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const configStore = useConfigStore()

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser().catch(() => {})
  }
  configStore.fetchConfig().then(() => {
    document.documentElement.dataset.bg = 'none'
  })
})

onUnmounted(() => {
  configStore.applyBackground()
})

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.admin-aside {
  background: #1d1e1f;
}

.brand {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid #333;
}

.admin-header {
  background: var(--blog-card);
  border-bottom: 1px solid var(--blog-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-main {
  background: var(--blog-bg);
}
</style>