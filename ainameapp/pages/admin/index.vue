<template>
  <view class="page">
    <view class="hero">
      <view class="hero-top">
        <view><text class="eyebrow">ADMIN CONSOLE</text><text class="title">管理控制台</text></view>
        <button size="mini" @click="logout">退出</button>
      </view>
      <text class="welcome">你好，{{ currentUser.username || '管理员' }}</text>
      <text class="hint">查看平台用户概况并处理账号管理任务。</text>
    </view>

    <view class="section-head"><text>用户概览</text><text class="refresh" @click="loadOverview">{{ loading ? '刷新中…' : '刷新' }}</text></view>
    <view class="stats">
      <view class="stat-card primary"><text class="stat-number">{{ total }}</text><text class="stat-label">注册用户</text></view>
      <view class="stat-card"><text class="stat-number">{{ normalCount }}</text><text class="stat-label">正常账号</text></view>
      <view class="stat-card danger"><text class="stat-number">{{ frozenCount }}</text><text class="stat-label">冻结账号</text></view>
      <view class="stat-card gold"><text class="stat-number">{{ adminCount }}</text><text class="stat-label">管理员</text></view>
    </view>
    <text v-if="total > sampledUsers.length" class="sample-note">状态统计基于最近 {{ sampledUsers.length }} 位用户，总用户数以“注册用户”为准。</text>

    <view class="section-head"><text>管理功能</text></view>
    <view class="menu-card" @click="goUsers">
      <view class="menu-icon">人</view>
      <view class="menu-content"><text class="menu-title">用户管理</text><text class="menu-desc">搜索、编辑额度、冻结账号、重置密码</text></view>
      <text class="arrow">›</text>
    </view>
    <view class="menu-card" @click="goFrontend">
      <view class="menu-icon green">名</view>
      <view class="menu-content"><text class="menu-title">进入业务前台</text><text class="menu-desc">检查起名、历史记录和知识库体验</text></view>
      <text class="arrow">›</text>
    </view>

    <view class="section-head"><text>第三阶段演示数据</text></view>
    <view class="phase-stats"><view><text>{{ orderCount }}</text><text>模拟订单</text></view><view><text>{{ reportCount }}</text><text>报告任务</text></view><view><text>{{ visualCount }}</text><text>视觉任务</text></view></view>
    <view class="menu-card" @click="goPlans"><view class="menu-icon gold">单</view><view class="menu-content"><text class="menu-title">套餐与订单演示</text><text class="menu-desc">查看模拟购买及权益到账流程</text></view><text class="arrow">›</text></view>

    <view class="notice">
      <text class="notice-title">管理员安全提示</text>
      <text>请勿共享管理员账号；删除用户不可恢复，冻结和权限调整前请确认目标账号。</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { getOrders, getReports, getVisuals } from '@/services/phase3Mock.js';

const currentUser = ref(uni.getStorageSync('user') || {});
const sampledUsers = ref([]);
const total = ref(0);
const loading = ref(false);
const orderCount = ref(0); const reportCount = ref(0); const visualCount = ref(0);
const frozenCount = computed(() => sampledUsers.value.filter(item => item.is_frozen).length);
const adminCount = computed(() => sampledUsers.value.filter(item => item.is_admin).length);
const normalCount = computed(() => sampledUsers.value.filter(item => !item.is_frozen).length);

