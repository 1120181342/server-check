<template>
  <div class="cart-page">
    <div class="container">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item>
          <router-link to="/">首页</router-link>
        </el-breadcrumb-item>
        <el-breadcrumb-item>我的购物车</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="cart-content" v-if="cartStore.items.length > 0">
        <div class="cart-main">
          <div class="cart-header">
            <div class="select-all" @click="cartStore.toggleSelectAll">
              <el-checkbox :model-value="cartStore.isAllSelected" :indeterminate="cartStore.selectedCount > 0 && cartStore.selectedCount < cartStore.totalCount" />
              <span>全选</span>
            </div>
            <div class="header-columns">
              <span class="col-info">商品信息</span>
              <span class="col-price">单价</span>
              <span class="col-quantity">数量</span>
              <span class="col-subtotal">小计</span>
              <span class="col-action">操作</span>
            </div>
          </div>

          <div class="cart-list">
            <div v-for="item in cartStore.items" :key="item.id" class="cart-item">
              <div class="item-select" @click="cartStore.toggleSelect(item.id)">
                <el-checkbox :model-value="item.selected" />
              </div>
              <div class="item-info" @click="goToDetail(item.id)">
                <el-image
                  :src="item.image"
                  :lazy="true"
                  fit="cover"
                  class="item-image"
                />
                <div class="item-detail">
                  <h3 class="item-name">{{ item.name }}</h3>
                  <p class="item-specs" v-if="item.specs">{{ item.specs }}</p>
                </div>
              </div>
              <div class="item-price">
                <span class="current-price">¥{{ item.discountPrice || item.price }}</span>
                <span v-if="item.discountPrice" class="original-price">¥{{ item.price }}</span>
              </div>
              <div class="item-quantity">
                <el-input-number
                  v-model="item.quantity"
                  :min="1"
                  :max="item.stock || 99"
                  :step="1"
                  size="small"
                  @change="handleQuantityChange(item, $event)"
                />
              </div>
              <div class="item-subtotal">
                <span class="subtotal-price">¥{{ calculateSubtotal(item).toFixed(2) }}</span>
              </div>
              <div class="item-action">
                <el-button type="text" class="action-btn" @click="removeItem(item)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="cart-sidebar">
          <div class="summary-card">
            <h3 class="summary-title">订单结算</h3>
            
            <div class="summary-row">
              <span class="summary-label">商品数量</span>
              <span class="summary-value">{{ cartStore.selectedCount }} 件</span>
            </div>
            
            <div class="summary-row">
              <span class="summary-label">商品总额</span>
              <span class="summary-value">¥{{ cartStore.selectedTotal.toFixed(2) }}</span>
            </div>
            
            <div class="summary-row">
              <span class="summary-label">运费</span>
              <span class="summary-value free">{{ shippingFee > 0 ? `¥${shippingFee}` : '免运费' }}</span>
            </div>
            
            <div class="summary-row discount-row" v-if="couponDiscount > 0">
              <span class="summary-label">优惠券</span>
              <span class="summary-value discount">-¥{{ couponDiscount.toFixed(2) }}</span>
            </div>
            
            <div class="summary-total">
              <span class="summary-label">应付总额</span>
              <span class="summary-value total-price">¥{{ totalAmount.toFixed(2) }}</span>
            </div>

            <div class="coupon-section">
              <div class="coupon-input">
                <el-input
                  v-model="couponCode"
                  placeholder="输入优惠券码"
                  style="width: 180px"
                />
                <el-button type="primary" @click="applyCoupon">使用</el-button>
              </div>
              <div class="coupon-list" v-if="availableCoupons.length > 0">
                <p class="coupon-title">可用优惠券：</p>
                <div 
                  v-for="coupon in availableCoupons" 
                  :key="coupon.id"
                  class="coupon-item"
                  :class="{ disabled: !coupon.available }"
                  @click="selectCoupon(coupon)"
                >
                  <div class="coupon-value">¥{{ coupon.value }}</div>
                  <div class="coupon-info">
                    <div class="coupon-name">{{ coupon.name }}</div>
                    <div class="coupon-condition">满{{ coupon.minAmount }}可用</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-actions">
              <el-button 
                type="primary" 
                size="large" 
                class="checkout-btn"
                :disabled="cartStore.selectedCount === 0"
                @click="goCheckout"
              >
                去结算 ({{ cartStore.selectedCount }})
              </el-button>
              <el-button 
                text 
                class="clear-btn"
                @click="handleClearSelected"
              >
                清除已选
              </el-button>
            </div>
          </div>

          <div class="recommend-card" v-if="recommendProducts.length > 0">
            <h3 class="recommend-title">为您推荐</h3>
            <div class="recommend-list">
              <div 
                v-for="product in recommendProducts" 
                :key="product.id"
                class="recommend-item"
                @click="goToDetail(product.id)"
              >
                <el-image :src="product.image" fit="cover" class="recommend-image" />
                <div class="recommend-info">
                  <p class="recommend-name">{{ product.name }}</p>
                  <p class="recommend-price">¥{{ product.discountPrice || product.price }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="cart-empty" v-else>
        <el-empty description="购物车空空如也">
          <el-button type="primary" @click="goShopping">
            <el-icon><ShoppingBag /></el-icon>
            去逛逛
          </el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore, useProductStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const cartStore = useCartStore()
const productStore = useProductStore()

const couponCode = ref('')
const couponDiscount = ref(0)
const selectedCoupon = ref(null)
const shippingFee = ref(0)

const availableCoupons = ref([
  { id: 1, name: '新人专享券', value: 50, minAmount: 200, available: true },
  { id: 2, name: '满减优惠券', value: 100, minAmount: 1000, available: true },
  { id: 3, name: '限时折扣券', value: 200, minAmount: 2000, available: false }
])

const recommendProducts = ref([])

const totalAmount = computed(() => {
  return Math.max(0, cartStore.selectedTotal - couponDiscount.value + shippingFee.value)
})

const calculateSubtotal = (item) => {
  const price = item.discountPrice || item.price
  return price * item.quantity
}

const handleQuantityChange = (item, newQuantity) => {
  console.time('quantity-change')
  cartStore.updateQuantity(item.id, newQuantity)
  console.timeEnd('quantity-change')
}

const removeItem = async (item) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    console.time('remove-item')
    cartStore.removeItem(item.id)
    ElMessage.success('已删除')
    console.timeEnd('remove-item')
  } catch {
    // 用户取消
  }
}

