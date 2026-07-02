<template>
  <view class="page">
    <view class="hero"><text class="eyebrow">BRAND KNOWLEDGE</text><text class="title">企业知识库</text><text class="subtitle">管理品牌资料，处理完成后会用于企业命名。</text><button :loading="uploading" @click="upload">上传 TXT / PDF</button></view>
    <view class="summary"><view><text class="num">{{ files.length }}</text><text>全部文件</text></view><view><text class="num">{{ completedCount }}</text><text>已完成</text></view><view><text class="num">{{ activeCount }}</text><text>处理中</text></view></view>
    <view v-if="loading && !files.length" class="state">正在读取文件…</view>
    <view v-else-if="!files.length" class="state">暂无资料，上传一份品牌介绍开始吧。</view>
    <view v-for="file in files" :key="file.id" class="file-card">
      <view class="file-head"><view class="file-icon">{{ file.file_type?.toUpperCase() || 'FILE' }}</view><view class="file-info"><text class="file-name">{{ file.filename }}</text><text class="meta">{{ formatSize(file.file_size) }} · {{ formatDate(file.updated_at) }}</text></view><text :class="['status', `status-${file.status}`]">{{ statusText[file.status] || file.status }}</text></view>
      <view v-if="file.status === 'failed'" class="error">失败原因：{{ file.error_message || '处理异常，请重新上传文件' }}</view>
      <view class="progress"><view :class="['bar', `bar-${file.status}`]"></view></view>
      <view class="tips">{{ statusTip[file.status] || '状态同步中' }}</view>
    </view>
    <text class="footnote">当前后端仅提供上传、列表和详情接口；删除与失败重试将在接口开放后接入。</text>
  </view>
</template>
<script setup>
import { computed, onUnmounted, ref } from 'vue';
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
const files = ref([]); const loading = ref(false); const uploading = ref(false); let timer;
const statusText = { pending: '等待处理', processing: '学习中', completed: '已完成', failed: '失败' };
const statusTip = { pending: '已进入处理队列', processing: '正在提取内容并建立知识索引', completed: '可用于企业命名', failed: '可重新上传该文件进行处理' };
const completedCount = computed(() => files.value.filter(item => item.status === 'completed').length);
const activeCount = computed(() => files.value.filter(item => ['pending','processing'].includes(item.status)).length);
onShow(() => { if (!uni.getStorageSync('token')) return uni.reLaunch({ url: '/pages/login/login' }); load(); });
onPullDownRefresh(async () => { await load(); uni.stopPullDownRefresh(); }); onUnmounted(() => clearTimeout(timer));
const load = async () => { loading.value = true; try { files.value = await http.getKnowledgeFiles(0, 100); if (activeCount.value) { clearTimeout(timer); timer = setTimeout(load, 4000); } } catch (e) { console.error(e); } finally { loading.value = false; } };
const upload = () => uni.chooseFile({ count: 1, type: 'all', extension: ['.txt','.pdf'], success: async ({ tempFiles }) => { const file = tempFiles?.[0]; if (!file) return; uploading.value = true; try { await http.uploadKnowledge(file.path); uni.showToast({ title: '上传成功，等待处理', icon: 'none' }); await load(); } finally { uploading.value = false; } } });
const formatDate = value => value ? String(value).replace('T',' ').slice(0,16) : '';
const formatSize = value => !value ? '未知大小' : value < 1048576 ? `${(value/1024).toFixed(1)} KB` : `${(value/1048576).toFixed(1)} MB`;
</script>
<style scoped>
.page{min-height:100vh;padding:32rpx 30rpx 90rpx;box-sizing:border-box;color:#292720;background:#f7f4ee}.hero{padding:34rpx;color:#fff;border-radius:26rpx;background:linear-gradient(135deg,#30483e,#60796b)}.eyebrow,.title,.subtitle{display:block}.eyebrow{color:#d8e2dc;font-size:17rpx;letter-spacing:3rpx}.title{margin-top:12rpx;font-family:serif;font-size:43rpx;font-weight:700}.subtitle{margin-top:10rpx;color:rgba(255,255,255,.7);font-size:22rpx}.hero button{margin:26rpx 0 0;width:260rpx;color:#365044;border-radius:40rpx;background:#fff;font-size:23rpx}.summary{display:flex;justify-content:space-around;margin:22rpx 0;padding:24rpx;border-radius:20rpx;background:#fff}.summary view{text-align:center;color:#988e81;font-size:19rpx}.num{display:block;color:#395247;font-size:34rpx;font-weight:700}.file-card,.state{margin-top:18rpx;padding:26rpx;border-radius:20rpx;background:#fff}.state{color:#968d81;text-align:center}.file-head{display:flex;align-items:center;gap:18rpx}.file-icon{display:flex;align-items:center;justify-content:center;width:70rpx;height:70rpx;color:#537064;border-radius:16rpx;background:#eaf1ed;font-size:17rpx;font-weight:700}.file-info{flex:1;min-width:0}.file-name,.meta{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.file-name{font-size:25rpx;font-weight:600}.meta,.tips{margin-top:6rpx;color:#a0978b;font-size:18rpx}.status{padding:7rpx 13rpx;border-radius:20rpx;font-size:18rpx}.status-completed{color:#357052;background:#e7f4ec}.status-pending,.status-processing{color:#956b1e;background:#fff2d7}.status-failed{color:#a64d43;background:#fae8e5}.progress{height:7rpx;margin-top:20rpx;overflow:hidden;border-radius:7rpx;background:#eeeae3}.bar{height:100%;width:20%;background:#c5a660}.bar-processing{width:65%;background:#c5a660}.bar-completed{width:100%;background:#5d826f}.bar-failed{width:100%;background:#b96359}.error{margin-top:18rpx;padding:16rpx;color:#985047;border-radius:12rpx;background:#fff2f0;font-size:20rpx}.footnote{display:block;margin-top:28rpx;color:#a49a8d;text-align:center;font-size:19rpx;line-height:1.6}
</style>
