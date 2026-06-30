<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="eyebrow">NAMING STUDIO</text>
        <view class="hello">你好，{{ user.username || '灵感探索者' }}</view>
      </view>
      <view class="history-link" @click="goHistory">历史方案 <text>›</text></view>
    </view>

    <view class="hero-card">
      <view class="hero-copy">
        <text class="hero-kicker">让好名字，有迹可循</text>
        <text class="hero-title">AI 灵感命名室</text>
        <text class="hero-desc">从文化意象到品牌表达，生成一组真正贴合你的名字。</text>
      </view>
      <view :class="['quota-card', quota <= 0 ? 'quota-empty' : '']">
        <text class="quota-label">免费次数</text>
        <view><text class="quota-number">{{ quota }}</text><text class="quota-unit"> / 3</text></view>
        <text class="quota-note">反馈优化不扣次数</text>
      </view>
    </view>

    <view class="category-tabs">
      <view v-for="item in categories" :key="item.value" :class="['category-tab', formData.category === item.value ? 'active' : '']" @click="switchCategory(item.value)">
        <text class="tab-icon">{{ item.icon }}</text>
        <text>{{ item.label }}</text>
      </view>
    </view>

    <view v-if="formData.category === '企业名'" class="knowledge-card">
      <view class="section-heading">
        <view>
          <text class="section-title">企业知识库</text>
          <text class="section-subtitle">上传品牌资料，AI 会更懂你的业务</text>
        </view>
        <button class="ghost-button" size="mini" :loading="uploading" @click="handleUploadDocs">上传资料</button>
      </view>
      <view v-if="knowledgeFiles.length" class="file-list">
        <view v-for="file in knowledgeFiles.slice(0, 3)" :key="file.id" class="file-row">
          <view class="file-info">
            <text class="file-name">{{ file.filename }}</text>
            <text class="file-meta">{{ formatFileSize(file.file_size) }} · {{ formatDate(file.updated_at) }}</text>
          </view>
          <text :class="['status-pill', `status-${file.status}`]">{{ statusText[file.status] || file.status }}</text>
        </view>
      </view>
      <view v-else class="empty-inline">还没有资料，可上传 TXT 或 PDF 文件</view>
    </view>

    <view class="form-card">
      <view class="section-title">描述你的命名需求</view>
      <view v-if="formData.category === '人名'" class="field">
        <text class="field-label">姓氏 <text class="required">*</text></text>
        <input class="control" v-model="formData.surname" maxlength="4" placeholder="例如：林" />
      </view>
      <view v-if="formData.category === '人名'" class="field-row">
        <view class="field half">
          <text class="field-label">性别倾向</text>
          <picker mode="selector" :range="genderOptions" @change="changeGender">
            <view class="control picker-value">{{ formData.gender }} <text>⌄</text></view>
          </picker>
        </view>
        <view class="field half">
          <text class="field-label">名字字数</text>
          <picker mode="selector" :range="lengthOptions" @change="changeLength">
            <view class="control picker-value">{{ formData.length }} <text>⌄</text></view>
          </picker>
        </view>
      </view>
      <view v-else class="field">
        <text class="field-label">名字字数</text>
        <picker mode="selector" :range="lengthOptions" @change="changeLength">
          <view class="control picker-value">{{ formData.length }} <text>⌄</text></view>
        </picker>
      </view>
      <view class="field">
        <text class="field-label">风格与诉求</text>
        <textarea class="textarea-control" v-model="formData.other" maxlength="300" :placeholder="placeholderText" />
        <text class="counter">{{ (formData.other || '').length }}/300</text>
      </view>
      <view class="field last-field">
        <text class="field-label">避讳字 <text class="optional">选填，用逗号分隔</text></text>
        <input class="control" v-model="excludeText" placeholder="例如：萍，旧，宏" />
      </view>
    </view>

    <button class="generate-button" :loading="loading" :disabled="loading || quota <= 0" @click="handleGenerate">
      {{ quota <= 0 ? '免费次数已用完' : '开始生成专属名字' }}
    </button>
    <text class="generate-note">首次生成消耗 1 次额度，同一方案可免费持续优化</text>

    <view v-if="names.length" class="results">
      <view class="result-heading">
        <view>
          <text class="eyebrow">YOUR SHORTLIST</text>
          <view class="result-title">为你精选的名字</view>
        </view>
        <text class="result-count">{{ names.length }} 个候选</text>
      </view>
      <view v-for="(item, index) in names" :key="`${item.name}-${index}`" class="name-card">
        <view class="name-index">0{{ index + 1 }}</view>
        <view class="name-main">
          <view class="name-header">
            <text class="name-text">{{ item.name }}</text>
            <view v-if="item.domain" :class="['domain-pill', domainAvailable(item.domain_status) ? 'available' : 'unavailable']">
              <text class="dot"></text>{{ item.domain_status || '查询中' }}
            </view>
          </view>
          <text v-if="item.domain" class="domain-text">{{ item.domain }}</text>
          <view class="detail-line"><text class="detail-label">灵感</text><text>{{ item.reference }}</text></view>
          <view class="detail-line"><text class="detail-label">寓意</text><text>{{ item.moral }}</text></view>
        </view>
      </view>

      <view class="feedback-card">
        <text class="section-title">还想再调整？</text>
        <text class="section-subtitle">告诉 AI 哪些要保留、哪些要改变，本轮不扣次数。</text>
        <textarea class="textarea-control feedback-input" v-model="feedbackText" maxlength="300" placeholder="例如：喜欢第二个名字的意境，希望整体更简洁一些" />
        <button class="feedback-button" :loading="loading" @click="handleFeedback">按意见重新生成</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const categories = [
  { label: '人名', value: '人名', icon: '人' },
  { label: '企业名', value: '企业名', icon: '企' },
  { label: '宠物名', value: '宠物名', icon: '宠' }
];
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两个字', '三个字', '四个字以内'];
const statusText = { pending: '等待处理', processing: '学习中', completed: '已完成', failed: '处理失败' };
const user = ref(uni.getStorageSync('user') || {});
const quota = ref(Number(user.value.free_quota ?? 0));
const formData = ref({ category: '人名', surname: '', gender: '不限', length: '不限', other: '', exclude: [] });
const excludeText = ref('');
const names = ref([]);
const threadId = ref('');
const feedbackText = ref('');
const knowledgeFiles = ref([]);
const loading = ref(false);
const uploading = ref(false);
let pollTimer = null;

