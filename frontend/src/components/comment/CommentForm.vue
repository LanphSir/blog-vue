<template>
  <div class="comment-form" :class="{ compact }">
    <div class="form-row">
      <el-input v-model="form.nickname" maxlength="30" placeholder="昵称" class="nick-input" />
      <el-input v-model="form.email" maxlength="100" placeholder="邮箱（选填，不会公开显示）" class="email-input" />
      <el-tooltip content="换一个身份：清空本机记忆并重新随机昵称" placement="top">
        <el-button class="identity-btn" circle :icon="RefreshRight" @click="confirmSwitchIdentity" />
      </el-tooltip>
    </div>
    <el-input
      v-model="form.content"
      type="textarea"
      :rows="compact ? 2 : 4"
      maxlength="500"
      show-word-limit
      :placeholder="placeholder"
    />
    <div class="form-row actions-row">
      <span class="md-hint">支持 Markdown</span>
      <span class="spacer" />
      <el-button v-if="compact" size="small" @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" :size="compact ? 'small' : 'default'" @click="openCaptchaDialog">
        {{ submitText }}
      </el-button>
    </div>

    <!-- 点击发表后才弹框验证：正文反复编辑不会触发拉图（验证码有时效，早拉会过期），
         弹框内图片点击刷新带防抖，避免连点刷爆验证码接口 -->
    <el-dialog
      v-model="captchaOpen"
      title="安全验证"
      width="360px"
      :close-on-click-modal="false"
      :close-on-press-escape="!submitting"
      :show-close="!submitting"
      append-to-body
      destroy-on-close
    >
      <div class="captcha-box">
        <el-input
          v-model="form.captcha_code"
          maxlength="4"
          placeholder="请输入图中字符"
          @keyup.enter="submit"
        />
        <div class="captcha-img-wrap" title="点击刷新" @click="refreshCaptchaDebounced">
          <img v-if="captchaSrc" :src="captchaSrc" class="captcha-img" alt="验证码，点击刷新" />
          <span v-else class="captcha-placeholder">加载中…</span>
        </div>
      </div>
      <template #footer>
        <el-button :disabled="submitting" @click="captchaOpen = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">{{ submitText }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 发表评论/回复共用的表单。身份：昵称/邮箱自动带出本机记忆（blog_comment_identity），
// 「换一个身份」清空并重随机。验证码在点击发表后以弹框展示并拉取（时效短，
// 不做输入即预取），提交失败自动换新图；图片点击刷新走防抖。提交成功即写入身份记忆。
import { onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import request from '@/api/index'
import { createComment } from '@/api/comments'
import { randomNickname } from '@/utils/commentAvatar'
import { debounce } from '@/utils/debounce'
import { clearIdentity, getIdentity, saveIdentity } from '@/utils/commentIdentity'

const props = defineProps({
  postSlug: { type: String, required: true },
  parentId: { type: Number, default: null },
  compact: { type: Boolean, default: false },
  placeholder: { type: String, default: '说点什么吧，友善的评论会让人心情愉快～' },
  submitText: { type: String, default: '发表评论' },
})
const emit = defineEmits(['created', 'cancel'])

const remembered = getIdentity()
const form = reactive({
  nickname: remembered ? remembered.nickname : randomNickname(),
  email: remembered ? remembered.email : '',
  content: '',
  captcha_id: '',
  captcha_code: '',
})
const captchaOpen = ref(false)
const captchaSrc = ref('')
const submitting = ref(false)

// 图标按钮点确认后再清：换身份会丢弃本机记忆和已填邮箱，误点成本高
async function confirmSwitchIdentity() {
  try {
    await ElMessageBox.confirm(
      '将清空本机记住的昵称/邮箱，并重新随机一个昵称，已填写的邮箱也会清空。继续？',
      '换一个身份',
      { type: 'warning', confirmButtonText: '换', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  switchIdentity()
}

function switchIdentity() {
  clearIdentity()
  form.nickname = randomNickname()
  form.email = ''
}

function arrayBufferToBase64(buf) {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

async function refreshCaptcha() {
  form.captcha_id = ''
  form.captcha_code = ''
  try {
    const resp = await request.get('/auth/captcha', { responseType: 'arraybuffer' })
    form.captcha_id = resp.headers['x-captcha-id'] || resp.headers['X-Captcha-Id'] || ''
    captchaSrc.value = `data:image/png;base64,${arrayBufferToBase64(resp.data)}`
  } catch {
    // 拉图失败保持空图（提交时 captcha_id 为空，后端按跳过校验处理）
    captchaSrc.value = ''
  }
}

// 点击换图：首次立即响应，500ms 内连点全部忽略（首部防抖）
const refreshCaptchaDebounced = debounce(refreshCaptcha, 500, { leading: true, trailing: false })
onBeforeUnmount(() => refreshCaptchaDebounced.cancel())

// 点发表：先验正文，再弹验证框并拉取验证码
function openCaptchaDialog() {
  if (!form.content.trim()) return ElMessage.warning('评论内容不能为空')
  captchaOpen.value = true
  refreshCaptcha()
}

async function submit() {
  const content = form.content.trim()
  if (!content) return ElMessage.warning('评论内容不能为空')
  const nickname = form.nickname.trim() || randomNickname()
  submitting.value = true
  try {
    const res = await createComment({
      post_slug: props.postSlug,
      parent_id: props.parentId,
      nickname,
      email: form.email.trim() || null,
      content,
      captcha_id: form.captcha_id,
      captcha_code: form.captcha_code.trim(),
    })
    saveIdentity(nickname, form.email.trim())
    form.content = ''
    captchaOpen.value = false
    emit('created', res.data)
  } catch {
    // 错误提示已由拦截器处理；验证码类失败留在弹框里换一张图重输
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.comment-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.form-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.nick-input {
  width: 180px;
}
.email-input {
  flex: 1;
}
/* 身份切换图标按钮：弱化存在感放在行尾，hover/tooltips 提示含义 */
.identity-btn {
  flex-shrink: 0;
  color: var(--blog-text-secondary);
  border-color: var(--blog-border);
}
.identity-btn:hover {
  color: var(--blog-primary);
  border-color: var(--blog-primary);
}
.md-hint {
  font-size: 12px;
  color: var(--blog-text-secondary);
  white-space: nowrap;
}
.spacer {
  flex: 1;
}
.captcha-box {
  display: flex;
  gap: 12px;
  align-items: center;
}
.captcha-img-wrap {
  height: 32px;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.captcha-img {
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--blog-border);
}
.captcha-placeholder {
  font-size: 12px;
  color: var(--blog-text-secondary);
}
</style>
