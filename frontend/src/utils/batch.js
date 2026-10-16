// 批量操作执行器（配合各管理页的勾选列 + BatchBar 使用）。
// 约定：批量 = 前端逐条循环复用现有单条接口，不新增 bulk 端点——这样软删除、
// 引用保护、级联校验等语义 100% 走单条路径，不产生第二套逻辑。
// 静默失败：响应拦截器失败时会弹 toast，批量循环里逐条弹会刷屏，
// 所以这里临时静音，最后只汇报一条聚合结果。
import { ElMessage } from 'element-plus'

/** 并行执行 ids 上的 fn(id)，返回 { ok: number, failed: Array<{ id, message }> }。 */
export async function runBatch(ids, fn) {
  const failed = []
  let ok = 0
  let quietUntil = 0
  const realError = ElMessage.error
  ElMessage.error = (msg) => {
    if (Date.now() < quietUntil) return { close: () => {} }
    return realError(msg)
  }
  try {
    const results = await Promise.allSettled(ids.map((id) => fn(id)))
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') ok += 1
      else failed.push({ id: ids[i], message: r.reason?.message || '操作失败' })
    })
  } finally {
    ElMessage.error = realError
    quietUntil = 0
  }
  return { ok, failed }
}

/** 汇报聚合结果：全成功 success，否则 warning 列出失败原因（去重、最多 3 条）。 */
export function reportBatch({ ok, failed }, successText) {
  if (!failed.length) {
    ElMessage.success(`${successText}（共 ${ok} 项）`)
    return
  }
  const reasons = [...new Set(failed.map((f) => f.message))].slice(0, 3)
  ElMessage.warning(
    `成功 ${ok} 项、失败 ${failed.length} 项：${reasons.join('；')}${failed.length > 3 ? ' 等' : ''}`,
  )
}
