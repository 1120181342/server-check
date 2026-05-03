<template>
  <div class="order-detail-page">
    <div class="page-header">
      <el-button type="default" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回订单列表
      </el-button>
      <h2>订单详情</h2>
    </div>

    <div class="order-status-section" v-if="order">
      <div class="status-timeline">
        <div class="status-item" :class="{ active: order.status !== 'pending' }">
          <div class="status-dot"></div>
          <div class="status-info">
            <h4>提交订单</h4>
            <p>{{ formatTime(order.createTime) }}</p>
          </div>
        </div>
        <div class="status-line"></div>
        <div class="status-item" :class="{ active: ['paid', 'shipped', 'completed'].includes(order.status) }">
          <div class="status-dot"></div>
          <div class="status-info">
            <h4>支付成功</h4>
            <p v-if="order.payTime">{{ formatTime(order.payTime) }}</p>
            <p v-else>等待支付</p>
          </div>
        </div>
        <div class="status-line"></div>
        <div class="status-item" :class="{ active: ['shipped', 'completed'].includes(order.status) }">
          <div class="status-dot"></div>
          <div class="status-info">
            <h4>商品发货</h4>
            <p v-if="order.shipTime">{{ formatTime(order.shipTime) }}</p>
            <p v-else>等待发货</p>
          </div>
        </div>
        <div class="status-line"></div>
        <div class="status-item" :class="{ active: order.status === 'completed' }">
          <div class="status-dot"></div>
          <div class="status-info">
            <h4>确认收货</h4>
            <p v-if="order.deliverTime">{{ formatTime(order.deliverTime) }}</p>
            <p v-else>等待收货</p>
          </div>
        </div>
      </div>
      
      <div class="status-actions" v-if="order.status === 'pending'">
        <el-button type="primary" size="large" @click="payOrder">
          立即支付
        </el-button>
        <el-button size="large" @click="cancelOrder">
          取消订单
        </el-button>
      </div>
    </div>

    <div class="order-info-section" v-if="order">
      <h3 class="section-title">订单信息</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">订单编号</span>
          <span class="info-value">{{ order.id }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">订单状态</span>
          <span class="info-value">
            <el-tag :type="getStatusType(order.status)">{{ order.statusText }}</el-tag>
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatTime(order.createTime) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">支付方式</span>
          <span class="info-value">{{ order.paymentMethod?.name || '未选择' }}</span>
        </div>
      </div>
    </div>

    <div class="address-section" v-if="order">
      <h3 class="section-title">收货地址</h3>
      <div class="address-card">
        <div class="address-info">
          <div class="address-header">
            <span class="receiver">{{ order.shippingAddress?.receiverName }}</span>
            <span class="phone">{{ order.shippingAddress?.phone }}</span>
            <el-tag type="danger" size="small">默认</el-tag>
          </div>
          <div class="address-detail">
            {{ order.shippingAddress?.province }}{{ order.shippingAddress?.city }}{{ order.shippingAddress?.district }}{{ order.shippingAddress?.detail }}
          </div>
        </div>
        <div class="shipping-method">
          <el-icon><Van /></el-icon>
          <span>{{ order.shippingMethod?.name || '普通快递' }}</span>
        </div>
      </div>
    </div>

    <div class="goods-section" v-if="order">
      <h3 class="section-title">商品清单</h3>
      <div class="goods-list">
        <div v-for="item in order.items" :key="item.id" class="goods-item">
          <el-image :src="item.image" fit="cover" class="goods-image" @click="goToDetail(item.id)" />
          <div class="goods-info" @click="goToDetail(item.id)">
            <h4 class="goods-name">{{ item.name }}</h4>
            <p class="goods-specs" v-if="item.specs">{{ item.specs }}</p>
          </div>
          <div class="goods-price">
            <span>¥{{ item.discountPrice || item.price }}</span>
          </div>
          <div class="goods-quantity">
            <span>x{{ item.quantity }}</span>
          </div>
          <div class="goods-subtotal">
            <span>¥{{ (item.quantity * (item.discountPrice || item.price)).toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="summary-section" v-if="order">
      <h3 class="section-title">订单金额</h3>
      <div class="summary-list">
        <div class="summary-row">
          <span class="summary-label">商品总价</span>
          <span class="summary-value">¥{{ order.totalAmount.toFixed(2) }}</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">运费</span>
          <span class="summary-value">
            {{ order.shippingMethod?.fee > 0 ? `¥${order.shippingMethod.fee}` : '免运费' }}
          </span>
        </div>
        <div class="summary-row discount-row" v-if="order.discountAmount > 0">
          <span class="summary-label">优惠券优惠</span>
          <span class="summary-value discount">-¥{{ order.discountAmount.toFixed(2) }}</span>
        </div>
        <div class="summary-row coupon-row" v-if="order.couponCode">
          <span class="summary-label">使用优惠券</span>
          <span class="summary-value">{{ order.couponCode }}</span>
        </div>
        <div class="summary-total">
          <span class="summary-label">应付总额</span>
          <span class="summary-value total-price">¥{{ order.totalAmount.toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else>
      <el-empty description="订单不存在">
        <el-button type="primary" @click="goBack">返回订单列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOrderStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const orderStore = useOrderStore()

const order = ref(null)

const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    paid: 'primary',
    shipped: 'info',
    completed: 'success',
    cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const goBack = () => {
  router.push('/orders')
}

const goToDetail = (productId) => {
  router.push(`/products/${productId}`)
}

const payOrder = async () => {
  if (!order.value) return
  
  try {
    await ElMessageBox.confirm('确定要支付该订单吗？', '支付确认', {
      confirmButtonText: '确认支付',
      cancelButtonText: '取消',
      type: 'success'
    })
    
    console.time('pay-order-detail')
    orderStore.payOrder(order.value.id)
    order.value = orderStore.getOrderById(order.value.id)
    ElMessage.success('支付成功！')
    console.timeEnd('pay-order-detail')
  } catch {
    // 用户取消
  }
}

const cancelOrder = async () => {
  if (!order.value) return
  
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    orderStore.cancelOrder(order.value.id)
    order.value = orderStore.getOrderById(order.value.id)
    ElMessage.success('订单已取消')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  console.time('order-detail-onMounted')
  
  const orderId = route.params.id
  order.value = orderStore.getOrderById(orderId)
  
  console.timeEnd('order-detail-onMounted')
})
</script>

<style scoped>
.order-detail-page {
  min-height: 500px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
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

.order-status-section {
  padding: 30px;
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border-radius: 8px;
  margin-bottom: 20px;
}

.status-timeline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
  padding: 0 20px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
}

.status-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e0e0e0;
  border: 3px solid #f5f5f5;
  margin-bottom: 10px;
}

.status-item.active .status-dot {
  background: #ff6b6b;
  border-color: #ffe4e4;
}

.status-info {
  text-align: center;
}

.status-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #999;
  margin: 0 0 6px 0;
}

.status-item.active .status-info h4 {
  color: #333;
}

.status-info p {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.status-line {
  flex: 1;
  height: 2px;
  background: #e0e0e0;
  margin-top: 12px;
}

.status-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ffe4e4;
}

.order-info-section,
.address-section,
.goods-section,
.summary-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  font-size: 14px;
  color: #999;
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: #333;
}

.address-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.address-info {
  flex: 1;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.receiver {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.phone {
  font-size: 14px;
  color: #666;
}

.address-detail {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.shipping-method {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #fff;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
}

.shipping-method .el-icon {
  color: #ff6b6b;
}

.goods-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.goods-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.goods-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  margin-right: 15px;
  cursor: pointer;
}

.goods-info {
  flex: 2;
  cursor: pointer;
}

.goods-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 6px 0;
  line-height: 1.4;
}

.goods-name:hover {
  color: #ff6b6b;
}

.goods-specs {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.goods-price,
.goods-quantity,
.goods-subtotal {
  flex: 1;
  text-align: center;
  font-size: 14px;
  color: #333;
}

.goods-subtotal {
  font-weight: 600;
  color: #ff4757;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 20px;
  font-size: 14px;
}

.summary-label {
  color: #999;
  min-width: 80px;
  text-align: right;
}

.summary-value {
  color: #333;
  min-width: 100px;
  text-align: right;
}

.summary-value.discount {
  color: #ff4757;
}

.discount-row,
.coupon-row {
  padding-top: 10px;
  border-top: 1px dashed #f0f0f0;
}

.summary-total {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 20px;
  padding-top: 15px;
  margin-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.summary-total .summary-label {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.total-price {
  font-size: 24px;
  font-weight: 700;
  color: #ff4757;
  text-align: right;
  min-width: 120px;
}

.empty-state {
  padding: 60px 0;
}
</style>
