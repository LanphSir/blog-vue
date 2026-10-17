<template>
  <PageLoading />
  <router-view />
</template>

<!-- 根组件：挂载全局路由加载动画 + 把路由视图挂出来，
     具体布局（前台/后台）由路由的布局组件决定。 -->
<script setup>
import PageLoading from '@/components/PageLoading.vue'
</script>
