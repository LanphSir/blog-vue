<template>
  <el-card>
    <h3 class="title">站点配置</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基础信息" name="basic">
        <el-form label-width="140px" :model="form">
          <ConfigFieldItems :fields="basicFields" :form="form" />
          <el-form-item label="Logo 图片">
            <MediaPicker v-model="form.site_logo" tip="站点 Logo，设置后展示在导航栏左侧，未设置时显示站点名称" :preview-width="96" :preview-height="40" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="外观" name="appearance">
        <el-form label-width="140px" :model="form">
          <ConfigFieldItems :fields="appearanceFields" :form="form" />
          <el-form-item label="强调色预览">
            <span class="accent-preview" :style="{ background: form.site_accent_color || '#2563eb' }" />
            <span class="accent-hint">当前强调色：{{ form.site_accent_color || '#2563eb' }}</span>
          </el-form-item>
          <el-form-item label="页面背景">
            <div class="bg-picker">
              <button
                v-for="opt in bgOptions"
                :key="opt.key"
                type="button"
                class="bg-option"
                :class="{ selected: (form.site_background || 'none') === opt.key }"
                @click="form.site_background = opt.key"
              >
                <span class="bg-thumb" :class="'thumb-' + opt.key" />
                <span class="bg-label">{{ opt.label }}</span>
              </button>
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="侧边栏" name="sidebar">
        <div class="section-card">
          <div class="section-head">
            <span class="section-title">简介卡片</span>
            <el-switch :model-value="isOn('profile_visible')" @update:model-value="(v) => setSwitch('profile_visible', v)" />
          </div>
          <el-collapse-transition>
            <div v-show="isOn('profile_visible')">
              <el-form label-width="140px" :model="form">
                <el-form-item label="作者头像">
                  <MediaPicker v-model="form.site_avatar" tip="方形头像，支持上传或从媒体库选取" :preview-width="64" :preview-height="64" />
                </el-form-item>
                <el-form-item label="个人简介">
                  <el-input v-model="form.site_bio" type="textarea" :rows="3" placeholder="侧边简介卡片文案" />
                </el-form-item>
              </el-form>
              <div class="social-block">
                <div class="social-head">
                  <span class="social-title">社交链接（简介卡片图标）</span>
                  <el-button size="small" @click="addSocialRow">添加一行</el-button>
                </div>
                <div v-for="(row, idx) in socialRows" :key="row.id ?? 'new-' + idx" class="social-row">
                  <el-select v-model="row.platform" style="width: 130px" @change="markDirty(row)">
                    <el-option v-for="opt in PLATFORM_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
                    <el-option label="自定义" value="custom" />
                  </el-select>
                  <el-input
                    v-if="row.platform === 'custom'"
                    v-model="row.label"
                    placeholder="显示名"
                    style="width: 130px"
                    @input="markDirty(row)"
                  />
                  <el-input v-model="row.url" placeholder="https://… 或 mailto:…" class="social-url" @input="markDirty(row)" />
                  <el-tooltip :content="row.visible ? '显示中' : '已隐藏'" placement="top">
                    <el-switch v-model="row.visible" @change="markDirty(row)" />
                  </el-tooltip>
                  <el-input-number
                    v-model="row.sort_order"
                    :min="0"
                    size="small"
                    controls-position="right"
                    style="width: 96px"
                    @change="markDirty(row)"
                  />
                  <el-button link type="danger" @click="removeSocialRow(row)">删除</el-button>
                </div>
                <p class="social-hint">修改后点击底部“保存配置”统一生效；关闭的链接不会出现在前台。</p>
              </div>
            </div>
          </el-collapse-transition>
        </div>

        <div class="section-card">
          <div class="section-head">
            <span class="section-title">标签云</span>
            <el-switch
              :model-value="isOn('sidebar_tags_visible')"
              @update:model-value="(v) => setSwitch('sidebar_tags_visible', v)"
            />
          </div>
          <el-collapse-transition>
            <el-form v-show="isOn('sidebar_tags_visible')" label-width="140px" :model="form">
              <el-form-item label="标签云数量">
                <el-input v-model="form.sidebar_tag_count" placeholder="侧边标签云最多显示个数（1-30），默认 8" />
              </el-form-item>
            </el-form>
          </el-collapse-transition>
        </div>

        <div class="section-card">
          <div class="section-head">
            <span class="section-title">最近发布</span>
            <el-switch
              :model-value="isOn('sidebar_recent_visible')"
              @update:model-value="(v) => setSwitch('sidebar_recent_visible', v)"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="关于我" name="about">
        <p class="about-hint">以下内容展示在前台「关于」页的自我介绍区，支持 Markdown；留空则显示站点描述。</p>
        <MarkdownEditor v-model="form.site_about_markdown" class="about-editor" />
      </el-tab-pane>
    </el-tabs>

    <el-button type="primary" :loading="saving" class="save-btn" @click="handleSave">保存配置</el-button>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElCollapseTransition, ElMessage } from 'element-plus'
