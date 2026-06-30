<template>
  <view class="page">
    <view class="intro">
      <text class="eyebrow">NAMING ARCHIVE</text>
      <text class="title">我的灵感档案</text>
      <text class="subtitle">每一次命名探索，都值得被好好保存。</text>
    </view>

    <view v-if="loading && !records.length" class="state-card">正在整理你的方案…</view>
    <view v-else-if="!records.length" class="empty-card">
      <view class="empty-mark">名</view>
      <text class="empty-title">还没有起名记录</text>
      <text class="empty-text">创建第一份方案后，它会出现在这里。</text>
      <button class="primary-button" @click="goCreate">去创建方案</button>
    </view>
    <view v-else class="record-list">
      <view v-for="record in records" :key="record.id" class="record-card" @click="openDetail(record.id)">
        <view :class="['category-mark', `mark-${record.category}`]">{{ categoryIcon[record.category] }}</view>
        <view class="record-content">
          <view class="record-top">
            <text class="record-title">{{ record.title || `${record.category}方案` }}</text>
            <text class="arrow">›</text>
          </view>
          <view class="meta-row">
            <text class="category-pill">{{ record.category }}</text>
            <text>{{ formatDate(record.updated_at) }}</text>
          </view>
        </view>
        <view class="delete-hit" @click.stop="confirmDelete(record)">删除</view>
      </view>
      <view v-if="records.length >= pageSize" class="load-more" @click="loadMore">{{ loading ? '加载中…' : '加载更多' }}</view>
      <view v-else class="list-end">— 已经到底了 —</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const records = ref([]);
const loading = ref(false);
const pageSize = 20;
const categoryIcon = { 人名: '人', 企业名: '企', 宠物名: '宠' };

onShow(() => {
  if (!uni.getStorageSync('token')) return uni.reLaunch({ url: '/pages/login/login' });
  loadRecords(true);
});
onPullDownRefresh(async () => {
  await loadRecords(true);
  uni.stopPullDownRefresh();
});

const loadRecords = async (reset = false) => {
  if (loading.value) return;
  loading.value = true;
  try {
    const skip = reset ? 0 : records.value.length;
    const data = await http.getNameRecords(skip, pageSize);
    records.value = reset ? data : [...records.value, ...data];
  } catch (error) { console.error(error); }
  finally { loading.value = false; }
};
const loadMore = () => loadRecords(false);
const formatDate = (value) => value ? String(value).replace('T', ' ').slice(0, 16) : '';
const openDetail = (id) => uni.navigateTo({ url: `/pages/history/detail?id=${id}` });
const goCreate = () => uni.navigateBack({ delta: 1 });
const confirmDelete = (record) => {
  uni.showModal({
    title: '删除这份方案？',
    content: `“${record.title || record.category + '方案'}”删除后将无法继续优化。`,
    confirmColor: '#a75549',
    success: async ({ confirm }) => {
      if (!confirm) return;
      try {
        await http.deleteNameRecord(record.id);
        records.value = records.value.filter(item => item.id !== record.id);
        uni.showToast({ title: '已删除', icon: 'success' });
      } catch (error) { console.error(error); }
    }
  });
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 46rpx 30rpx 90rpx; box-sizing: border-box; color: #28251f; background: #f7f4ee; }
.intro { padding: 12rpx 8rpx 34rpx; }
.eyebrow { color: #8a6f42; font-size: 18rpx; letter-spacing: 4rpx; font-weight: 700; }
.title, .subtitle { display: block; }
.title { margin-top: 12rpx; font-family: serif; font-size: 46rpx; font-weight: 700; }
.subtitle { margin-top: 12rpx; color: #91877a; font-size: 23rpx; }
.record-list { display: flex; flex-direction: column; gap: 18rpx; }
.record-card { display: flex; align-items: center; gap: 22rpx; padding: 26rpx 24rpx; border-radius: 20rpx; background: #fff; box-shadow: 0 8rpx 25rpx rgba(54,47,37,.055); }
.category-mark { display: flex; align-items: center; justify-content: center; width: 76rpx; height: 76rpx; flex-shrink: 0; color: #fff; border-radius: 22rpx; background: #587668; font-size: 26rpx; font-weight: 700; }
.mark-企业名 { background: #aa7655; }.mark-宠物名 { background: #8b7568; }
.record-content { flex: 1; min-width: 0; }
.record-top, .meta-row { display: flex; align-items: center; }
.record-top { justify-content: space-between; }
.record-title { overflow: hidden; color: #2c2a25; text-overflow: ellipsis; white-space: nowrap; font-family: serif; font-size: 31rpx; font-weight: 700; }
.arrow { color: #b4aa9e; font-size: 38rpx; }
.meta-row { gap: 15rpx; margin-top: 12rpx; color: #a49a8d; font-size: 20rpx; }
.category-pill { padding: 4rpx 12rpx; color: #536b60; border-radius: 20rpx; background: #eaf1ed; }
.delete-hit { align-self: stretch; display: flex; align-items: flex-end; padding: 0 2rpx 4rpx; color: #b29d92; font-size: 20rpx; }
.state-card, .empty-card { padding: 70rpx 35rpx; color: #948b7e; border-radius: 24rpx; background: #fff; text-align: center; }
.empty-card { display: flex; align-items: center; flex-direction: column; }
.empty-mark { display: flex; align-items: center; justify-content: center; width: 110rpx; height: 110rpx; color: #536e61; border: 1rpx solid #aabbb1; border-radius: 50%; background: #edf3ef; font-family: serif; font-size: 42rpx; }
.empty-title { margin-top: 28rpx; color: #34312b; font-size: 31rpx; font-weight: 700; }
.empty-text { margin-top: 12rpx; font-size: 23rpx; }
button.primary-button { width: 310rpx; margin-top: 32rpx; color: #fff; border-radius: 40rpx; background: #3e594d; font-size: 25rpx; }
.load-more, .list-end { padding: 26rpx; color: #887f74; text-align: center; font-size: 22rpx; }
.list-end { color: #b0a79a; }
</style>
