import request from './index'

export const getPosts = (params) => request.get('/posts', { params })
export const getPostBySlug = (slug) => request.get(`/posts/${slug}`)
export const getPostNeighbors = (slug) => request.get(`/posts/${slug}/neighbors`)

export const adminGetPosts = (params) => request.get('/admin/posts', { params })
export const adminGetPost = (id) => request.get(`/admin/posts/${id}`)
export const adminCreatePost = (data) => request.post('/admin/posts', data)
export const adminUpdatePost = (id, data) => request.put(`/admin/posts/${id}`, data)
export const adminDeletePost = (id) => request.delete(`/admin/posts/${id}`)