<template>
  <div class="user-info-page">
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <div class="user-stats">
      <div class="stat-card">
        <div class="stat-icon orders">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ orderStats.total }}</div>
          <div class="stat-label">全部订单</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon pending">
          <el-icon :size="28"><Wallet /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ orderStats.pending }}</div>
          <div class="stat-label">待付款</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon paid">
          <el-icon :size="28"><Van /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ orderStats.paid }}</div>
          <div class="stat-label">待收货</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon coupons">
          <el-icon :size="28"><Ticket /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ couponStats.available }}</div>
          <div class="stat-label">可用优惠券</div>
        </div>
      </div>
    </div>

    <div class="user-content">
      <div class="info-section">
        <h3 class="section-title">基本信息</h3>
        <el-form :model="userForm" label-width="100px" class="info-form">
          <el-form-item label="用户名">
            <el-input v-model="userForm.username" disabled />
          </el-form-item>
          <el-form-item label="昵称">
            <el-input v-model="userForm.nickname" placeholder="请输入昵称" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="userForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="userForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="性别">
            <el-radio-group v-model="userForm.gender">
              <el-radio value="male">男</el-radio>
              <el-radio value="female">女</el-radio>
              <el-radio value="secret">保密</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="生日">
            <el-date-picker
              v-model="userForm.birthday"
              type="date"
              placeholder="选择生日"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveProfile">保存修改</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="quick-actions">
        <h3 class="section-title">快捷入口</h3>
        <div class="action-grid">
          <router-link to="/orders" class="action-item">
            <el-icon :size="32"><Document /></el-icon>
            <span>我的订单</span>
          </router-link>
          <router-link to="/user/address" class="action-item">
            <el-icon :size="32"><Location /></el-icon>
            <span>收货地址</span>
          </router-link>
          <router-link to="/user/coupons" class="action-item">
            <el-icon :size="32"><Ticket /></el-icon>
            <span>我的优惠券</span>
          </router-link>
          <router-link to="/cart" class="action-item">
            <el-icon :size="32"><ShoppingCart /></el-icon>
            <span>购物车</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore, useOrderStore } from '@/store'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const orderStore = useOrderStore()

const userForm = reactive({
  username: userStore.userName || 'user123',
  nickname: userStore.userName || '',
  phone: userStore.userInfo?.phone || '138****0000',
  email: userStore.userInfo?.email || '',
  gender: userStore.userInfo?.gender || 'secret',
  birthday: userStore.userInfo?.birthday || null
})

const orderStats = computed(() => ({
  total: orderStore.orders.length,
  pending: orderStore.getOrdersByStatus('pending').length,
  paid: orderStore.getOrdersByStatus('paid').length + orderStore.getOrdersByStatus('shipped').length
}))

const couponStats = computed(() => ({
  available: 2
}))

const saveProfile = () => {
  console.time('save-profile')
  userStore.setUserInfo({
    ...userStore.userInfo,
    ...userForm
  })
  ElMessage.success('保存成功')
  console.timeEnd('save-profile')
}

onMounted(() => {
  console.time('user-info-onMounted')
  console.timeEnd('user-info-onMounted')
})
</script>

<style scoped>
.user-info-page {
  min-height: 500px;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.user-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: linear-gradient(135deg, #fafafa 0%, #fff 100%);
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.orders {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.stat-icon.paid {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.stat-icon.coupons {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #fff;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.user-content {
  display: flex;
  gap: 30px;
}

.info-section {
  flex: 1;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.info-form {
  max-width: 400px;
}

.quick-actions {
  width: 320px;
  flex-shrink: 0;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 25px 15px;
  background: #fafafa;
  border-radius: 8px;
  text-decoration: none;
  color: #666;
  transition: all 0.2s;
}

.action-item:hover {
  background: #fff5f5;
  color: #ff6b6b;
  transform: translateY(-2px);
}

.action-item .el-icon {
  color: #999;
  transition: color 0.2s;
}

.action-item:hover .el-icon {
  color: #ff6b6b;
}

.action-item span {
  font-size: 14px;
}
</style>
