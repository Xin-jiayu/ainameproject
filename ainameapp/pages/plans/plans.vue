<template>
  <view class="page">
    <view class="intro"><text class="eyebrow">MEMBERSHIP</text><text class="title">套餐与订单</text><text class="desc">选择套餐后创建订单，通过支付宝沙箱完成演示支付。</text></view>
    <view v-if="loading" class="empty">正在读取套餐…</view>
    <view v-for="plan in products" :key="plan.id" class="plan">
      <view class="head"><view><text class="tag">{{ typeText(plan.entitlement_type) }}</text><text class="name">{{ plan.name }}</text></view><view><text class="currency">¥</text><text class="price">{{ money(plan.price) }}</text></view></view>
      <text class="description">{{ plan.description || '购买后权益实时到账' }}</text><text class="benefit">✓ {{ plan.entitlement_amount }} {{ typeText(plan.entitlement_type) }}</text>
      <button :loading="buying===plan.id" @click="buy(plan)">创建订单</button>
    </view>
    <view class="section-head"><text>我的订单</text><text @click="load">刷新</text></view>
    <view v-if="!orders.length && !loading" class="empty">暂无订单</view>
    <view v-for="item in orders" :key="item.id" class="order">
      <view class="order-top"><view><text class="order-name">{{ item.extra_data?.product_name || item.product_type }}</text><text class="muted">{{ item.order_no }} · {{ formatDate(item.created_at) }}</text></view><text class="amount">¥{{ money(item.amount) }}</text></view>
      <view class="order-bottom"><text :class="['status', item.pay_status]">{{ statusText(item.pay_status) }}</text><view><button v-if="item.pay_status==='pending'" size="mini" @click="close(item)">取消</button><button v-if="item.pay_status==='pending'" size="mini" class="pay" @click="pay(item)">沙箱支付</button></view></view>
    </view>
  </view>
</template>
<script setup>
import { ref } from 'vue'; import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'; import http from '@/http/http.js';
const products=ref([]),orders=ref([]),loading=ref(false),buying=ref(null);
const load=async()=>{loading.value=true;try{const [p,o]=await Promise.all([http.getProducts(),http.getOrders({page:1,page_size:50})]);products.value=p||[];orders.value=o.items||[];}finally{loading.value=false;uni.stopPullDownRefresh();}};
onShow(load);onPullDownRefresh(load);
const buy=async(plan)=>{buying.value=plan.id;try{const order=await http.createOrder(plan.id,`web-${Date.now()}-${plan.id}`);orders.value=[order,...orders.value];uni.showToast({title:'订单已创建',icon:'success'});}finally{buying.value=null;}};
const pay=item=>uni.showModal({title:'支付宝沙箱支付',content:`确认模拟支付 ¥${money(item.amount)}？`,success:async({confirm})=>{if(!confirm)return;await http.payOrder(item.id);await load();uni.showToast({title:'支付成功，权益已到账',icon:'none'});}});
const close=item=>uni.showModal({title:'取消订单',content:'确定关闭这笔待支付订单？',success:async({confirm})=>{if(confirm){await http.closeOrder(item.id);await load();}}});
const money=v=>Number(v||0).toFixed(2);const formatDate=v=>String(v||'').replace('T',' ').slice(0,16);const typeText=v=>({name_generate:'次生成额度',report_generate:'份报告权益',visual_generate:'次视觉权益'}[v]||v||'平台权益');const statusText=v=>({pending:'待支付',paid:'已支付',failed:'支付失败',closed:'已关闭',refunded:'已退款'}[v]||v);
</script>
<style scoped>
.page{min-height:100vh;padding:36rpx 30rpx 90rpx;box-sizing:border-box;color:#292620;background:#f7f4ee}.eyebrow,.title,.desc,.tag,.name,.description,.benefit,.muted,.order-name{display:block}.eyebrow{color:#8a6f42;font-size:17rpx;letter-spacing:4rpx}.title{margin-top:10rpx;font-family:serif;font-size:43rpx;font-weight:700}.desc{margin-top:10rpx;color:#948a7d;font-size:21rpx}.plan,.order,.empty{margin-top:20rpx;padding:27rpx;border-radius:21rpx;background:#fff}.head,.order-top,.order-bottom,.section-head{display:flex;align-items:center;justify-content:space-between}.tag{color:#9b6a2b;font-size:18rpx}.name{margin-top:6rpx;font-size:30rpx;font-weight:700}.currency{font-size:20rpx}.price{font-size:42rpx;font-weight:700}.description{margin-top:16rpx;color:#81786d;font-size:21rpx}.benefit{margin-top:14rpx;color:#476456;font-size:21rpx}.plan button{margin-top:20rpx;color:#fff;background:#3d594c}.section-head{margin:38rpx 4rpx 10rpx;font-size:28rpx;font-weight:700}.section-head text:last-child{color:#687e72;font-size:20rpx}.empty{text-align:center;color:#968d82}.order-name{font-size:24rpx;font-weight:700}.muted{margin-top:6rpx;color:#9a9186;font-size:17rpx}.amount{font-size:25rpx;font-weight:700}.order-bottom{margin-top:18rpx}.status{padding:7rpx 13rpx;border-radius:20rpx;background:#eee9e1;color:#756d63;font-size:18rpx}.status.paid{color:#347050;background:#e4f2e9}.status.failed{color:#a44f45;background:#fae7e3}.order-bottom button{display:inline-block;margin:0 0 0 10rpx}.order-bottom .pay{color:#fff;background:#3d594c}
</style>
