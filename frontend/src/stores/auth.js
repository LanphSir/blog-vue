// 认证 store：token 直接存 localStorage（键 blog_token），刷新后页面初始化即恢复。
// login 成功同时写内存 ref 与 localStorage，logout 清两处，避免后台刷新残留登录态。
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getMe, login as loginApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('blog_token') || '')
  const user = ref(null)

  const isLoggedIn = () => !!token.value

  async function login(username, password, extra = {}) {
    const res = await loginApi({ username, password, ...extra })
    token.value = res.data.access_token
    localStorage.setItem('blog_token', token.value)
    await fetchUser()
  }

  async function fetchUser() {
    const res = await getMe()
    user.value = res.data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('blog_token')
  }

  return { token, user, isLoggedIn, login, fetchUser, logout }
})