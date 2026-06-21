<template>
  <view class="container">
    <view class="title">账号注册</view>
    
    <input class="input-box" v-model="form.username" placeholder="请输入用户名 (至少4个字符)" />
    
    <input class="input-box" v-model="form.email" placeholder="请输入邮箱" />
    
    <view class="code-group">
      <input class="input-box code-input" v-model="form.code" placeholder="4位验证码" maxlength="4" />
      <button class="code-btn" :disabled="countdown > 0" @click="sendCode">
        {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
      </button>
    </view>
    
    <input class="input-box" v-model="form.password" type="password" placeholder="请输入密码 (至少6位)" />
    <input class="input-box" v-model="form.confirm_password" type="password" placeholder="请再次确认密码" />
    
    <button class="btn-primary" :loading="loading" @click="handleRegister">立即注册</button>
    <view class="link" @click="goLogin">已有账号？去登录</view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

// 表单数据绑定 (字段名严格对应后端 RegisterIn 的 Schema)
const form = ref({
  username: '',
  email: '',
  code: '',
  password: '',
  confirm_password: ''
});

const loading = ref(false);
const countdown = ref(0); // 倒计时秒数
let timer = null; // 定时器

// --- 发送邮箱验证码 ---
const sendCode = async () => {
  if (!form.value.email.trim()) {
    return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  }
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailReg.test(form.value.email)) {
    return uni.showToast({ title: '邮箱格式不正确', icon: 'none' });
  }

  uni.showLoading({ title: '发送中...' });
  try {
    // 调用 http.js 中封装的 getEmailCode 接口
    await http.getEmailCode(form.value.email);
    uni.showToast({ title: '验证码已发送至邮箱', icon: 'success' });
    
    // 开启 60 秒倒计时
    countdown.value = 60;
    timer = setInterval(() => {
      if (countdown.value > 0) {
        countdown.value--;
      } else {
        clearInterval(timer);
      }
    }, 1000);
  } catch (error) {
    console.error("验证码发送失败:", error);
  } finally {
    uni.hideLoading();
  }
};

// --- 执行注册 ---
const handleRegister = async () => {
  // 1. 前端基础拦截校验 (与后端 Pydantic 规则保持一致)
  if (form.value.username.length < 4) return uni.showToast({ title: '用户名至少4位', icon: 'none' });
  if (!form.value.email.trim()) return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  if (form.value.code.length !== 4) return uni.showToast({ title: '请输入4位验证码', icon: 'none' });
  if (form.value.password.length < 6) return uni.showToast({ title: '密码至少6位', icon: 'none' });
  if (form.value.password !== form.value.confirm_password) return uni.showToast({ title: '两次密码输入不一致', icon: 'none' });

  loading.value = true;
  uni.showLoading({ title: '注册中...' });

  try {
    // 2. 发起注册网络请求
    await http.register(form.value);
    
    uni.showToast({ title: '注册成功！', icon: 'success' });
    // 3. 延迟跳转回登录页
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/login/login' });
    }, 1500);
    
  } catch (error) {
    console.error("注册报错:", error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

// 跳转到登录页
const goLogin = () => {
  uni.redirectTo({ url: '/pages/login/login' });
};
</script>

<style scoped>
.container { padding: 40rpx; }
.title { font-size: 48rpx; font-weight: bold; margin-bottom: 60rpx; text-align: center; }

/* 基础输入框 */
.input-box { border-bottom: 1px solid #eee; padding: 24rpx 10rpx; margin-bottom: 30rpx; font-size: 28rpx;}

/* 验证码同行布局 */
.code-group { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30rpx;}
.code-input { flex: 1; margin-bottom: 0; /* 抵消原有的 margin-bottom */ border-bottom: 1px solid #eee; }
.code-btn { width: 220rpx; font-size: 24rpx; background: #f0f0f0; color: #333; margin-left: 20rpx; border-radius: 8rpx; padding: 0; line-height: 70rpx;}
.code-btn::after { border: none; }

/* 按钮与链接 */
.btn-primary { background-color: #007AFF; color: white; margin-top: 50rpx; border-radius: 50rpx; font-size: 32rpx;}
.link { text-align: center; color: #007AFF; margin-top: 30rpx; font-size: 28rpx; }
</style>