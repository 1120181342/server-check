<template>
  <div class="order-list-page">
    <div class="page-header">
      <h2>我的订单</h2>
    </div>

    <div class="order-tabs">
      <div 
        v-for="tab in orderTabs" 
        :key="tab.value"
        class="order-tab"
        :class="{ active: currentTab === tab.value }"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
        <span v-if="tab.count > 0" class="tab-count">({{ tab.count }})</span>
      </div>
    </div>

    <div class="order-list" v-if="filteredOrders.length > 0">
      <div v-for="order in filteredOrders" :key="order.id" class="order-card">
        <div class="order-header">
          <div class="order-info">
            <span class="order-id">订单号: {{ order.id }}</span>
            <span class="order-time">{{ formatTime(order.createTime) }}</span>
          </div>
          <div class="order-status">
            <el-tag :type="getStatusType(order.status)" size="large">
              {{ order.statusText }}
            </el-tag>
          </div>
        </div>

        <div class="order-items">
          <div v-for="(item, index) in order.items" :key="index" class="order-item">
            <el-image :src="item.image" fit="cover" class="item-image" @click="goToDetail(item.id)" />
            <div class="item-info" @click="goToDetail(item.id)">
              <h4 class="item-name">{{ item.name }}</h4>
              <p class="item-specs" v-if="item.specs">{{ item.specs }}</p>
            </div>
            <div class="item-price">
              <span>¥{{ item.discountPrice || item.price }}</span>
            </div>
            <div class="item-quantity">
              <span>x{{ item.quantity }}</span>
            </div>
          </div>
          <div v-if="order.items.length > 3" class="more-items">
            共 {{ order.items.length }} 件商品
          </div>
        </div>

        <div class="order-footer">
          <div class="order-total">
            <span>订单金额：</span>
            <span class="total-price">¥{{ order.totalAmount.toFixed(2) }}</span>
          </div>
          <div class="order-actions">
            <router-link :to="`/orders/${order.id}`" class="action-link">
              查看详情
            </router-link>
            
            <el-button 
              v-if="order.status === 'pending'"
              type="primary" 
              size="small"
              @click="payOrder(order)"
            >
              立即支付
            </el-button>
            <el-button 
              v-if="order.status === 'pending'"
              type="default" 
              size="small"
              @click="cancelOrder(order)"
            >
              取消订单
            </el-button>
            
            <el-button 
              v-if="order.status === 'paid'"
              type="primary" 
              size="small"
            >
              提醒发货
            </el-button>
            
            <el-button 
              v-if="order.status === 'shipped'"
              type="primary" 
              size="small"
              @click="confirmReceive(order)"
            >
              确认收货
            </el-button>
            
            <el-button 
              v-if="order.status === 'completed'"
              type="default" 
              size="small"
            >
              评价
            </el-button>
            
            <el-button 
              v-if="order.status === 'completed'"
              type="default" 
              size="small"
            >
              再次购买
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="order-empty" v-else>
      <el-empty description="暂无订单">
        <el-button type="primary" @click="goShopping">
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
import { useOrderStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const orderStore = useOrderStore()

const currentTab = ref('all')

const orderTabs = computed(() => [
  { label: '全部', value: 'all', count: orderStore.orders.length },
  { label: '待付款', value: 'pending', count: orderStore.getOrdersByStatus('pending').length },
  { label: '待发货', value: 'paid', count: orderStore.getOrdersByStatus('paid').length },
  { label: '待收货', value: 'shipped', count: orderStore.getOrdersByStatus('shipped').length },
  { label: '已完成', value: 'completed', count: orderStore.getOrdersByStatus('completed').length }
])

const filteredOrders = computed(() => {
  if (currentTab.value === 'all') {
    return orderStore.orders
  }
  return orderStore.getOrdersByStatus(currentTab.value)
})

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
    minute: '2-digit'
  })
}

const switchTab = (tab) => {
  currentTab.value = tab
}

const goToDetail = (productId) => {
  router.push(`/products/${productId}`)
}

const goShopping = () => {
  router.push('/products')
}

