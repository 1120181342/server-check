<template>
  <div class="user-coupons-page">
    <div class="page-header">
      <h2>我的优惠券</h2>
    </div>

    <div class="coupon-tabs">
      <div 
        v-for="tab in couponTabs" 
        :key="tab.value"
        class="coupon-tab"
        :class="{ active: currentTab === tab.value }"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
        <span class="tab-count">({{ getTabCount(tab.value) }})</span>
      </div>
    </div>

    <div class="coupon-list" v-if="filteredCoupons.length > 0">
      <div 
        v-for="coupon in filteredCoupons" 
        :key="coupon.id"
        class="coupon-card"
        :class="{ expired: coupon.expired, used: coupon.used }"
      >
        <div class="coupon-left">
          <div class="coupon-value">
            <span class="currency">¥</span>
            <span class="value">{{ coupon.value }}</span>
          </div>
          <div class="coupon-condition">满{{ coupon.minAmount }}可用</div>
        </div>
        <div class="coupon-right">
          <div class="coupon-name">{{ coupon.name }}</div>
          <div class="coupon-validity">有效期至: {{ coupon.validity }}</div>
          <div class="coupon-actions">
            <el-button 
              v-if="!coupon.used && !coupon.expired"
              type="primary" 
              size="small"
              @click="useCoupon(coupon)"
            >
              立即使用
            </el-button>
            <el-tag v-else type="info" size="small">
              {{ coupon.used ? '已使用' : '已过期' }}
            </el-tag>
          </div>
        </div>
        <div class="coupon-cut left"></div>
        <div class="coupon-cut right"></div>
      </div>
    </div>

    <div class="coupon-empty" v-else>
      <el-empty :description="currentTab === 'available' ? '暂无可用优惠券' : '暂无优惠券'">
        <el-button type="primary" v-if="currentTab === 'available'" @click="goShopping">
          <el-icon><ShoppingBag /></el-icon>
          去逛逛
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const currentTab = ref('available')

const couponTabs = [
  { label: '可使用', value: 'available' },
  { label: '已使用', value: 'used' },
  { label: '已过期', value: 'expired' }
]

const coupons = ref([
  { id: 1, name: '新人专享券', value: 50, minAmount: 200, validity: '2024-12-31', used: false, expired: false },
  { id: 2, name: '满减优惠券', value: 100, minAmount: 1000, validity: '2024-06-30', used: false, expired: false },
  { id: 3, name: '限时折扣券', value: 200, minAmount: 2000, validity: '2024-03-31', used: true, expired: false },
  { id: 4, name: '节日优惠券', value: 30, minAmount: 100, validity: '2023-12-31', used: false, expired: true }
])

const filteredCoupons = computed(() => {
  switch (currentTab.value) {
    case 'available':
      return coupons.value.filter(c => !c.used && !c.expired)
    case 'used':
      return coupons.value.filter(c => c.used)
    case 'expired':
      return coupons.value.filter(c => c.expired)
    default:
      return coupons.value
  }
})

const getTabCount = (tab) => {
  switch (tab) {
    case 'available':
      return coupons.value.filter(c => !c.used && !c.expired).length
    case 'used':
      return coupons.value.filter(c => c.used).length
    case 'expired':
      return coupons.value.filter(c => c.expired).length
    default:
      return 0
  }
}

const switchTab = (tab) => {
  currentTab.value = tab
}

const useCoupon = (coupon) => {
  ElMessage.info('正在跳转到商品列表...')
  router.push('/products')
}

const goShopping = () => {
  router.push('/products')
}

onMounted(() => {
  console.time('user-coupons-onMounted')
  console.timeEnd('user-coupons-onMounted')
})
</script>

<style scoped>
.user-coupons-page {
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

.coupon-tabs {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.coupon-tab {
  position: relative;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.coupon-tab:hover {
  color: #ff6b6b;
}

.coupon-tab.active {
  color: #ff6b6b;
  font-weight: 600;
}

.coupon-tab.active::after {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 0;
  right: 0;
  height: 2px;
  background: #ff6b6b;
}

.tab-count {
  margin-left: 4px;
  color: #999;
}

.coupon-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.coupon-card {
  display: flex;
  position: relative;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
}

.coupon-card:hover:not(.expired):not(.used) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.coupon-card.expired,
.coupon-card.used {
  filter: grayscale(100%);
  opacity: 0.6;
  cursor: not-allowed;
}

.coupon-left {
  width: 120px;
  padding: 20px;
  text-align: center;
  border-right: 2px dashed rgba(255, 255, 255, 0.3);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.coupon-value {
  color: #fff;
  margin-bottom: 8px;
}

.currency {
  font-size: 16px;
  font-weight: 600;
}

.value {
  font-size: 36px;
  font-weight: 700;
}

.coupon-condition {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.coupon-right {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: #fff;
}

.coupon-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.coupon-validity {
  font-size: 12px;
  color: #999;
  margin-bottom: 15px;
}

.coupon-actions {
  display: flex;
  align-items: center;
}

.coupon-cut {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  background: #f5f5f5;
  border-radius: 50%;
}

.coupon-cut.left {
  left: 114px;
}

.coupon-cut.right {
  right: 0;
}

.coupon-empty {
  padding: 60px 0;
}
</style>
