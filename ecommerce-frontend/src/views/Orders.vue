<template>
  <div class="orders-layout">
    <div class="container">
      <div class="user-sidebar">
        <div class="user-info-card">
          <el-avatar :size="64" class="user-avatar">
            {{ userStore.userName?.charAt(0) || 'U' }}
          </el-avatar>
          <div class="user-name">{{ userStore.userName }}</div>
          <div class="user-level">
            <el-tag type="warning" size="small">VIP会员</el-tag>
          </div>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="user-menu"
          router
        >
          <el-menu-item index="/orders">
            <el-icon><Document /></el-icon>
            <span>我的订单</span>
          </el-menu-item>
          <el-menu-item index="/user">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
          <el-menu-item index="/user/address">
            <el-icon><Location /></el-icon>
            <span>收货地址</span>
          </el-menu-item>
          <el-menu-item index="/user/coupons">
            <el-icon><Ticket /></el-icon>
            <span>我的优惠券</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="user-main">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store'

const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/orders')) return '/orders'
  if (path.startsWith('/user/address')) return '/user/address'
  if (path.startsWith('/user/coupons')) return '/user/coupons'
  return '/user'
})
</script>

<style scoped>
.orders-layout {
  padding: 20px 0;
  min-height: calc(100vh - 200px);
}

.container {
  display: flex;
  gap: 20px;
}

.user-sidebar {
  width: 220px;
  flex-shrink: 0;
}

.user-info-card {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  margin-bottom: 20px;
}

.user-avatar {
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
  font-size: 28px;
  font-weight: 600;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
}

.user-menu {
  background: #fff;
  border-radius: 8px;
  border: none;
}

.user-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

.user-menu :deep(.el-menu-item.is-active) {
  color: #ff6b6b;
  background: #fff5f5;
}

.user-main {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}
</style>
