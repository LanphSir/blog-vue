import request from './index'

export const getSiteConfig = () => request.get('/site/config')
export const updateSiteConfig = (data) => request.put('/admin/site/config', data)
export const getSiteStats = () => request.get('/site/stats')
export const getBanners = () => request.get('/banners')
export const adminGetBanners = () => request.get('/admin/banners')
export const adminCreateBanner = (data) => request.post('/admin/banners', data)
export const adminUpdateBanner = (id, data) => request.put(`/admin/banners/${id}`, data)
export const adminDeleteBanner = (id) => request.delete(`/admin/banners/${id}`)
export const getFriends = () => request.get('/friends')
export const adminCreateFriend = (data) => request.post('/admin/friends', data)
export const adminUpdateFriend = (id, data) => request.put(`/admin/friends/${id}`, data)
export const adminDeleteFriend = (id) => request.delete(`/admin/friends/${id}`)