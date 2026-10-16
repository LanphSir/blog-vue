// 上传与媒体库接口。上传走 multipart；删除=软删进回收站，
// 彻底删除带 force 参数可跳过「被引用」保护强制物理删除。
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

export const adminDeleteMedia = (id) => request.delete(`/admin/media/${id}`)

export const adminRestoreMedia = (id) => request.post(`/admin/media/${id}/restore`)

export const adminPermanentDeleteMedia = (id, force = false) =>
  request.delete(`/admin/media/${id}/permanent`, { params: { force } })
