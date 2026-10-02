import request from './index'

export const getCaptcha = () => request.get('/auth/captcha', { responseType: 'arraybuffer' })
export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')