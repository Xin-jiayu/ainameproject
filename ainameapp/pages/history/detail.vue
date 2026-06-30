<template>
  <view class="page">
    <view v-if="loading && !record" class="loading-state">正在打开方案…</view>
    <template v-else-if="record">
      <view class="summary-card">
        <view class="summary-top">
          <text class="category-pill">{{ record.category }}</text>
          <text class="date">{{ formatDate(record.created_at) }}</text>
        </view>
        <text class="title">{{ record.title || `${record.category}命名方案` }}</text>
        <text class="summary-text">{{ inputSummary }}</text>
      </view>

      <view class="section-head">
        <view><text class="eyebrow">LATEST VERSION</text><text class="section-title">当前候选方案</text></view>
        <text class="count">{{ names.length }} 个名字</text>
      </view>
      <view v-for="(item, index) in names" :key="`${item.name}-${index}`" class="name-card">
        <view class="name-top">
          <text class="number">0{{ index + 1 }}</text>
          <text class="name">{{ item.name }}</text>
          <text v-if="item.domain_status" :class="['domain-status', domainAvailable(item.domain_status) ? 'available' : '']">{{ item.domain_status }}</text>
        </view>
        <text v-if="item.domain" class="domain">{{ item.domain }}</text>
        <view class="detail"><text>灵感</text><view>{{ item.reference }}</view></view>
        <view class="detail"><text>寓意</text><view>{{ item.moral }}</view></view>
      </view>

      <view v-if="record.feedbacks?.length" class="timeline-section">
        <view class="section-title">优化记录</view>
        <view v-for="(item, index) in record.feedbacks" :key="item.id" class="timeline-item">
          <view class="timeline-dot"></view>
          <view class="timeline-content">
            <text class="timeline-label">第 {{ index + 1 }} 次优化 · {{ formatDate(item.created_at) }}</text>
            <text class="timeline-text">{{ item.feedback_text }}</text>
          </view>
        </view>
      </view>

      <view class="continue-card">
        <text class="section-title">继续打磨这个方案</text>
        <text class="hint">基于原有上下文优化，不消耗免费次数</text>
        <textarea class="feedback-input" v-model="feedback" maxlength="300" placeholder="写下你希望保留和调整的部分…" />
        <button class="continue-button" :loading="submitting" @click="submitFeedback">继续优化</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const recordId = ref(null);
const record = ref(null);
const loading = ref(false);
const submitting = ref(false);
const feedback = ref('');
const names = computed(() => normalizeNames(record.value?.result_data));
const inputSummary = computed(() => {
  const input = record.value?.input_data || {};
  const parts = [input.surname ? `姓氏：${input.surname}` : '', input.gender && input.gender !== '不限' ? input.gender : '', input.length && input.length !== '不限' ? input.length : '', input.other || ''];
  return parts.filter(Boolean).join(' · ') || '未填写额外需求';
});