const placeholderText = computed(() => ({
  人名: '例如：希望温柔、有书卷气，适合女孩，名字读起来清朗自然',
  企业名: '例如：环保新材料初创公司，希望科技、可信赖，有国际感',
  宠物名: '例如：一只活泼的白色小狗，亲人、爱撒娇，名字可爱好叫'
}[formData.value.category]));

onShow(() => {
  if (!uni.getStorageSync('token')) return uni.reLaunch({ url: '/pages/login/login' });
  user.value = uni.getStorageSync('user') || {};
  quota.value = Number(user.value.free_quota ?? quota.value);
  if (formData.value.category === '企业名') loadKnowledgeFiles();
});
onUnmounted(() => clearTimeout(pollTimer));

const persistQuota = (value) => {
  quota.value = Math.max(0, value);
  user.value = { ...user.value, free_quota: quota.value };
  uni.setStorageSync('user', user.value);
};
const switchCategory = (category) => {
  formData.value.category = category;
  names.value = [];
  threadId.value = '';
  feedbackText.value = '';
  if (category === '企业名') loadKnowledgeFiles();
};
const changeGender = (event) => { formData.value.gender = genderOptions[event.detail.value]; };
const changeLength = (event) => { formData.value.length = lengthOptions[event.detail.value]; };
const goHistory = () => uni.navigateTo({ url: '/pages/history/history' });
const domainAvailable = (status = '') => /未注册|可注册|available|✅/i.test(status);
const formatDate = (value) => value ? String(value).replace('T', ' ').slice(0, 16) : '';
const formatFileSize = (bytes) => !bytes ? '未知大小' : bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;

