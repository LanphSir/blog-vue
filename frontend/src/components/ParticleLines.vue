<template>
  <canvas ref="canvasRef" class="particle-bg" aria-hidden="true" />
</template>

<script setup>
/* 线条背景（site_background=line 时由 FrontLayout 挂载）：
 * canvas 粒子连线动画，颜色跟随强调色、暗色下自动提亮。
 * 三个坑位：
 * - canvas 是「替换元素」，CSS 里必须显式给 100vw/100vh（见 style），否则 abspos 不会拉伸它；
 * - 坐标用 canvas.clientWidth/clientHeight 而非 window.innerWidth——后者含滚动条会错位；
 * - prefers-reduced-motion 用户只画一帧不启动 rAF，且切后台隐藏时 stop() 停 rAF。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useConfigStore } from '@/stores/config'
import { useThemeStore } from '@/stores/theme'

const LINK_DIST = 110
const POINTER_DIST = 160

const configStore = useConfigStore()
const themeStore = useThemeStore()
const canvasRef = ref(null)

let ctx = null
let rafId = 0
let particles = []
let rgb = '37, 99, 235'
let viewW = window.innerWidth
let viewH = window.innerHeight
const pointer = { x: -9999, y: -9999 }
let running = false

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')

function hexToRgb(hex) {
  const m = /^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.exec((hex || '').trim())
  if (!m) return null
  let h = m[1]
  if (h.length === 3) h = [...h].map((c) => c + c).join('')
  const n = parseInt(h, 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function refreshColor() {
  let parts = hexToRgb(configStore.accentColor()) || [37, 99, 235]
  if (themeStore.isDark) {
    parts = parts.map((c) => Math.round(c + (255 - c) * 0.35))
  }
  rgb = parts.join(', ')
}

function spawn() {
  const w = viewW
  const h = viewH
  const count = Math.min(80, Math.max(26, Math.floor((w * h) / 24000)))
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
  }))
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  // 用画布实际 CSS 尺寸（clientWidth 不含滚动条），避免与 innerWidth 拉伸错位
  viewW = canvas.clientWidth || window.innerWidth
  viewH = canvas.clientHeight || window.innerHeight
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
  canvas.width = viewW * dpr
  canvas.height = viewH * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  spawn()
}

function drawFrame() {
  const canvas = canvasRef.value
  if (!canvas || !ctx) return
  const w = viewW
  const h = viewH
  ctx.clearRect(0, 0, w, h)

  for (const p of particles) {
    if (running) {
      const dx = pointer.x - p.x
      const dy = pointer.y - p.y
      const pd = Math.hypot(dx, dy)
      if (pd < POINTER_DIST && pd > 1) {
        p.vx += (dx / pd) * 0.012
        p.vy += (dy / pd) * 0.012
      }
      p.vx = Math.max(-0.8, Math.min(0.8, p.vx))
      p.vy = Math.max(-0.8, Math.min(0.8, p.vy))
      p.x += p.vx
      p.y += p.vy
      if (p.x < -20) p.x = w + 20
      if (p.x > w + 20) p.x = -20
      if (p.y < -20) p.y = h + 20
      if (p.y > h + 20) p.y = -20
    }
  }

  for (let i = 0; i < particles.length; i++) {
    const a = particles[i]
    for (let j = i + 1; j < particles.length; j++) {
      const b = particles[j]
      const dx = a.x - b.x
      const dy = a.y - b.y
      const d = Math.hypot(dx, dy)
      if (d >= LINK_DIST) continue
      ctx.strokeStyle = `rgba(${rgb}, ${((1 - d / LINK_DIST) * 0.5).toFixed(3)})`
      ctx.lineWidth = 1.4
      ctx.beginPath()
      ctx.moveTo(a.x, a.y)
      ctx.lineTo(b.x, b.y)
      ctx.stroke()
    }
    const pd = Math.hypot(pointer.x - a.x, pointer.y - a.y)
    if (pd < POINTER_DIST) {
      ctx.strokeStyle = `rgba(${rgb}, ${((1 - pd / POINTER_DIST) * 0.85).toFixed(3)})`
      ctx.beginPath()
      ctx.moveTo(a.x, a.y)
      ctx.lineTo(pointer.x, pointer.y)
      ctx.stroke()
    }
    ctx.fillStyle = `rgba(${rgb}, 0.7)`
    ctx.beginPath()
    ctx.arc(a.x, a.y, 1.9, 0, Math.PI * 2)
    ctx.fill()
  }
}

function loop() {
  drawFrame()
  rafId = requestAnimationFrame(loop)
}

function start() {
  if (running || reduced.matches) return
  running = true
  rafId = requestAnimationFrame(loop)
}

function stop() {
  running = false
  cancelAnimationFrame(rafId)
}

function onVisibility() {
  if (document.hidden) stop()
  else start()
}

function onPointerMove(e) {
  pointer.x = e.clientX
  pointer.y = e.clientY
}

function onPointerLeave() {
  pointer.x = -9999
  pointer.y = -9999
}

onMounted(() => {
  ctx = canvasRef.value.getContext('2d')
  refreshColor()
  resize()
  if (reduced.matches) {
    drawFrame()
  } else {
    start()
  }
  window.addEventListener('resize', resize)
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  document.addEventListener('pointerleave', onPointerLeave)
  document.addEventListener('visibilitychange', onVisibility)
})

onBeforeUnmount(() => {
  stop()
  window.removeEventListener('resize', resize)
  window.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerleave', onPointerLeave)
  document.removeEventListener('visibilitychange', onVisibility)
})

watch([() => configStore.accentColor(), () => themeStore.isDark], () => {
  refreshColor()
  if (!running) drawFrame()
})
</script>

<style scoped>
.particle-bg {
  position: fixed;
  inset: 0;
  /* canvas 属替换元素，abspos 下不会随 inset 拉伸，必须显式占满视口 */
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
}
</style>
