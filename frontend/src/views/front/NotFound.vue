<template>
  <div class="card notfound">
    <p class="code">404</p>
    <h1>这个页面不见了</h1>
    <p class="hint">地址可能过期或被移除，去别处逛逛吧。</p>
    <div class="actions">
      <router-link class="act primary" to="/">返回首页</router-link>
      <router-link class="act" to="/posts">浏览文章</router-link>
    </div>
  </div>
</template>

<script setup>
/* 404 页：路由 catch-all 兜底。若站点配置尚未拉取，先拉一次（为了页脚等展示站点名），失败静默。
 */
import { useConfigStore } from '@/stores/config'

const configStore = useConfigStore()
if (!Object.keys(configStore.configs).length) configStore.fetchConfig()
</script>

<style scoped>
.notfound {
  text-align: center;
  padding: 72px 24px 80px;
}

.code {
  font-family: var(--blog-font-display);
  font-size: 96px;
  font-weight: 800;
  line-height: 1;
  color: color-mix(in srgb, var(--blog-primary) 18%, transparent);
  margin: 0;
}

h1 {
  font-size: 20px;
  margin: 18px 0 8px;
}

.hint {
  color: var(--blog-text-secondary);
  font-size: 14px;
  margin-bottom: 26px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.act {
  display: inline-block;
  padding: 8px 22px;
  border: 1px solid var(--blog-border);
  border-radius: 999px;
  font-size: 14px;
  color: var(--blog-text);
  text-decoration: none;
  transition:
    color 0.15s,
    border-color 0.15s;
}

.act:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}

.act.primary {
  background: var(--blog-primary);
  border-color: var(--blog-primary);
  color: #fff;
}

.act.primary:hover {
  opacity: 0.9;
  color: #fff;
}
</style>
