<template>
  <div class="comment-form" :class="{ compact }">
    <div class="form-row">
      <el-input v-model="form.nickname" maxlength="30" placeholder="昵称" class="nick-input" />
      <el-input v-model="form.email" maxlength="100" placeholder="邮箱（选填，不会公开显示）" class="email-input" />
    </div>
    <el-input
      v-model="form.content"
      type="textarea"
      :rows="compact ? 2 : 4"
      maxlength="500"
      show-word-limit
      :placeholder="placeholder"
    />
    <div class="form-row captcha-row">
      <el-input v-model="form.captcha_code" maxlength="4" placeholder="验证码" class="captcha-input" />
      <img
        v-if="captchaSrc"
        :src="captchaSrc"
        class="captcha-img"
        alt="验证码，点击刷新"
        title="点击刷新"
        @click="refreshCaptcha"
      />
      <span class="spacer" />
      <el-button v-if="compact" size="small" @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" :size="compact ? 'small' : 'default'" :loading="submitting" @click="submit">
        {{ submitText }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
// 发表评论/回复共用的表单：昵称预填随机「用户_xxxx」、验证码图点击刷新、
// 提交成功后由父组件决定刷新策略。验证码复用登录同款接口与"留空跳过"规则。
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/index'
import { createComment } from '@/api/comments'
import { randomNickname } from '@/utils/commentAvatar'

const props = defineProps({
  postSlug: { type: String, required: true },
  parentId: { type: Number, default: null },
  compact: { type: Boolean, default: false },
  placeholder: { type: String, default: '说点什么吧，友善的评论会让人心情愉快～' },
  submitText: { type: String, default: '发表评论' },
})
const emit = defineEmits(['created', 'cancel'])

const form = reactive({
  nickname: randomNickname(),
  email: '',
  content: '',
  captcha_id: '',
  captcha_code: '',
})
const captchaSrc = ref('')
const submitting = ref(false)

function arrayBufferToBase64(buf) {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

async function refreshCaptcha() {
  try {
    const resp = await request.get('/auth/captcha', { responseType: 'arraybuffer' })
    form.captcha_id = resp.headers['x-captcha-id'] || resp.headers['X-Captcha-Id'] || ''
    captchaSrc.value = `data:image/png;base64,${arrayBufferToBase64(resp.data)}`
  } catch {
    captchaSrc.value = ''
  }
}

async function submit() {
  const content = form.content.trim()
  if (!content) return ElMessage.warning('评论内容不能为空')
  submitting.value = true
  try {
    const res = await createComment({
      post_slug: props.postSlug,
      parent_id: props.parentId,
      nickname: form.nickname.trim() || randomNickname(),
      email: form.email.trim() || null,
      content,
      captcha_id: form.captcha_id,
      captcha_code: form.captcha_code.trim(),
    })
    form.content = ''
    form.captcha_code = ''
    await refreshCaptcha()
    emit('created', res.data)
  } catch {
    // 错误提示已由拦截器处理；验证码类失败需要换一张图
    form.captcha_code = ''
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

onMounted(refreshCaptcha)
defineExpose({ refreshCaptcha })
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
.captcha-input {
  width: 140px;
}
.captcha-img {
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--blog-border);
  cursor: pointer;
}
.spacer {
  flex: 1;
}
</style>