const payOrder = async (order) => {
  try {
    await ElMessageBox.confirm('确定要支付该订单吗？', '支付确认', {
      confirmButtonText: '确认支付',
      cancelButtonText: '取消',
      type: 'success'
    })
    
    console.time('pay-order')
    orderStore.payOrder(order.id)
    ElMessage.success('支付成功！')
    console.timeEnd('pay-order')
  } catch {
    // 用户取消
  }
}

const cancelOrder = async (order) => {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    orderStore.cancelOrder(order.id)
    ElMessage.success('订单已取消')
  } catch {
    // 用户取消
  }
}

const confirmReceive = async (order) => {
  try {
    await ElMessageBox.confirm('确认已收到商品吗？', '提示', {
      confirmButtonText: '确认收货',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    orderStore.confirmReceive(order.id)
    ElMessage.success('确认收货成功！')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  console.time('order-list-onMounted')
  
  if (orderStore.orders.length === 0) {
    const mockItems = [
      {
        id: 1,
        name: 'Apple iPhone 15 Pro Max',
        price: 9999,
        discountPrice: 9599,
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPhone%2015%20Pro%20Max%20smartphone%20product%20photo&image_size=square_hd',
        quantity: 1,
        specs: '钛金属黑 / 256GB'
      },
      {
        id: 2,
        name: 'AirPods Pro 2',
        price: 1899,
        discountPrice: 1599,
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=AirPods%20Pro%202%20wireless%20earbuds%20product%20photo&image_size=square_hd',
        quantity: 1,
        specs: 'USB-C充电盒'
      }
    ]
    
    orderStore.createOrder({
      items: mockItems,
      totalAmount: 11198,
      shippingAddress: {
        receiverName: '张三',
        phone: '13800138000',
        province: '北京市',
        city: '东城区',
        district: '东城区',
        detail: '王府井大街88号'
      },
      paymentMethod: { id: 1, name: '支付宝' },
      shippingMethod: { id: 1, name: '普通快递', fee: 0 },
      couponCode: '',
      discountAmount: 0
    })
    
    const paidOrder = orderStore.createOrder({
      items: [mockItems[1]],
      totalAmount: 1599,
      shippingAddress: {
        receiverName: '张三',
        phone: '13800138000',
        province: '北京市',
        city: '东城区',
        district: '东城区',
        detail: '王府井大街88号'
      },
      paymentMethod: { id: 2, name: '微信支付' },
      shippingMethod: { id: 2, name: '顺丰速运', fee: 12 },
      couponCode: '新人专享券',
      discountAmount: 50
    })
    orderStore.payOrder(paidOrder.id)
  }
  
  console.timeEnd('order-list-onMounted')
})
</script>

<style scoped>
.order-list-page {
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

.order-tabs {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.order-tab {
  position: relative;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.order-tab:hover {
  color: #ff6b6b;
}

.order-tab.active {
  color: #ff6b6b;
  font-weight: 600;
}

.order-tab.active::after {
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

.order-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.order-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.order-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.order-info {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #999;
}

.order-id {
  font-weight: 500;
  color: #666;
}

.order-items {
  padding: 15px 20px;
}

.order-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.order-item:not(:last-child) {
  border-bottom: 1px dashed #f0f0f0;
}

.item-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  margin-right: 15px;
  cursor: pointer;
}

.item-info {
  flex: 2;
  cursor: pointer;
}

.item-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 6px 0;
  line-height: 1.4;
}

.item-name:hover {
  color: #ff6b6b;
}

.item-specs {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.item-price,
.item-quantity {
  flex: 1;
  text-align: center;
  font-size: 14px;
  color: #333;
}

.more-items {
  text-align: center;
  padding: 10px 0;
  font-size: 13px;
  color: #999;
  cursor: pointer;
}

.more-items:hover {
  color: #ff6b6b;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #fafafa;
  border-top: 1px solid #e0e0e0;
}

.order-total {
  font-size: 14px;
  color: #666;
}

.total-price {
  font-size: 18px;
  font-weight: 700;
  color: #ff4757;
}

.order-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.action-link {
  font-size: 14px;
  color: #666;
  text-decoration: none;
  cursor: pointer;
  margin-right: 20px;
}

.action-link:hover {
  color: #ff6b6b;
}

.order-empty {
  padding: 60px 0;
}
</style>
