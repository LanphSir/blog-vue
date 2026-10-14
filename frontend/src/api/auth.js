// 认证接口。getCaptcha 用 arraybuffer 拿图片二进制，验证码 id 在响应头 X-Captcha-Id 里。
import request from './index'

export const getCaptcha = () => request.get('/auth/captcha', { responseType: 'arraybuffer' })
export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')