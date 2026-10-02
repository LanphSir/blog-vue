import request from './index'

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/admin/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}