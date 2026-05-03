<template>
  <div class="checkout-page">
    <div class="container">
      <el-steps :active="1" align-center class="checkout-steps">
        <el-step title="确认订单" />
        <el-step title="支付" />
        <el-step title="完成" />
      </el-steps>

      <div class="checkout-content">
        <div class="checkout-main">
          <div class="address-section">
            <div class="section-header">
              <h3>
                <el-icon><Location /></el-icon>
                收货地址
              </h3>
              <el-button type="primary" text @click="showAddressForm = true">
                <el-icon><Plus /></el-icon>
                新增地址
              </el-button>
            </div>
            <div class="address-list">
              <div 
                v-for="addr in addressStore.addresses" 
                :key="addr.id"
                class="address-card"
                :class="{ selected: selectedAddress?.id === addr.id, default: addr.isDefault }"
                @click="selectAddress(addr)"
              >
                <div class="address-info">
                  <div class="address-header">
                    <span class="receiver">{{ addr.receiverName }}</span>
                    <span class="phone">{{ addr.phone }}</span>
                    <el-tag v-if="addr.isDefault" type="danger" size="small">默认</el-tag>
                  </div>
                  <div class="address-detail">
                    {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
                  </div>
                </div>
                <div class="address-actions" @click.stop>
                  <el-button type="text" size="small" @click="editAddress(addr)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button type="text" size="small" @click="deleteAddress(addr.id)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
              <div v-if="addressStore.addresses.length === 0" class="no-address">
                <el-empty description="暂无收货地址" :image-size="80">
                  <el-button type="primary" @click="showAddressForm = true">添加收货地址</el-button>
                </el-empty>
              </div>
            </div>
          </div>

          <div class="shipping-section">
            <div class="section-header">
              <h3>
                <el-icon><Van /></el-icon>
                配送方式
              </h3>
            </div>
            <div class="shipping-list">
              <div 
                v-for="shipping in shippingMethods" 
                :key="shipping.id"
                class="shipping-card"
                :class="{ selected: selectedShipping?.id === shipping.id }"
                @click="selectShipping(shipping)"
              >
                <div class="shipping-icon">
                  <el-icon :size="28"><component :is="shipping.icon" /></el-icon>
                </div>
                <div class="shipping-info">
                  <div class="shipping-name">{{ shipping.name }}</div>
                  <div class="shipping-desc">{{ shipping.description }}</div>
                </div>
                <div class="shipping-fee">
                  <span v-if="shipping.fee > 0">¥{{ shipping.fee }}</span>
                  <span v-else class="free">免运费</span>
                </div>
              </div>
            </div>
          </div>

          <div class="payment-section">
            <div class="section-header">
              <h3>
                <el-icon><Wallet /></el-icon>
                支付方式
              </h3>
            </div>
            <div class="payment-list">
              <div 
                v-for="payment in paymentMethods" 
                :key="payment.id"
                class="payment-card"
                :class="{ selected: selectedPayment?.id === payment.id }"
                @click="selectPayment(payment)"
              >
                <div class="payment-icon" :style="{ background: payment.color }">
                  <el-icon :size="24"><component :is="payment.icon" /></el-icon>
                </div>
                <div class="payment-name">{{ payment.name }}</div>
              </div>
            </div>
          </div>

          <div class="goods-section">
            <div class="section-header">
              <h3>
                <el-icon><ShoppingBag /></el-icon>
                商品清单
              </h3>
              <router-link to="/cart" class="edit-link">
                <el-icon><Edit /></el-icon>
                修改
              </router-link>
            </div>
            <div class="goods-list">
              <div v-for="item in cartStore.selectedItems" :key="item.id" class="goods-item">
                <el-image :src="item.image" fit="cover" class="goods-image" />
                <div class="goods-info">
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

          <div class="coupon-section">
            <div class="section-header">
              <h3>
                <el-icon><Ticket /></el-icon>
                优惠券
              </h3>
            </div>
            <div class="coupon-list">
              <div 
                v-for="coupon in availableCoupons" 
                :key="coupon.id"
                class="coupon-card"
                :class="{ selected: selectedCoupon?.id === coupon.id, disabled: !coupon.available }"
                @click="selectCoupon(coupon)"
              >
                <div class="coupon-value">
                  <span class="currency">¥</span>
                  <span class="value">{{ coupon.value }}</span>
                </div>
                <div class="coupon-info">
                  <div class="coupon-name">{{ coupon.name }}</div>
                  <div class="coupon-condition">满{{ coupon.minAmount }}可用</div>
                </div>
              </div>
            </div>
          </div>

          <div class="message-section">
            <div class="section-header">
              <h3>
                <el-icon><EditPen /></el-icon>
                订单备注
              </h3>
            </div>
            <el-input
              v-model="orderMessage"
              type="textarea"
              :rows="3"
              placeholder="选填，请输入订单备注信息"
              maxlength="200"
              show-word-limit
            />
          </div>
        </div>

        <div class="checkout-sidebar">
          <div class="summary-card">
            <h3 class="summary-title">订单汇总</h3>
            
            <div class="summary-row">
              <span class="summary-label">商品总价</span>
              <span class="summary-value">¥{{ cartStore.selectedTotal.toFixed(2) }}</span>
            </div>
            
            <div class="summary-row">
              <span class="summary-label">运费</span>
              <span class="summary-value">
                {{ selectedShipping?.fee > 0 ? `¥${selectedShipping.fee}` : '免运费' }}
              </span>
            </div>
            
            <div class="summary-row discount-row" v-if="selectedCoupon">
              <span class="summary-label">优惠券</span>
              <span class="summary-value discount">-¥{{ selectedCoupon.value }}</span>
            </div>
            
            <div class="summary-total">
              <span class="summary-label">应付总额</span>
              <span class="summary-value total-price">¥{{ totalAmount.toFixed(2) }}</span>
            </div>

            <div class="summary-notice" v-if="!canSubmit">
              <el-icon><Warning /></el-icon>
              <span>{{ submitNotice }}</span>
            </div>

            <el-button 
              type="primary" 
              size="large" 
              class="submit-btn"
              :disabled="!canSubmit"
              :loading="submitting"
              @click="submitOrder"
            >
              提交订单
            </el-button>

            <div class="summary-agreement">
              <el-checkbox v-model="agreed">我已阅读并同意</el-checkbox>
              <a href="javascript:void(0)" class="agreement-link">《用户协议》</a>
              <span>和</span>
              <a href="javascript:void(0)" class="agreement-link">《隐私政策》</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="showAddressForm" 
      :title="editingAddress ? '编辑收货地址' : '新增收货地址'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addressFormRef"
        :model="addressForm"
        :rules="addressRules"
        label-width="80px"
      >
        <el-form-item label="收货人" prop="receiverName">
          <el-input v-model="addressForm.receiverName" placeholder="请输入收货人姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="addressForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="所在地区" prop="region">
          <el-cascader
            v-model="addressForm.region"
            :options="regionOptions"
            placeholder="请选择省/市/区"
            clearable
          />
        </el-form-item>
        <el-form-item label="详细地址" prop="detail">
          <el-input
            v-model="addressForm.detail"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址"
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="addressForm.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddressForm = false">取消</el-button>
        <el-button type="primary" @click="saveAddress">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore, useOrderStore, useAddressStore } from '@/store'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const cartStore = useCartStore()