import ConfigFieldItems from '@/components/admin/ConfigFieldItems.vue'
import MediaPicker from '@/components/admin/MediaPicker.vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import {
  adminCreateSocialLink,
  adminDeleteSocialLink,
  adminGetSocialLinks,
  adminUpdateSocialLink,
  getSiteConfig,
  updateSiteConfig,
} from '@/api/site'
import { PLATFORM_OPTIONS } from '@/utils/platforms'

const basicFields = [
  { key: 'site_name', label: '站点名称', type: 'input' },
  { key: 'site_description', label: '站点描述', type: 'textarea', rows: 2 },
  { key: 'site_slogan', label: '首页副标题', type: 'input', placeholder: '显示在首页 Hero 区' },
  { key: 'site_author', label: '站点作者', type: 'input', placeholder: '文章卡片显示的默认作者' },
  { key: 'icp', label: 'ICP 备案号', type: 'input' },
  { key: 'footer_text', label: '页脚文字', type: 'input' },
]

const appearanceFields = [{ key: 'site_accent_color', label: '主题强调色', type: 'color' }]

const bgOptions = [
  { key: 'none', label: '纯色' },
  { key: 'grid', label: '蓝图网格' },
  { key: 'aurora', label: '光晕流动' },
  { key: 'dots', label: '点阵' },
  { key: 'topo', label: '等高波纹' },
  { key: 'geek', label: '极客终端' },
  { key: 'line', label: '线条变幻' },
]

const activeTab = ref('basic')
const form = reactive({})
const saving = ref(false)
const socialRows = ref([])
const removedSocialRows = ref([])

function isOn(key) {
  return form[key] !== 'false'
}

function setSwitch(key, value) {
  form[key] = String(value)
}

onMounted(async () => {
  const res = await getSiteConfig()
  for (const item of res.data) {
    form[item.key] = item.value
  }
  await reloadSocialRows()
})

async function reloadSocialRows() {
  const res = await adminGetSocialLinks()
  socialRows.value = res.data.map((item) => ({ ...item, _dirty: false }))
  removedSocialRows.value = []
}

function addSocialRow() {
  socialRows.value.push({
    id: null,
    platform: 'github',
    label: null,
    url: '',
    visible: true,
    sort_order: socialRows.value.length,
    _dirty: true,
  })
}

function markDirty(row) {
  row._dirty = true
}

function removeSocialRow(row) {
  socialRows.value = socialRows.value.filter((r) => r !== row)
  if (row.id) removedSocialRows.value.push(row)
}

function validateSocialRows() {
  for (const row of socialRows.value) {
    const url = (row.url || '').trim()
    if (!url) return '社交链接的 URL 不能为空'
    if (!/^(https?:\/\/|mailto:)/.test(url)) {
      return `「${url}」不是合法链接（需以 http(s):// 或 mailto: 开头）`
    }
    if (row.platform === 'custom' && !(row.label || '').trim()) return '自定义平台需要填写显示名'
  }
  return null
}

async function saveSocialRows() {
  for (const row of removedSocialRows.value) {
    await adminDeleteSocialLink(row.id)
  }
  for (const row of socialRows.value) {
    if (row.id && !row._dirty) continue
    const payload = {
      platform: row.platform,
      label: row.platform === 'custom' ? (row.label || '').trim() || null : null,
      url: (row.url || '').trim(),
      visible: row.visible,
      sort_order: row.sort_order || 0,
    }
    if (row.id) {
      await adminUpdateSocialLink(row.id, payload)
    } else {
      await adminCreateSocialLink(payload)
    }
  }
  await reloadSocialRows()
}

