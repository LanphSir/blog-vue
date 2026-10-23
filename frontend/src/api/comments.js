// 评论接口封装。公开侧：按 slug 取评论线程、取楼内回复、发表（带图形验证码）；
// 后台侧：分页筛选（status/deleted/keyword）、通过/隐藏/软删/恢复、待审计数。
import request from './index'

export const getCommentThreads = (params) => request.get('/comments', { params })
export const getCommentCount = (slug) => request.get('/comments/count', { params: { slug } })
export const getCommentReplies = (id, params) => request.get(`/comments/${id}/replies`, { params })
export const createComment = (data) => request.post('/comments', data)

export const adminGetComments = (params) => request.get('/admin/comments', { params })
export const adminGetCommentDetail = (id) => request.get(`/admin/comments/${id}`)
export const adminApproveComment = (id) => request.post(`/admin/comments/${id}/approve`)
export const adminHideComment = (id) => request.post(`/admin/comments/${id}/hide`)
export const adminDeleteComment = (id) => request.delete(`/admin/comments/${id}`)
export const adminRestoreComment = (id) => request.post(`/admin/comments/${id}/restore`)
export const adminPinComment = (id) => request.post(`/admin/comments/${id}/pin`)
export const adminUnpinComment = (id) => request.post(`/admin/comments/${id}/unpin`)
export const adminPendingCommentCount = () => request.get('/admin/comments/pending-count')
