<template>
  <view class="page">
    <view class="header">
      <view><text class="eyebrow">ADMIN CONSOLE</text><text class="title">用户管理</text></view>
      <button class="logout" size="mini" @click="goDashboard">控制台</button>
    </view>

    <view class="search-bar">
      <input v-model="keyword" confirm-type="search" placeholder="搜索邮箱或用户名" @confirm="search" />
      <button size="mini" @click="search">搜索</button>
    </view>

    <view v-if="loading && !users.length" class="state">正在加载用户…</view>
    <view v-else-if="!users.length" class="state">没有找到用户</view>
    <view v-for="item in users" :key="item.id" class="user-card">
      <view class="user-head">
        <view class="identity">
          <text class="avatar">{{ (item.username || item.email || '?').slice(0, 1).toUpperCase() }}</text>
          <view><text class="username">{{ item.username }}</text><text class="email">{{ item.email }}</text></view>
        </view>
        <view class="badges"><text v-if="item.is_admin" class="badge admin">管理员</text><text :class="['badge', item.is_frozen ? 'frozen' : 'normal']">{{ item.is_frozen ? '已冻结' : '正常' }}</text></view>
      </view>
      <view class="meta"><text>ID {{ item.id }}</text><text>剩余额度 {{ item.free_quota }}</text></view>
      <view class="actions">
        <button size="mini" @click="openEdit(item)">编辑</button>
        <button size="mini" @click="openPassword(item)">重置密码</button>
        <button v-if="!isSelf(item)" size="mini" :class="item.is_frozen ? 'success' : 'warning'" @click="toggleFreeze(item)">{{ item.is_frozen ? '解冻' : '冻结' }}</button>
        <button v-if="!isSelf(item)" size="mini" class="danger" @click="removeUser(item)">删除</button>
      </view>
    </view>

    <view v-if="total > pageSize" class="pagination">
      <button size="mini" :disabled="page <= 1" @click="changePage(-1)">上一页</button>
      <text>{{ page }} / {{ totalPages }}</text>
      <button size="mini" :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
    </view>

    <view v-if="dialog" class="mask" @click.self="closeDialog">
      <view class="dialog">
        <text class="dialog-title">{{ dialog === 'edit' ? '编辑用户' : '重置密码' }}</text>
        <template v-if="dialog === 'edit'">
          <text class="label">用户名</text><input v-model="editForm.username" class="control" maxlength="50" />
          <text class="label">邮箱</text><input v-model="editForm.email" class="control" />
          <text class="label">免费额度</text><input v-model="editForm.free_quota" class="control" type="number" />
          <view class="switch-row"><text>管理员权限</text><switch :checked="editForm.is_admin" :disabled="isSelf(selected)" color="#355347" @change="editForm.is_admin = $event.detail.value" /></view>
        </template>
        <template v-else>
          <text class="label">新密码（6–50 位）</text><input v-model="password" class="control" type="password" maxlength="50" placeholder="请输入新密码" />
        </template>
        <view class="dialog-actions"><button @click="closeDialog">取消</button><button class="primary" :loading="saving" @click="submitDialog">保存</button></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const currentUser = ref(uni.getStorageSync('user') || {});
const users = ref([]);
const keyword = ref('');
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const loading = ref(false);
const saving = ref(false);
const dialog = ref('');
const selected = ref(null);
const password = ref('');
const editForm = ref({});
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));
const isSelf = (item) => Number(item?.id) === Number(currentUser.value.id);

const loadUsers = async () => {
  loading.value = true;
  try {
    const res = await http.getAdminUsers({ page: page.value, page_size: pageSize, keyword: keyword.value.trim() });
    users.value = res.items || [];
    total.value = Number(res.total || 0);
  } catch (error) {
    if ([401, 403].includes(error?.statusCode)) uni.reLaunch({ url: '/pages/login/login' });
  } finally { loading.value = false; uni.stopPullDownRefresh(); }
};
onShow(() => {
  currentUser.value = uni.getStorageSync('user') || {};
  if (!uni.getStorageSync('token') || !currentUser.value.is_admin) return uni.reLaunch({ url: '/pages/login/login' });
  loadUsers();
});
onPullDownRefresh(loadUsers);
const search = () => { page.value = 1; loadUsers(); };
const changePage = (offset) => { page.value += offset; loadUsers(); uni.pageScrollTo({ scrollTop: 0 }); };
const openEdit = (item) => { selected.value = item; editForm.value = { username: item.username, email: item.email, free_quota: String(item.free_quota), is_admin: item.is_admin }; dialog.value = 'edit'; };
const openPassword = (item) => { selected.value = item; password.value = ''; dialog.value = 'password'; };
const closeDialog = () => { if (!saving.value) dialog.value = ''; };
const submitDialog = async () => {
  if (dialog.value === 'password' && (password.value.length < 6 || password.value.length > 50)) return uni.showToast({ title: '密码长度需为 6–50 位', icon: 'none' });
  const quota = Number(editForm.value.free_quota);
  if (dialog.value === 'edit' && (!editForm.value.username?.trim() || !editForm.value.email?.trim() || !Number.isInteger(quota) || quota < 0)) return uni.showToast({ title: '请检查用户名、邮箱和额度', icon: 'none' });
  saving.value = true;
  try {
    if (dialog.value === 'edit') await http.updateAdminUser(selected.value.id, { username: editForm.value.username.trim(), email: editForm.value.email.trim(), free_quota: quota, is_admin: editForm.value.is_admin });
    else await http.resetAdminUserPassword(selected.value.id, password.value);
    uni.showToast({ title: dialog.value === 'edit' ? '用户已更新' : '密码已重置', icon: 'success' });
    dialog.value = '';
    await loadUsers();
  } finally { saving.value = false; }
};
const toggleFreeze = (item) => uni.showModal({ title: item.is_frozen ? '确认解冻' : '确认冻结', content: `${item.is_frozen ? '解冻' : '冻结'}用户 ${item.username}？`, success: async ({ confirm }) => { if (!confirm) return; await http.setAdminUserFrozen(item.id, !item.is_frozen); uni.showToast({ title: item.is_frozen ? '已解冻' : '已冻结' }); loadUsers(); } });
const removeUser = (item) => uni.showModal({ title: '删除用户', content: `将永久删除 ${item.username}，此操作不可恢复。`, confirmColor: '#b84c43', success: async ({ confirm }) => { if (!confirm) return; await http.deleteAdminUser(item.id); uni.showToast({ title: '用户已删除' }); if (users.value.length === 1 && page.value > 1) page.value--; loadUsers(); } });
const goDashboard = () => uni.redirectTo({ url: '/pages/admin/index' });
</script>