function validateConfigKeys() {
  const color = (form.site_accent_color || '').trim()
  if (color && !/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(color)) {
    return { message: '主题强调色必须是 #RGB 或 #RRGGBB 格式', tab: 'appearance' }
  }
  const tagCount = (form.sidebar_tag_count || '').trim()
  if (tagCount && (!/^\d+$/.test(tagCount) || Number(tagCount) < 1 || Number(tagCount) > 30)) {
    return { message: '标签云数量必须是 1-30 的整数', tab: 'sidebar' }
  }
  return null
}

async function handleSave() {
  const socialError = validateSocialRows()
  if (socialError) {
    ElMessage.warning(socialError)
    activeTab.value = 'sidebar'
    return
  }
  const configError = validateConfigKeys()
  if (configError) {
    ElMessage.warning(configError.message)
    activeTab.value = configError.tab
    return
  }
  saving.value = true
  try {
    const payload = Object.entries(form).map(([key, value]) => {
      if (typeof value === 'boolean') return { key, value: String(value) }
      return { key, value }
    })
    await updateSiteConfig(payload)
    await saveSocialRows()
    ElMessage.success('配置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.title {
  margin-bottom: 8px;
}

.save-btn {
  margin-top: 8px;
}

.accent-preview {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  margin-right: 10px;
  vertical-align: middle;
}

.accent-hint {
  font-size: 13px;
  color: var(--blog-text-secondary);
}

.section-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 14px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-weight: 600;
}

.section-card .el-form {
  margin-top: 14px;
}

.social-block {
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 14px;
}

.social-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.social-title {
  font-weight: 600;
}

.social-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.social-url {
  flex: 1;
  min-width: 200px;
}

.social-hint {
  font-size: 12px;
  color: var(--blog-text-secondary);
}

.bg-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.bg-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: border-color 0.15s;
}

.bg-option.selected {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px var(--el-color-primary);
}

.bg-thumb {
  width: 96px;
  height: 60px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  display: block;
}

.bg-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.thumb-none {
  background: #fafaf8;
}

.thumb-grid {
  background-color: #fafaf8;
  background-image:
    linear-gradient(rgba(37, 99, 235, 0.22) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.22) 1px, transparent 1px);
  background-size: 11px 11px;
}

.thumb-aurora {
  background-color: #fafaf8;
  background-image:
    radial-gradient(45% 55% at 25% 30%, rgba(37, 99, 235, 0.4), transparent 70%),
    radial-gradient(40% 50% at 78% 65%, rgba(37, 99, 235, 0.25), transparent 70%);
}

.thumb-dots {
  background-color: #fafaf8;
  background-image: radial-gradient(rgba(31, 35, 40, 0.4) 1px, transparent 1px);
  background-size: 10px 10px;
}

.thumb-topo {
  background-color: #fafaf8;
  background-image: repeating-radial-gradient(circle at 30% 40%, transparent 0 7px, rgba(31, 35, 40, 0.3) 7px 8px);
}

.thumb-geek {
  background-color: #0d1117;
  background-image:
    repeating-linear-gradient(180deg, transparent 0 6px, rgba(0, 230, 118, 0.35) 6px 7px),
    linear-gradient(rgba(0, 230, 118, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 230, 118, 0.16) 1px, transparent 1px);
  background-size:
    100% 24px,
    10px 10px,
    10px 10px;
}

.thumb-line {
  background-color: #fafaf8;
  background-image:
    radial-gradient(circle, rgba(37, 99, 235, 0.7) 1.2px, transparent 1.4px),
    linear-gradient(24deg, transparent 47%, rgba(37, 99, 235, 0.3) 49.5%, transparent 52%),
    linear-gradient(-33deg, transparent 47%, rgba(37, 99, 235, 0.3) 49.5%, transparent 52%);
  background-size:
    20px 15px,
    100% 100%,
    100% 100%;
}

.about-editor {
  width: 100%;
}

.about-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
