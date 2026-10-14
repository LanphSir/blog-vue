// 文章接口封装。公开侧按 slug 访问；后台侧支持软删除：adminDeletePost 进回收站、
// restore 恢复、permanent 彻底删除。注意 getArchive 是公开归档（无分页，按月分组）。
import request from './index'

export const getPosts = (params) => request.get('/posts', { params })
export const getPostBySlug = (slug, params) => request.get(`/posts/${slug}`, { params })
export const getArchive = () => request.get('/posts/archive')
export const getPostNeighbors = (slug) => request.get(`/posts/${slug}/neighbors`)

export const adminGetPosts = (params) => request.get('/admin/posts', { params })
export const adminGetPost = (id) => request.get(`/admin/posts/${id}`)
export const adminCreatePost = (data) => request.post('/admin/posts', data)
export const adminUpdatePost = (id, data) => request.put(`/admin/posts/${id}`, data)
export const adminDeletePost = (id) => request.delete(`/admin/posts/${id}`)
export const adminRestorePost = (id) => request.post(`/admin/posts/${id}/restore`)
export const adminPermanentDeletePost = (id) => request.delete(`/admin/posts/${id}/permanent`)