<style scoped>
.page { min-height: 100vh; padding: 34rpx 30rpx 90rpx; box-sizing: border-box; color: #26231f; background: #f7f4ee; }
.header,.user-head,.identity,.badges,.actions,.pagination,.dialog-actions,.switch-row { display: flex; align-items: center; }
.header,.user-head,.switch-row { justify-content: space-between; }.eyebrow { display: block; color: #8a6f42; font-size: 18rpx; letter-spacing: 4rpx; }.title { display: block; margin-top: 8rpx; font-size: 42rpx; font-weight: 700; }
button.logout { margin: 0; color: #6b6257; background: transparent; }.search-bar { display: flex; gap: 16rpx; margin: 30rpx 0; padding: 14rpx 14rpx 14rpx 24rpx; border-radius: 18rpx; background: #fff; }.search-bar input { flex: 1; height: 64rpx; }.search-bar button { margin: 0; color: #fff; background: #355347; }
.state { padding: 100rpx 0; color: #91887c; text-align: center; }.user-card { margin-bottom: 20rpx; padding: 28rpx; border-radius: 22rpx; background: #fff; box-shadow: 0 8rpx 24rpx rgba(54,47,37,.06); }.identity { min-width: 0; gap: 18rpx; }.avatar { display: flex; align-items: center; justify-content: center; width: 70rpx; height: 70rpx; flex-shrink: 0; color: #fff; border-radius: 50%; background: #526f60; font-weight: 700; }.username,.email { display: block; }.username { font-size: 28rpx; font-weight: 700; }.email { max-width: 330rpx; margin-top: 5rpx; overflow: hidden; color: #8e8579; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }.badges { justify-content: flex-end; flex-wrap: wrap; gap: 8rpx; }.badge { padding: 6rpx 12rpx; border-radius: 20rpx; font-size: 18rpx; }.admin { color: #73571f; background: #f5e9c8; }.normal { color: #317052; background: #e4f2e9; }.frozen { color: #a34b43; background: #f8e5e2; }
.meta { display: flex; gap: 30rpx; margin: 24rpx 0 18rpx; padding-top: 18rpx; color: #81786c; border-top: 1rpx solid #eee9e1; font-size: 21rpx; }.actions { flex-wrap: wrap; gap: 12rpx; }.actions button { margin: 0; color: #554d43; background: #f2eee7; font-size: 21rpx; }.actions .warning { color: #986317; background: #fff0d2; }.actions .success { color: #317052; background: #e4f2e9; }.actions .danger { color: #a34b43; background: #f8e5e2; }.pagination { justify-content: center; gap: 24rpx; margin-top: 32rpx; color: #81786c; }.pagination button { margin: 0; }
.mask { position: fixed; inset: 0; z-index: 20; display: flex; align-items: center; justify-content: center; padding: 30rpx; background: rgba(28,27,24,.52); }.dialog { width: 100%; padding: 34rpx; box-sizing: border-box; border-radius: 24rpx; background: #fff; }.dialog-title { display: block; margin-bottom: 28rpx; font-size: 32rpx; font-weight: 700; }.label { display: block; margin: 22rpx 0 10rpx; color: #645d53; font-size: 22rpx; }.control { height: 78rpx; padding: 0 20rpx; box-sizing: border-box; border: 1rpx solid #ddd6cb; border-radius: 12rpx; background: #fbfaf7; }.switch-row { margin-top: 25rpx; }.dialog-actions { gap: 16rpx; margin-top: 34rpx; }.dialog-actions button { flex: 1; }.dialog-actions .primary { color: #fff; background: #355347; }
</style>
