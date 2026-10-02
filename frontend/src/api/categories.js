import request from './index'

export const getCategories = () => request.get('/categories')
export const getCategoryTree = () => request.get('/categories/tree')
export const getTags = () => request.get('/tags')

export const adminCreateCategory = (data) => request.post('/admin/categories', data)
export const adminUpdateCategory = (id, data) => request.put(`/admin/categories/${id}`, data)
export const adminDeleteCategory = (id) => request.delete(`/admin/categories/${id}`)

export const adminCreateTag = (data) => request.post('/admin/tags', data)
export const adminUpdateTag = (id, data) => request.put(`/admin/tags/${id}`, data)
export const adminDeleteTag = (id) => request.delete(`/admin/tags/${id}`)