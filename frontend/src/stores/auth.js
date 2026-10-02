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