const orderStore = useOrderStore()
const addressStore = useAddressStore()

const selectedAddress = ref(null)
const selectedShipping = ref(null)
const selectedPayment = ref(null)
const selectedCoupon = ref(null)
const orderMessage = ref('')
const agreed = ref(true)
const submitting = ref(false)
const showAddressForm = ref(false)
const editingAddress = ref(null)
const addressFormRef = ref<FormInstance>()

const shippingMethods = ref([
  { id: 1, name: '普通快递', description: '预计3-5天送达', icon: 'Van', fee: 0 },
  { id: 2, name: '顺丰速运', description: '预计1-2天送达', icon: 'Promotion', fee: 12 },
  { id: 3, name: '次日达', description: '次日送达', icon: 'Clock', fee: 20 }
])

const paymentMethods = ref([
  { id: 1, name: '支付宝', icon: 'Wallet', color: '#1677ff' },
  { id: 2, name: '微信支付', icon: 'ChatDotRound', color: '#07c160' },
  { id: 3, name: '银联支付', icon: 'CreditCard', color: '#e4393c' }
])

const availableCoupons = ref([
  { id: 1, name: '新人专享券', value: 50, minAmount: 200, available: true },
  { id: 2, name: '满减优惠券', value: 100, minAmount: 1000, available: true },
  { id: 3, name: '限时折扣券', value: 200, minAmount: 2000, available: false }
])

