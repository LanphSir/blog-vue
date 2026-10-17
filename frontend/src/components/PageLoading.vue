<template>
  <Transition name="pl-fade">
    <div v-if="active" class="page-loading" :class="'pl-mode-' + mode">
      <div v-if="mode === 'spinner'" class="pl-spinner" />
      <div v-else-if="mode === 'bar'" class="pl-bar"><i /></div>
      <div v-else-if="mode === 'progress'" class="pl-scan" />
    </div>
  </Transition>
</template>

<script setup>
/* 全局页面加载动画（0.14.0）：配置键 site_loading = spinner/progress/bar/none。
 * 数据源是 utils/loadingBus（axios 请求活动计数）：切换页面后的“空白等待期”
 * 就是请求在途的时段，动画覆盖它而不是路由切换的一瞬。
 * 请求结束后再停留 MIN_MS 淡出，避免快请求时一闪而过；spinner 模式带半透明
 * 遮罩盖住空白内容区，bar/progress 是顶部指示条不遮内容。动画仅 transform/
 * width/opacity；reduced-motion 下静止。
 */
import { computed, onBeforeUnmount, ref } from 'vue'
import { useConfigStore } from '@/stores/config'
import { onActivityChange } from '@/utils/loadingBus'

const MIN_MS = 400
const configStore = useConfigStore()
const active = ref(false)
let hideTimer = 0
let requestActive = false

// computed 而非函数：模板里 mode 直接当值用（:class 拼接与 v-if 比较）
const mode = computed(() => configStore.loadingMode())

function render() {
  const on = requestActive && mode.value !== 'none'
  if (on) {
    clearTimeout(hideTimer)
    active.value = true
  } else if (active.value) {
    clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      active.value = false
    }, MIN_MS)
  }
}

const unsubscribe = onActivityChange((on) => {
  requestActive = on
  render()
})
onBeforeUnmount(() => {
  unsubscribe()
  clearTimeout(hideTimer)
})
</script>

<style scoped>
.page-loading {
  position: fixed;
  inset: 0;
  z-index: 99999;
  pointer-events: none;
}

/* 旋转环模式需要盖住空白内容，其余两种是顶部指示条 */
.pl-mode-spinner {
  background: color-mix(in srgb, var(--blog-bg, #fff) 62%, transparent);
}

/* 旋转环：居中 */
.pl-spinner {
  position: absolute;
  top: 42%;
  left: 50%;
  width: 38px;
  height: 38px;
  margin: -19px 0 0 -19px;
  border-radius: 50%;
  border: 3px solid color-mix(in srgb, var(--blog-primary) 18%, transparent);
  border-top-color: var(--blog-primary);
  animation: pl-spin 0.8s linear infinite;
}

/* 进度条：顶部，宽度先到 ~90% 再缓慢逼近 */
.pl-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  overflow: hidden;
}

.pl-bar i {
  display: block;
  height: 100%;
  width: 20%;
  background: linear-gradient(90deg, var(--blog-primary), color-mix(in srgb, var(--blog-primary) 55%, #fff));
  animation: pl-grow 2.4s cubic-bezier(0.1, 0.7, 0.2, 1) forwards;
}

/* 扫光：顶部 2px 高光来回 */
.pl-scan {
  position: absolute;
  top: 0;
  left: -40%;
  width: 40%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--blog-primary), transparent);
  animation: pl-scan 0.9s ease-in-out infinite;
}

@keyframes pl-spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pl-grow {
  0% {
    width: 12%;
  }
  40% {
    width: 62%;
  }
  100% {
    width: 92%;
  }
}

@keyframes pl-scan {
  to {
    transform: translateX(350%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pl-spinner,
  .pl-bar i,
  .pl-scan {
    animation: none;
  }
}

.pl-fade-leave-active {
  transition: opacity 0.25s ease;
}

.pl-fade-leave-to {
  opacity: 0;
}
</style>
