<template>
  <view class="container">
    <view class="title">AI 智能起名</view>
    <input class="input-box" v-model="form.email" placeholder="请输入邮箱" />
    <input class="input-box" v-model="form.password" type="password" placeholder="请输入密码" />
    <button class="btn" :loading="loading" @click="handleLogin">登录</button>
    <view class="link" @click="goRegister">没有账号？去注册</view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

const form = ref({ email: '', password: '' });
const loading = ref(false);

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) return uni.showToast({ title: '请填写完整', icon: 'none' });
  loading.value = true;
  try {
    const res = await http.login(form.value);
    uni.setStorageSync('token', res.token);
    uni.setStorageSync('user', res.user);
    uni.showToast({ title: '登录成功' });
    setTimeout(() => uni.reLaunch({ url: '/pages/index/index' }), 1000); // 假设index是tab页，如果不是用redirectTo
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

const goRegister = () => uni.navigateTo({ url: '/pages/register/register' });
</script>

<style scoped>
.container { padding: 40rpx; }
.title { font-size: 48rpx; font-weight: bold; margin-bottom: 60rpx; text-align: center; }
.input-box { border-bottom: 1px solid #eee; padding: 20rpx 0; margin-bottom: 30rpx; }
.btn { background-color: #007AFF; color: white; margin-top: 40rpx; }
.link { text-align: center; color: #007AFF; margin-top: 20rpx; font-size: 28rpx; }
</style>