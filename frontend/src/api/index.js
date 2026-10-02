import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem('blog_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const ct = response.headers['content-type'] || ''
    if (!ct.includes('json')) {
      return response
    }
    const res = response.data
    if (res.code !== undefined && res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      if (res.code === 401) {
        localStorage.removeItem('blog_token')
        router.push({ name: 'login' })
      }
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('blog_token')
      router.push({ name: 'login' })
    }
    ElMessage.error(error.response?.data?.message || error.message || '网络错误')
    return Promise.reject(error)
  },
)

export default service