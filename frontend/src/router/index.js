import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/FrontLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/front/Home.vue') },
      { path: 'posts', name: 'posts', component: () => import('@/views/front/PostList.vue') },
      { path: 'categories', name: 'categories', component: () => import('@/views/front/CategoryPage.vue') },
      { path: 'tags', name: 'tags', component: () => import('@/views/front/TagPage.vue') },
      { path: 'post/:slug', name: 'post-detail', component: () => import('@/views/front/PostDetail.vue') },
      { path: 'friends', name: 'friends', component: () => import('@/views/front/Friends.vue') },
      { path: 'about', name: 'about', component: () => import('@/views/front/About.vue') },
    ],
  },
  {
    path: '/admin/login',
    name: 'login',
    component: () => import('@/views/admin/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/admin/Dashboard.vue') },
      { path: 'posts', name: 'admin-posts', component: () => import('@/views/admin/PostManage.vue') },
      { path: 'posts/new', name: 'admin-post-create', component: () => import('@/views/admin/PostEdit.vue') },
      { path: 'posts/:id', name: 'admin-post-edit', component: () => import('@/views/admin/PostEdit.vue') },
      { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/CategoryManage.vue') },
      { path: 'tags', name: 'admin-tags', component: () => import('@/views/admin/TagManage.vue') },
      { path: 'banners', name: 'admin-banners', component: () => import('@/views/admin/BannerManage.vue') },
      { path: 'config', name: 'admin-config', component: () => import('@/views/admin/ConfigManage.vue') },
      { path: 'friends', name: 'admin-friends', component: () => import('@/views/admin/FriendManage.vue') },
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

export default router