const loadKnowledgeFiles = async () => {
  try { knowledgeFiles.value = await http.getKnowledgeFiles(0, 20); } catch (error) { console.error(error); }
};
const pollKnowledgeFiles = (round = 0) => {
  clearTimeout(pollTimer);
  if (round >= 10) return;
  pollTimer = setTimeout(async () => {
    await loadKnowledgeFiles();
    if (knowledgeFiles.value.some(file => ['pending', 'processing'].includes(file.status))) pollKnowledgeFiles(round + 1);
  }, 3000);
};
const handleUploadDocs = () => {
  uni.chooseFile({
    count: 1,
    type: 'all',
    extension: ['.txt', '.pdf'],
    success: async (res) => {
      const file = res.tempFiles?.[0];
      if (!file) return;
      uploading.value = true;
      try {
        await http.uploadKnowledge(file.path);
        uni.showToast({ title: '上传成功，后台学习中', icon: 'none' });
        await loadKnowledgeFiles();
        pollKnowledgeFiles();
      } catch (error) { console.error(error); }
      finally { uploading.value = false; }
    }
  });
};
const validateForm = () => {
  if (formData.value.category === '人名' && !formData.value.surname.trim()) {
    uni.showToast({ title: '请先填写姓氏', icon: 'none' });
    return false;
  }
  if (!formData.value.other?.trim()) {
    uni.showToast({ title: '请描述你的命名诉求', icon: 'none' });
    return false;
  }
  return true;
};
const handleGenerate = async () => {
  if (quota.value <= 0 || !validateForm()) return;
  loading.value = true;
  try {
    const payload = {
      ...formData.value,
      exclude: excludeText.value.split(/[，,]/).map(item => item.trim()).filter(Boolean)
    };
    const res = await http.generateName(payload);
    names.value = res.names || [];
    threadId.value = res.thread_id;
    feedbackText.value = '';
    persistQuota(quota.value - 1);
    setTimeout(() => uni.pageScrollTo({ selector: '.results', duration: 300 }), 100);
  } catch (error) {
    if (error?.statusCode === 403) persistQuota(0);
  } finally { loading.value = false; }
};
const handleFeedback = async () => {
  if (!feedbackText.value.trim()) return uni.showToast({ title: '请先写下修改意见', icon: 'none' });
  if (!threadId.value) return uni.showToast({ title: '当前方案缺少会话信息', icon: 'none' });
  loading.value = true;
  try {
    const res = await http.feedbackName({ thread_id: threadId.value, category: formData.value.category, feedback: feedbackText.value.trim() });
    names.value = res.names || [];
    feedbackText.value = '';
    uni.showToast({ title: '方案已更新', icon: 'success' });
  } catch (error) { console.error(error); }
  finally { loading.value = false; }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 34rpx 30rpx 100rpx; box-sizing: border-box; background: #f7f4ee; color: #24231f; }
.topbar, .section-heading, .result-heading, .name-header, .field-row { display: flex; align-items: center; justify-content: space-between; }
.eyebrow { display: block; color: #8a6f42; font-size: 18rpx; letter-spacing: 4rpx; font-weight: 700; }
.hello { margin-top: 8rpx; font-size: 32rpx; font-weight: 700; }
.history-link { color: #685d4c; font-size: 26rpx; padding: 14rpx 0; }
.history-link text { margin-left: 8rpx; font-size: 34rpx; }
.hero-card { display: flex; justify-content: space-between; gap: 24rpx; margin-top: 32rpx; padding: 38rpx 32rpx; border-radius: 28rpx; color: #fff; background: linear-gradient(135deg, #293d35 0%, #466354 100%); box-shadow: 0 18rpx 45rpx rgba(36, 59, 48, .18); }
.hero-copy { flex: 1; display: flex; flex-direction: column; }
.hero-kicker { color: #d9e5da; font-size: 22rpx; }
.hero-title { margin: 10rpx 0 16rpx; font-family: serif; font-size: 44rpx; font-weight: 700; letter-spacing: 2rpx; }
.hero-desc { max-width: 390rpx; color: rgba(255,255,255,.76); font-size: 23rpx; line-height: 1.7; }
.quota-card { width: 172rpx; min-width: 172rpx; padding: 22rpx 18rpx; box-sizing: border-box; border: 1rpx solid rgba(255,255,255,.16); border-radius: 20rpx; background: rgba(255,255,255,.1); }
.quota-empty { background: rgba(91, 42, 35, .32); }
.quota-label, .quota-note { display: block; color: rgba(255,255,255,.7); font-size: 20rpx; }
.quota-number { font-size: 54rpx; font-weight: 700; }
.quota-unit { color: rgba(255,255,255,.55); font-size: 22rpx; }
.quota-note { margin-top: 6rpx; font-size: 17rpx; }
.category-tabs { display: flex; gap: 14rpx; margin: 30rpx 0; padding: 10rpx; border-radius: 22rpx; background: #ebe5da; }
.category-tab { flex: 1; display: flex; align-items: center; justify-content: center; gap: 10rpx; padding: 19rpx 8rpx; border-radius: 16rpx; color: #746b5e; font-size: 27rpx; }
.category-tab.active { color: #2e493d; font-weight: 700; background: #fff; box-shadow: 0 5rpx 16rpx rgba(52, 45, 34, .08); }
.tab-icon { display: inline-flex; align-items: center; justify-content: center; width: 36rpx; height: 36rpx; border: 1rpx solid currentColor; border-radius: 50%; font-size: 18rpx; }
.form-card, .knowledge-card, .feedback-card { padding: 32rpx; border-radius: 24rpx; background: #fff; box-shadow: 0 8rpx 28rpx rgba(54, 47, 37, .06); }
.knowledge-card { margin-bottom: 24rpx; }
.section-title { display: block; font-size: 30rpx; font-weight: 700; }
.section-subtitle { display: block; margin-top: 7rpx; color: #938a7d; font-size: 22rpx; line-height: 1.5; }
button.ghost-button { margin: 0; padding: 0 24rpx; color: #355347; border: 1rpx solid #aebeb5; border-radius: 30rpx; background: #f5f8f5; font-size: 22rpx; }
button.ghost-button::after, button.generate-button::after, button.feedback-button::after { border: none; }
.file-list { margin-top: 24rpx; border-top: 1rpx solid #eee9e0; }
.file-row { display: flex; align-items: center; gap: 16rpx; padding: 20rpx 0; border-bottom: 1rpx solid #f2eee7; }
.file-info { flex: 1; min-width: 0; }
.file-name, .file-meta { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-name { font-size: 25rpx; }
.file-meta { margin-top: 5rpx; color: #aaa195; font-size: 19rpx; }
.status-pill, .domain-pill { flex-shrink: 0; padding: 7rpx 13rpx; border-radius: 30rpx; font-size: 19rpx; }
.status-pending, .status-processing { color: #9a6b16; background: #fff3d9; }
.status-completed { color: #357052; background: #e7f4ec; }
.status-failed { color: #a64d43; background: #fae8e5; }
.empty-inline { margin-top: 24rpx; padding: 24rpx; color: #a39a8c; border-radius: 14rpx; background: #faf8f4; text-align: center; font-size: 22rpx; }
.field { position: relative; margin-top: 30rpx; }
.field-row { gap: 20rpx; }
.half { width: calc(50% - 10rpx); }
.field-label { display: block; margin-bottom: 13rpx; color: #5c564d; font-size: 23rpx; font-weight: 600; }
.required { color: #bd6459; }.optional { margin-left: 8rpx; color: #aaa196; font-size: 19rpx; font-weight: 400; }
.control, .textarea-control { width: 100%; box-sizing: border-box; color: #282620; border: 1rpx solid #e4ded4; border-radius: 14rpx; background: #fbfaf7; font-size: 26rpx; }
.control { height: 86rpx; padding: 0 24rpx; }
.picker-value { display: flex; align-items: center; justify-content: space-between; }
.textarea-control { height: 190rpx; padding: 22rpx 24rpx; line-height: 1.65; }
.counter { position: absolute; right: 18rpx; bottom: 14rpx; color: #b3aa9f; font-size: 18rpx; }
.last-field { margin-bottom: 2rpx; }
button.generate-button { margin-top: 28rpx; height: 96rpx; line-height: 96rpx; color: #fff; border-radius: 18rpx; background: #c37b52; box-shadow: 0 12rpx 26rpx rgba(173, 96, 55, .2); font-size: 29rpx; font-weight: 700; }
button.generate-button[disabled] { color: #fff; background: #bdb5a8; box-shadow: none; }
.generate-note { display: block; margin-top: 15rpx; color: #9d9488; text-align: center; font-size: 20rpx; }
.results { margin-top: 64rpx; }
.result-title { margin-top: 8rpx; font-family: serif; font-size: 40rpx; font-weight: 700; }
.result-count { color: #8e8478; font-size: 22rpx; }
.name-card { position: relative; display: flex; gap: 22rpx; margin-top: 22rpx; padding: 30rpx; overflow: hidden; border-radius: 22rpx; background: #fff; box-shadow: 0 8rpx 25rpx rgba(54, 47, 37, .06); }
.name-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 7rpx; background: #708f7e; }
.name-index { padding-top: 8rpx; color: #b9ad9c; font-family: serif; font-size: 22rpx; }
.name-main { flex: 1; min-width: 0; }
.name-text { font-family: serif; font-size: 43rpx; font-weight: 700; letter-spacing: 3rpx; }
.domain-pill { color: #9b564a; background: #fae9e4; }
.domain-pill.available { color: #357052; background: #e6f3eb; }
.dot { display: inline-block; width: 9rpx; height: 9rpx; margin-right: 8rpx; border-radius: 50%; background: currentColor; }
.domain-text { display: block; margin: 8rpx 0 22rpx; color: #8b7861; font-size: 21rpx; }
.detail-line { display: flex; gap: 18rpx; margin-top: 13rpx; color: #716a60; font-size: 24rpx; line-height: 1.65; }
.detail-label { flex-shrink: 0; color: #3e4e46; font-weight: 700; }
.feedback-card { margin-top: 30rpx; background: #efe9de; box-shadow: none; }
.feedback-input { margin-top: 22rpx; background: rgba(255,255,255,.75); }
button.feedback-button { margin-top: 20rpx; color: #fff; border-radius: 14rpx; background: #344f43; font-size: 26rpx; }
</style>
