import request from './index'

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/admin/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const adminListMedia = (params) => request.get('/admin/media', { params })

export const adminMediaFolders = () => request.get('/admin/media/folders')

export const adminDeleteMedia = (id, force = false) =>
  request.delete(`/admin/media/${id}`, { params: { force } })