onLoad((options) => {
  if (!uni.getStorageSync('token')) return uni.reLaunch({ url: '/pages/login/login' });
  recordId.value = Number(options.id);
  loadDetail();
});
const normalizeNames = (data) => {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.names)) return data.names;
  return [];
};
const loadDetail = async () => {
  if (!recordId.value) return;
  loading.value = true;
  try { record.value = await http.getNameRecord(recordId.value); }
  catch (error) { console.error(error); }
  finally { loading.value = false; }
};
const formatDate = (value) => value ? String(value).replace('T', ' ').slice(0, 16) : '';
const domainAvailable = (status = '') => /未注册|可注册|available|✅/i.test(status);
const submitFeedback = async () => {
  if (!feedback.value.trim()) return uni.showToast({ title: '请先写下修改意见', icon: 'none' });
  submitting.value = true;
  try {
    await http.feedbackName({ thread_id: record.value.thread_id, category: record.value.category, feedback: feedback.value.trim() });
    feedback.value = '';
    await loadDetail();
    uni.showToast({ title: '方案已更新', icon: 'success' });
    uni.pageScrollTo({ scrollTop: 0, duration: 300 });
  } catch (error) { console.error(error); }
  finally { submitting.value = false; }
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 32rpx 30rpx 90rpx; box-sizing: border-box; color: #28251f; background: #f7f4ee; }
.loading-state { padding: 90rpx 20rpx; color: #91887c; text-align: center; }
.summary-card { padding: 34rpx; color: #fff; border-radius: 26rpx; background: linear-gradient(135deg, #30483e, #5a7567); box-shadow: 0 15rpx 35rpx rgba(43,65,55,.16); }
.summary-top, .name-top, .section-head { display: flex; align-items: center; }
.summary-top, .section-head { justify-content: space-between; }
.category-pill { padding: 6rpx 16rpx; color: #e6eee9; border: 1rpx solid rgba(255,255,255,.25); border-radius: 30rpx; background: rgba(255,255,255,.1); font-size: 20rpx; }
.date { color: rgba(255,255,255,.63); font-size: 20rpx; }
.title { display: block; margin-top: 25rpx; font-family: serif; font-size: 43rpx; font-weight: 700; }
.summary-text { display: block; margin-top: 15rpx; color: rgba(255,255,255,.72); font-size: 23rpx; line-height: 1.7; }
.section-head { margin: 48rpx 5rpx 20rpx; }
.eyebrow { display: block; color: #8a6f42; font-size: 17rpx; letter-spacing: 3rpx; font-weight: 700; }
.section-title { display: block; margin-top: 7rpx; font-family: serif; font-size: 33rpx; font-weight: 700; }
.count { color: #948a7d; font-size: 21rpx; }
.name-card { margin-top: 18rpx; padding: 30rpx; border-radius: 21rpx; background: #fff; box-shadow: 0 8rpx 24rpx rgba(54,47,37,.055); }
.name-top { gap: 18rpx; }
.number { color: #b5aa9c; font-size: 20rpx; }
.name { flex: 1; font-family: serif; font-size: 39rpx; font-weight: 700; letter-spacing: 2rpx; }
.domain-status { padding: 6rpx 13rpx; color: #9b564a; border-radius: 30rpx; background: #fae9e4; font-size: 18rpx; }
.domain-status.available { color: #357052; background: #e6f3eb; }
.domain { display: block; margin: 6rpx 0 20rpx 52rpx; color: #8d7961; font-size: 20rpx; }
.detail { display: flex; gap: 20rpx; margin-top: 13rpx; color: #70695f; font-size: 23rpx; line-height: 1.65; }
.detail > text { flex-shrink: 0; color: #3d5449; font-weight: 700; }
.timeline-section, .continue-card { margin-top: 30rpx; padding: 30rpx; border-radius: 22rpx; background: #fff; }
.timeline-section > .section-title, .continue-card > .section-title { margin: 0; }
.timeline-item { position: relative; display: flex; gap: 20rpx; padding: 25rpx 0 5rpx; }
.timeline-item:not(:last-child)::after { content: ''; position: absolute; left: 7rpx; top: 42rpx; bottom: -8rpx; width: 1rpx; background: #d9d2c7; }
.timeline-dot { z-index: 1; width: 15rpx; height: 15rpx; margin-top: 8rpx; flex-shrink: 0; border-radius: 50%; background: #668172; }
.timeline-label, .timeline-text { display: block; }
.timeline-label { color: #a0978b; font-size: 19rpx; }
.timeline-text { margin-top: 8rpx; color: #544f47; font-size: 23rpx; line-height: 1.55; }
.continue-card { background: #eee8dd; }
.hint { display: block; margin-top: 8rpx; color: #908679; font-size: 21rpx; }
.feedback-input { width: 100%; height: 180rpx; margin-top: 22rpx; padding: 21rpx; box-sizing: border-box; border: 1rpx solid #ddd5c8; border-radius: 14rpx; background: rgba(255,255,255,.75); font-size: 25rpx; }
button.continue-button { margin-top: 20rpx; color: #fff; border-radius: 14rpx; background: #3b564a; font-size: 26rpx; }
button.continue-button::after { border: none; }
</style>
