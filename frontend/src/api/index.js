// 统一的 axios 实例 + 请求/响应拦截器。
// 后端所有接口都包一层 {code, message, data} 信封：响应拦截器在这里解包，
// code!==0 视为失败并提示；401 一律清 token 并跳登录页（前台/后台逻辑一致）。
// 非 JSON 响应（如上传、验证码这类 arraybuffer）直接原样放行。
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