const ensureAdmin = () => {
  currentUser.value = uni.getStorageSync('user') || {};
  if (!uni.getStorageSync('token') || !currentUser.value.is_admin) {
    uni.reLaunch({ url: '/pages/login/login' });
    return false;
  }
  return true;
};
const loadOverview = async () => {
  if (loading.value || !ensureAdmin()) return;
  loading.value = true;
  try {
    const res = await http.getAdminUsers({ page: 1, page_size: 100 });
    sampledUsers.value = res.items || [];
    total.value = Number(res.total || 0);
  } catch (error) {
    if ([401, 403].includes(error?.statusCode)) uni.reLaunch({ url: '/pages/login/login' });
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
};
onShow(() => { if (ensureAdmin()) { orderCount.value=getOrders().length; reportCount.value=getReports().length; visualCount.value=getVisuals().length; loadOverview(); } });
onPullDownRefresh(loadOverview);
const goUsers = () => uni.navigateTo({ url: '/pages/admin/users' });
const goFrontend = () => uni.navigateTo({ url: '/pages/index/index' });
const goPlans = () => uni.navigateTo({ url: '/pages/plans/plans' });
const logout = () => uni.showModal({
  title: '退出管理员端',
  content: '确定退出当前账号？',
  success: ({ confirm }) => {
    if (!confirm) return;
    uni.removeStorageSync('token');
    uni.removeStorageSync('user');
    uni.reLaunch({ url: '/pages/login/login' });
  }
});
</script>

<style scoped>
.page { min-height: 100vh; padding: 32rpx 30rpx 90rpx; box-sizing: border-box; color: #28251f; background: #f5f2ec; }
.hero { padding: 34rpx; color: #fff; border-radius: 28rpx; background: linear-gradient(135deg,#243a31,#587363); box-shadow: 0 16rpx 38rpx rgba(37,58,49,.2); }
.hero-top,.section-head,.menu-card { display: flex; align-items: center; }.hero-top,.section-head { justify-content: space-between; }.hero button { margin: 0; color: #355146; background: #fff; }
.eyebrow,.title,.welcome,.hint { display: block; }.eyebrow { color: #d4dfd8; font-size: 17rpx; letter-spacing: 4rpx; }.title { margin-top: 8rpx; font-family: serif; font-size: 42rpx; font-weight: 700; }.welcome { margin-top: 32rpx; font-size: 27rpx; font-weight: 700; }.hint { margin-top: 8rpx; color: rgba(255,255,255,.67); font-size: 21rpx; }
.section-head { margin: 38rpx 5rpx 18rpx; font-size: 28rpx; font-weight: 700; }.refresh { color: #78877e; font-size: 21rpx; font-weight: 400; }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }.stat-card { padding: 25rpx; border-radius: 20rpx; background: #fff; box-shadow: 0 7rpx 20rpx rgba(54,47,37,.05); }.stat-number,.stat-label { display: block; }.stat-number { color: #3f5c4e; font-size: 43rpx; font-weight: 700; }.stat-label { margin-top: 7rpx; color: #91887c; font-size: 20rpx; }.stat-card.danger .stat-number { color: #aa544a; }.stat-card.gold .stat-number { color: #9b7332; }.sample-note { display: block; margin-top: 12rpx; color: #a0978a; font-size: 18rpx; }
.menu-card { gap: 20rpx; margin-bottom: 16rpx; padding: 25rpx; border-radius: 20rpx; background: #fff; }.menu-icon { display: flex; align-items: center; justify-content: center; width: 70rpx; height: 70rpx; flex-shrink: 0; color: #fff; border-radius: 18rpx; background: #a66c49; font-weight: 700; }.menu-icon.green { background: #526f60; }.menu-content { flex: 1; min-width: 0; }.menu-title,.menu-desc { display: block; }.menu-title { font-size: 27rpx; font-weight: 700; }.menu-desc { margin-top: 6rpx; color: #938a7e; font-size: 20rpx; }.arrow { color: #b5ab9e; font-size: 42rpx; }
.menu-icon.gold{background:#a58245}.phase-stats{display:flex;gap:12rpx;margin-bottom:16rpx}.phase-stats view{flex:1;padding:20rpx 8rpx;border-radius:16rpx;background:#fff;text-align:center}.phase-stats text{display:block}.phase-stats text:first-child{color:#426052;font-size:31rpx;font-weight:700}.phase-stats text:last-child{margin-top:4rpx;color:#978e82;font-size:17rpx}
.notice { margin-top: 30rpx; padding: 25rpx; color: #7d7062; border: 1rpx solid #e3d4bc; border-radius: 18rpx; background: #fff8e9; font-size: 20rpx; line-height: 1.65; }.notice-title { display: block; margin-bottom: 7rpx; color: #7f5c27; font-weight: 700; }
</style>