const handleClearSelected = async () => {
  if (cartStore.selectedCount === 0) {
    ElMessage.warning('请先选择要清除的商品')
    return
  }
  try {
    await ElMessageBox.confirm('确定要清除已选商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    console.time('clear-selected')
    cartStore.clearSelected()
    ElMessage.success('已清除')
    console.timeEnd('clear-selected')
  } catch {
    // 用户取消
  }
}

const applyCoupon = () => {
  if (!couponCode.value.trim()) {
    ElMessage.warning('请输入优惠券码')
    return
  }
  const coupon = availableCoupons.value.find(c => c.name === couponCode.value)
  if (coupon && coupon.available) {
    selectCoupon(coupon)
  } else {
    ElMessage.error('优惠券无效或不可用')
  }
}

const selectCoupon = (coupon) => {
  if (!coupon.available) {
    ElMessage.warning('该优惠券不可用')
    return
  }
  if (cartStore.selectedTotal < coupon.minAmount) {
    ElMessage.warning(`订单金额不满${coupon.minAmount}元，无法使用该优惠券`)
    return
  }
  selectedCoupon.value = coupon
  couponDiscount.value = coupon.value
  couponCode.value = coupon.name
  ElMessage.success('优惠券已应用')
}

const goToDetail = (productId) => {
  router.push(`/products/${productId}`)
}

const goCheckout = () => {
  console.time('go-checkout')
  router.push('/checkout')
  console.timeEnd('go-checkout')
}

const goShopping = () => {
  router.push('/products')
}

onMounted(() => {
  console.time('cart-onMounted')
  recommendProducts.value = productStore.getHotProducts(4)
  console.timeEnd('cart-onMounted')
})
</script>

<style scoped>
.cart-page {
  padding: 20px 0;
  min-height: calc(100vh - 200px);
}

.breadcrumb {
  margin-bottom: 20px;
  padding: 15px 20px;
  background: #fff;
  border-radius: 8px;
}

.cart-content {
  display: flex;
  gap: 20px;
}

.cart-main {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.cart-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  width: 60px;
}

.header-columns {
  flex: 1;
  display: flex;
  font-size: 14px;
  color: #666;
}

.col-info {
  flex: 2;
  padding-left: 20px;
}

.col-price {
  flex: 1;
  text-align: center;
}

.col-quantity {
  flex: 1;
  text-align: center;
}

.col-subtotal {
  flex: 1;
  text-align: center;
}

.col-action {
  flex: 0.8;
  text-align: center;
}

.cart-list {
  display: flex;
  flex-direction: column;
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.cart-item:hover {
  background: #fafafa;
}

.item-select {
  width: 60px;
  cursor: pointer;
}

.item-info {
  flex: 2;
  display: flex;
  gap: 15px;
  cursor: pointer;
}

.item-image {
  width: 100px;
  height: 100px;
  border-radius: 4px;
}

.item-detail {
  flex: 1;
}

.item-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 8px 0;
  line-height: 1.4;
  transition: color 0.2s;
}

.item-name:hover {
  color: #ff6b6b;
}

.item-specs {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.item-price {
  flex: 1;
  text-align: center;
}

.current-price {
  font-size: 16px;
  font-weight: 600;
  color: #ff4757;
}

.original-price {
  display: block;
  font-size: 12px;
  color: #999;
  text-decoration: line-through;
}

.item-quantity {
  flex: 1;
  text-align: center;
}

.item-subtotal {
  flex: 1;
  text-align: center;
}

.subtotal-price {
  font-size: 16px;
  font-weight: 600;
  color: #ff4757;
}

.item-action {
  flex: 0.8;
  text-align: center;
}

.action-btn {
  color: #999;
}

.action-btn:hover {
  color: #ff4757;
}

.cart-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.summary-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.summary-label {
  color: #666;
}

.summary-value {
  color: #333;
}

.summary-value.free {
  color: #67c23a;
}

.summary-value.discount {
  color: #ff4757;
}

.discount-row {
  padding-top: 10px;
  border-top: 1px dashed #f0f0f0;
}

.summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  margin: 15px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.summary-total .summary-label {
  font-size: 16px;
  font-weight: 500;
}

.total-price {
  font-size: 20px;
  font-weight: 700;
  color: #ff4757;
}

.coupon-section {
  margin-bottom: 20px;
}

.coupon-input {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.coupon-title {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
}

.coupon-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.coupon-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #fff5f5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.coupon-item:hover:not(.disabled) {
  border-color: #ff6b6b;
}

.coupon-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.coupon-value {
  font-size: 24px;
  font-weight: 700;
  color: #ff4757;
}

.coupon-info {
  flex: 1;
}

.coupon-name {
  font-size: 14px;
  color: #333;
}

.coupon-condition {
  font-size: 12px;
  color: #999;
}

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkout-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
}

.clear-btn {
  color: #999;
}

.clear-btn:hover {
  color: #ff4757;
}

.recommend-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.recommend-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.recommend-item {
  display: flex;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
  padding: 8px;
  border-radius: 4px;
}

.recommend-item:hover {
  background: #fafafa;
}

.recommend-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

.recommend-info {
  flex: 1;
}

.recommend-name {
  font-size: 12px;
  color: #333;
  margin: 0 0 8px 0;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.recommend-price {
  font-size: 14px;
  font-weight: 600;
  color: #ff4757;
  margin: 0;
}

.cart-empty {
  background: #fff;
  border-radius: 8px;
  padding: 80px 0;
}
</style>
