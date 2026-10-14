<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="title">博客后台登录</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item class="captcha-row">
          <el-input v-model="form.captcha_code" placeholder="验证码" size="large" maxlength="4" class="captcha-input" @keyup.enter="handleLogin" />
          <img v-if="captchaSrc" :src="captchaSrc" class="captcha-img" alt="验证码" @click="refreshCaptcha" />
          <el-button link size="large" @click="refreshCaptcha">换一张</el-button>
        </el-form-item>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="handleLogin">
          登 录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
/* 后台登录：用户名密码 + 图形验证码。
 * 验证码接口返回 arraybuffer，需要先转 base64 当 <img> 源；验证码 id 在响应头 X-Captcha-Id。
 * 登录成功按 ?redirect 或 /admin 跳转；失败刷新验证码并清空输入。
 */
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/index'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const form = ref({ username: '', password: '', captcha_id: '', captcha_code: '' })
const loading = ref(false)
const captchaSrc = ref('')

function arrayBufferToBase64(buf) {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

async function refreshCaptcha() {
  try {
    const resp = await request.get('/auth/captcha', { responseType: 'arraybuffer' })
    form.value.captcha_id = resp.headers['x-captcha-id'] || resp.headers['X-Captcha-Id'] || ''
    const base64 = arrayBufferToBase64(resp.data)
    captchaSrc.value = `data:image/png;base64,${base64}`
  } catch {
    captchaSrc.value = ''
  }
}

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  if (!form.value.captcha_code || !form.value.captcha_id) {
    ElMessage.warning('请输入验证码或点击刷新')
    return
  }
  loading.value = true
  try {
    await authStore.login(form.value.username, form.value.password, {
      captcha_id: form.value.captcha_id,
      captcha_code: form.value.captcha_code,
    })
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/admin')
  } catch {
    refreshCaptcha()
    form.value.captcha_code = ''
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1d1e1f 0%, #2b2d31 100%);
}

.login-card {
  width: 380px;
  border-radius: 12px;
}

.title {
  text-align: center;
  margin-bottom: 24px;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.captcha-input {
  width: 130px;
}

.captcha-img {
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--blog-border);
}

.submit {
  width: 100%;
}
</style>