<template>
  <view class="container">
    <view class="tabs">
      <view v-for="item in categories" :key="item" 
            :class="['tab', formData.category === item ? 'active' : '']" 
            @click="switchCategory(item)">
        {{ item }}
      </view>
    </view>

    <view class="upload-section" v-if="formData.category === '企业名'">
      <view class="upload-tip">有企业命名规范？让 AI 学习你的专属标准</view>
      <button size="mini" @click="handleUploadDocs">上传专属知识库 (TXT/PDF)</button>
    </view>

    <view class="form-group">
      <input v-if="formData.category === '人名'" class="input-box" v-model="formData.surname" placeholder="请输入姓氏 (如: 张)" />
      
      <picker v-if="formData.category === '人名'" mode="selector" :range="genderOptions" @change="e => formData.gender = genderOptions[e.detail.value]">
        <view class="input-box">性别倾向：{{ formData.gender }}</view>
      </picker>

      <picker mode="selector" :range="lengthOptions" @change="e => formData.length = lengthOptions[e.detail.value]">
        <view class="input-box">字数要求：{{ formData.length }}</view>
      </picker>

      <textarea class="textarea-box" v-model="formData.other" placeholder="核心诉求"></textarea>
    </view>

    <button class="btn-primary" :loading="loading" @click="handleGenerate">开始智能起名</button>

    <view class="result-box" v-if="names.length > 0">
      <view class="result-title">为您生成的专属方案：</view>
      <view class="name-card" v-for="(item, index) in names" :key="index">
        <view class="name-header">
          <text class="name-text">{{ item.name }}</text>
          <text v-if="item.domain" :class="['domain-tag', item.domain_status.includes('✅') ? 'domain-success' : 'domain-fail']">
            {{ item.domain }} ({{ item.domain_status }})
          </text>
        </view>
        <view class="name-detail"><text class="label">出处：</text>{{ item.reference }}</view>
        <view class="name-detail"><text class="label">寓意：</text>{{ item.moral }}</view>
      </view>

      <view class="feedback-box">
        <textarea class="textarea-box" v-model="feedbackText" placeholder="对结果不满意？请输入修改意见 (如: 保留第二个名字，其他换成带水字旁的)"></textarea>
        <button class="btn-secondary" :loading="loading" @click="handleFeedback">基于意见重新生成</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

// --- 状态定义 ---
const categories = ['人名', '企业名', '宠物名'];
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两字', '多字'];

const formData = ref({
  category: '人名',
  surname: '',
  gender: '不限',
  length: '不限',
  other: '',
  exclude: []
});

const loading = ref(false);
const names = ref([]);
const threadId = ref(''); // 核心：保存上下文记忆的ID
const feedbackText = ref('');

// --- 方法定义 ---
const switchCategory = (cat) => {
  formData.value.category = cat;
  names.value = []; // 切换场景清空历史
  threadId.value = '';
};

// 上传专属知识库 (RAG)
// 上传专属知识库 (RAG) - 兼容 Web 端
const handleUploadDocs = () => {
  uni.chooseFile({
    count: 1, // 只允许上传1个文件
    type: 'all', // Web 端建议写 all，通过 extension 限制后缀
    extension: ['.txt', '.pdf'], // 限制文件格式
    success: async (res) => {
      // 拿到本地文件路径
      const tempFilePath = res.tempFiles[0].path;
      uni.showLoading({ title: '知识库解析中...' });
      
      try {
        // 调用 http.js 里的文件上传封装接口
        await http.uploadKnowledge(tempFilePath);
        uni.showToast({ title: '知识库学习完成！', icon: 'success' });
      } catch (error) {
        console.error("上传失败:", error);
        // 错误提示已在 http.js 拦截器里处理过，这里可省略或做额外逻辑
      } finally {
        uni.hideLoading();
      }
    },
    fail: (err) => {
      // 如果用户中途取消了选择，这里会捕获到，不用报错
      console.log("用户取消选择文件或选择失败", err);
    }
  });
};

// 首次生成 (创建 Thread)
const handleGenerate = async () => {
  if (formData.value.category === '人名' && !formData.value.surname.trim()) {
    return uni.showToast({ title: '人名必须填写姓氏', icon: 'none' });
  }

  loading.value = true;
  uni.showLoading({ title: 'AI思考中...' });
  
  try {
    const res = await http.generateName(formData.value);
    names.value = res.names;
    threadId.value = res.thread_id; // 保存后端返回的记忆指针
    feedbackText.value = ''; // 清空上一轮反馈
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

// 多轮微调 (带着 Thread_id 访问)
const handleFeedback = async () => {
  if (!feedbackText.value.trim()) {
    return uni.showToast({ title: '请输入修改意见', icon: 'none' });
  }
  
  loading.value = true;
  uni.showLoading({ title: '微调修改中...' });
  
  try {
    const res = await http.feedbackName({
      thread_id: threadId.value,
      category: formData.value.category,
      feedback: feedbackText.value
    });
    names.value = res.names;
    // threadId 保持不变，实现无限轮次对话
    feedbackText.value = ''; 
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};
</script>

<style scoped>
.container { padding: 30rpx; background-color: #f5f7fa; min-height: 100vh; }
/* Tabs 样式 */
.tabs { display: flex; justify-content: space-around; background: #fff; padding: 20rpx; border-radius: 16rpx; margin-bottom: 30rpx; }
.tab { font-size: 30rpx; color: #666; padding: 10rpx 30rpx; }
.tab.active { color: #007AFF; font-weight: bold; border-bottom: 4rpx solid #007AFF; }

/* 知识库上传 */
.upload-section { background: #e6f7ff; padding: 20rpx; border-radius: 12rpx; margin-bottom: 30rpx; text-align: center; }
.upload-tip { font-size: 24rpx; color: #007AFF; margin-bottom: 10rpx; }

/* 表单样式 */
.form-group { background: #fff; padding: 20rpx; border-radius: 16rpx; margin-bottom: 30rpx; }
.input-box { border-bottom: 1px solid #eee; padding: 24rpx 10rpx; font-size: 28rpx; }
.textarea-box { width: 100%; height: 160rpx; background: #f9f9f9; padding: 20rpx; box-sizing: border-box; border-radius: 8rpx; font-size: 28rpx; margin-top: 20rpx;}

/* 按钮 */
.btn-primary { background: #007AFF; color: #fff; border-radius: 50rpx; margin-bottom: 40rpx; }
.btn-secondary { background: #ff9800; color: #fff; border-radius: 50rpx; margin-top: 20rpx; }

/* 结果卡片 */
.result-box { margin-top: 40rpx; }
.result-title { font-size: 32rpx; font-weight: bold; margin-bottom: 20rpx; }
.name-card { background: #fff; padding: 30rpx; border-radius: 16rpx; margin-bottom: 24rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.name-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.name-text { font-size: 40rpx; font-weight: bold; color: #333; }

/* 域名状态标签 */
.domain-tag { font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 30rpx; }
.domain-success { background: #e8f5e9; color: #4caf50; }
.domain-fail { background: #ffebee; color: #f44336; }

.name-detail { font-size: 26rpx; color: #666; line-height: 1.6; margin-bottom: 8rpx; }
.label { font-weight: bold; color: #333; }
.feedback-box { margin-top: 40rpx; background: #fff; padding: 30rpx; border-radius: 16rpx; }
</style>