const regionOptions = ref([
  {
    value: '北京市',
    label: '北京市',
    children: [
      {
        value: '东城区',
        label: '东城区',
        children: [{ value: '东城区', label: '东城区' }]
      },
      {
        value: '西城区',
        label: '西城区',
        children: [{ value: '西城区', label: '西城区' }]
      }
    ]
  },
  {
    value: '上海市',
    label: '上海市',
    children: [
      {
        value: '黄浦区',
        label: '黄浦区',
        children: [{ value: '黄浦区', label: '黄浦区' }]
      },
      {
        value: '浦东新区',
        label: '浦东新区',
        children: [{ value: '浦东新区', label: '浦东新区' }]
      }
    ]
  }
])

const addressForm = reactive({
  receiverName: '',
  phone: '',
  region: [],
  detail: '',
  isDefault: false
})

const addressRules: FormRules = {
  receiverName: [{ required: true, message: '请输入收货人姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  region: [{ required: true, message: '请选择所在地区', trigger: 'change' }],
  detail: [{ required: true, message: '请输入详细地址', trigger: 'blur' }]
}

const totalAmount = computed(() => {
  let total = cartStore.selectedTotal
  if (selectedShipping.value?.fee > 0) {
    total += selectedShipping.value.fee
  }
  if (selectedCoupon.value) {
    total -= selectedCoupon.value.value
  }
  return Math.max(0, total)
})

const canSubmit = computed(() => {
  return !!selectedAddress.value && 
         !!selectedShipping.value && 
         !!selectedPayment.value &&
         cartStore.selectedItems.length > 0 &&
         agreed.value
})

const submitNotice = computed(() => {
  if (!selectedAddress.value) return '请选择收货地址'
  if (!selectedShipping.value) return '请选择配送方式'
  if (!selectedPayment.value) return '请选择支付方式'
  if (!agreed.value) return '请先同意用户协议'
  return ''
})

const selectAddress = (addr) => {
  selectedAddress.value = addr
}

const selectShipping = (shipping) => {
  selectedShipping.value = shipping
}

const selectPayment = (payment) => {
  selectedPayment.value = payment
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
  selectedCoupon.value = selectedCoupon.value?.id === coupon.id ? null : coupon
}

const editAddress = (addr) => {
  editingAddress.value = addr
  addressForm.receiverName = addr.receiverName
  addressForm.phone = addr.phone
  addressForm.region = [addr.province, addr.city, addr.district]
  addressForm.detail = addr.detail
  addressForm.isDefault = addr.isDefault
  showAddressForm.value = true
}

const deleteAddress = async (addrId) => {
  try {
    await ElMessageBox.confirm('确定要删除该地址吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    addressStore.deleteAddress(addrId)
    if (selectedAddress.value?.id === addrId) {
      selectedAddress.value = addressStore.defaultAddress
    }
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

const saveAddress = async () => {
  if (!addressFormRef.value) return
  
  await addressFormRef.value.validate((valid) => {
    if (valid) {
      const addressData = {
        receiverName: addressForm.receiverName,
        phone: addressForm.phone,
        province: addressForm.region[0],
        city: addressForm.region[1],
        district: addressForm.region[2],
        detail: addressForm.detail,
        isDefault: addressForm.isDefault
      }
      
      if (editingAddress.value) {
        addressStore.updateAddress(editingAddress.value.id, addressData)
        ElMessage.success('修改成功')
      } else {
        addressStore.addAddress(addressData)
        ElMessage.success('添加成功')
      }
      
      showAddressForm.value = false
      resetAddressForm()
    }
  })
}

const resetAddressForm = () => {
  editingAddress.value = null
  addressForm.receiverName = ''
  addressForm.phone = ''
  addressForm.region = []
  addressForm.detail = ''
  addressForm.isDefault = false
}

const submitOrder = async () => {
  if (!canSubmit.value) return
  
  submitting.value = true
  console.time('submit-order')
  
  try {
    const order = orderStore.createOrder({
      items: [...cartStore.selectedItems],
      totalAmount: totalAmount.value,
      shippingAddress: { ...selectedAddress.value },
      paymentMethod: selectedPayment.value,
      shippingMethod: selectedShipping.value,
      couponCode: selectedCoupon.value?.name || '',
      discountAmount: selectedCoupon.value?.value || 0,
      message: orderMessage.value
    })
    
    cartStore.clearSelected()
    
    console.timeEnd('submit-order')
    
    ElMessage.success('订单创建成功！')
    router.push(`/orders/${order.id}`)
  } catch (error) {
    ElMessage.error('订单创建失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  console.time('checkout-onMounted')
  
  if (addressStore.addresses.length === 0) {
    addressStore.addAddress({
      receiverName: '张三',
      phone: '13800138000',
      province: '北京市',
      city: '东城区',
      district: '东城区',
      detail: '王府井大街88号',
      isDefault: true
    })
  }
  
  if (addressStore.defaultAddress) {
    selectedAddress.value = addressStore.defaultAddress
  } else if (addressStore.addresses.length > 0) {
    selectedAddress.value = addressStore.addresses[0]
  }
  
  selectedShipping.value = shippingMethods.value[0]
  selectedPayment.value = paymentMethods.value[0]
  
  console.timeEnd('checkout-onMounted')
})
</script>

<style scoped>
.checkout-page {
  padding: 20px 0;
  min-height: calc(100vh - 200px);
}

.checkout-steps {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.checkout-content {
  display: flex;
  gap: 20px;
}

.checkout-main {
  flex: 1;
}

.checkout-sidebar {
  width: 320px;
  flex-shrink: 0;
  position: sticky;
  top: 100px;
  height: fit-content;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.edit-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #ff6b6b;
  text-decoration: none;
}

.address-section,
.shipping-section,
.payment-section,
.goods-section,
.coupon-section,
.message-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.address-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.address-card {
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.address-card:hover {
  border-color: #ffb3b3;
}

.address-card.selected {
  border-color: #ff6b6b;
  background: #fff5f5;
}

.address-card.default::before {
  content: '默认';
  position: absolute;
  top: 0;
  right: 0;
  padding: 2px 8px;
  background: #ff6b6b;
  color: #fff;
  font-size: 12px;
  border-radius: 0 8px 0 4px;
}

.address-info {
  margin-bottom: 10px;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.receiver {
  font-size: 15px;
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

.address-actions {
  display: flex;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px dashed #f0f0f0;
}

.no-address {
  grid-column: span 2;
  padding: 40px 0;
}

.shipping-list {
  display: flex;
  gap: 15px;
}

.shipping-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.shipping-card:hover {
  border-color: #ffb3b3;
}

.shipping-card.selected {
  border-color: #ff6b6b;
  background: #fff5f5;
}

.shipping-icon {
  width: 50px;
  height: 50px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.shipping-info {
  flex: 1;
}

.shipping-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.shipping-desc {
  font-size: 13px;
  color: #999;
}

.shipping-fee {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.shipping-fee .free {
  color: #67c23a;
}

.payment-list {
  display: flex;
  gap: 15px;
}

.payment-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 25px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.payment-card:hover {
  border-color: #ffb3b3;
}

.payment-card.selected {
  border-color: #ff6b6b;
  background: #fff5f5;
}

.payment-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.payment-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
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
}

.goods-info {
  flex: 2;
}

.goods-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 6px 0;
  line-height: 1.4;
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

.coupon-list {
  display: flex;
  gap: 15px;
}

.coupon-card {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border: 1px dashed #ffb3b3;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.coupon-card:hover:not(.disabled) {
  border-style: solid;
  border-color: #ff6b6b;
  transform: translateY(-2px);
}

.coupon-card.selected {
  border-style: solid;
  border-color: #ff6b6b;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
}

.coupon-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.coupon-value {
  padding-right: 15px;
  border-right: 1px dashed #ffb3b3;
  margin-right: 15px;
}

.coupon-card.selected .coupon-value {
  border-right-color: rgba(255, 255, 255, 0.5);
}

.currency {
  font-size: 14px;
  color: #ff4757;
  font-weight: 600;
}

.coupon-card.selected .currency {
  color: #fff;
}

.value {
  font-size: 28px;
  font-weight: 700;
  color: #ff4757;
}

.coupon-card.selected .value {
  color: #fff;
}

.coupon-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.coupon-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.coupon-card.selected .coupon-name {
  color: #fff;
}

.coupon-condition {
  font-size: 12px;
  color: #999;
}

.coupon-card.selected .coupon-condition {
  color: rgba(255, 255, 255, 0.9);
}

.summary-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
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
  font-size: 22px;
  font-weight: 700;
  color: #ff4757;
}

.summary-notice {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 15px;
  background: #fffbe6;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 13px;
  color: #e6a23c;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
  margin-bottom: 15px;
}

.summary-agreement {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.agreement-link {
  color: #ff6b6b;
  text-decoration: none;
}
</style>
