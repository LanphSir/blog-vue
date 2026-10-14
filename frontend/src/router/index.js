// 路由表 + 守卫。
// 守卫两个要点：admin 路由 requiresAuth 且无 token 时跳登录并带 redirect；
// 登录态下再进登录页会送回 dashboard。全局 catch-all 挂在 FrontLayout 子路由末尾兜 404。
import { createRouter, createWebHistory } from 'vue-router'
import { setRouteTitle } from '@/utils/pageTitle'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/FrontLayout.vue'),
    children: [
      { path: '', name: 'home', meta: { title: '首页' }, component: () => import('@/views/front/Home.vue') },
      { path: 'posts', name: 'posts', meta: { title: '文章' }, component: () => import('@/views/front/PostList.vue') },
      { path: 'categories', name: 'categories', meta: { title: '分类' }, component: () => import('@/views/front/CategoryPage.vue') },
      { path: 'tags', name: 'tags', meta: { title: '标签' }, component: () => import('@/views/front/TagPage.vue') },
      { path: 'post/:slug', name: 'post-detail', component: () => import('@/views/front/PostDetail.vue') },
      { path: 'friends', name: 'friends', meta: { title: '友情链接' }, component: () => import('@/views/front/Friends.vue') },
      { path: 'about', name: 'about', meta: { title: '关于' }, component: () => import('@/views/front/About.vue') },
      { path: 'notice/:id', name: 'notice', component: () => import('@/views/front/NoticePage.vue') },
      { path: 'archive', name: 'archive', meta: { title: '归档' }, component: () => import('@/views/front/ArchivePage.vue') },
      { path: ':pathMatch(.*)*', name: 'not-found', meta: { title: '页面不见了' }, component: () => import('@/views/front/NotFound.vue') },
    ],
  },
  {
    path: '/admin/login',
    name: 'login',
    component: () => import('@/views/admin/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/admin/Dashboard.vue') },
      { path: 'posts', name: 'admin-posts', meta: { title: '文章管理' }, component: () => import('@/views/admin/PostManage.vue') },
      { path: 'posts/new', name: 'admin-post-create', meta: { title: '写文章' }, component: () => import('@/views/admin/PostEdit.vue') },
      { path: 'posts/:id', name: 'admin-post-edit', meta: { title: '编辑文章' }, component: () => import('@/views/admin/PostEdit.vue') },
      { path: 'categories', name: 'admin-categories', meta: { title: '分类管理' }, component: () => import('@/views/admin/CategoryManage.vue') },
      { path: 'tags', name: 'admin-tags', meta: { title: '标签管理' }, component: () => import('@/views/admin/TagManage.vue') },
      { path: 'banners', name: 'admin-banners', meta: { title: '轮播图管理' }, component: () => import('@/views/admin/BannerManage.vue') },
      { path: 'media', name: 'admin-media', meta: { title: '媒体库' }, component: () => import('@/views/admin/MediaManage.vue') },
      { path: 'menus', name: 'admin-menus', meta: { title: '导航菜单' }, component: () => import('@/views/admin/MenuManage.vue') },
      { path: 'notices', name: 'admin-notices', meta: { title: '公告管理' }, component: () => import('@/views/admin/NoticeManage.vue') },
      { path: 'config', name: 'admin-config', meta: { title: '站点配置' }, component: () => import('@/views/admin/ConfigManage.vue') },
      { path: 'friends', name: 'admin-friends', meta: { title: '友链管理' }, component: () => import('@/views/admin/FriendManage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const token = localStorage.getItem('blog_token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && token) {
    return { name: 'dashboard' }
  }
  return true
})

router.afterEach((to) => {
  setRouteTitle(to.meta.title || '')
})

export default router