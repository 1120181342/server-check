<template>
  <div class="product-detail-page">
    <div class="container">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item>
          <router-link to="/">首页</router-link>
        </el-breadcrumb-item>
        <el-breadcrumb-item>
          <router-link :to="`/products?category=${product?.categoryId}`">
            {{ product?.categoryName }}
          </router-link>
        </el-breadcrumb-item>
        <el-breadcrumb-item>{{ product?.name }}</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="product-main">
        <div class="product-gallery">
          <el-image
            :src="currentImage"
            :zoom-rate="1.2"
            :max-scale="3"
            :min-scale="0.2"
            :preview-src-list="allImages"
            :initial-index="0"
            fit="contain"
            class="main-image"
          />
          <div class="thumbnail-list">
            <div 
              v-for="(img, index) in allImages" 
              :key="index"
              class="thumbnail-item"
              :class="{ active: currentImageIndex === index }"
              @click="selectImage(index)"
            >
              <el-image :src="img" fit="cover" class="thumbnail-image" />
            </div>
          </div>
        </div>

        <div class="product-info">
          <div class="product-header">
            <div class="product-tags" v-if="product?.isNew || product?.isHot">
              <span v-if="product?.isNew" class="tag new-tag">新品</span>
              <span v-if="product?.isHot" class="tag hot-tag">热卖</span>
            </div>
            <h1 class="product-name">{{ product?.name }}</h1>
            <p class="product-summary">{{ product?.description }}</p>
          </div>

          <div class="price-section">
            <div class="price-row">
              <span class="price-label">促销价</span>
              <span class="current-price">¥{{ product?.discountPrice || product?.price }}</span>
              <span v-if="product?.discountPrice" class="original-price">¥{{ product?.price }}</span>
              <span v-if="product?.discountPrice" class="discount-tag">
                {{ Math.round((1 - product.discountPrice / product.price) * 100) }}% OFF
              </span>
            </div>
            <div class="promo-row" v-if="promotions.length > 0">
              <span class="promo-label">促销</span>
              <div class="promo-list">
                <div v-for="promo in promotions" :key="promo.id" class="promo-item">
                  <span class="promo-tag">{{ promo.type }}</span>
                  <span class="promo-text">{{ promo.text }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="specs-section" v-if="product?.specs?.length">
            <div class="specs-row" v-for="spec in product.specs" :key="spec.name">
              <span class="specs-label">{{ spec.name }}</span>
              <div class="specs-options">
                <div 
                  v-for="(option, index) in spec.values" 
                  :key="index"
                  class="specs-option"
                  :class="{ active: selectedSpecs[spec.name] === option }"
                  @click="selectSpec(spec.name, option)"
                >
                  {{ option }}
                </div>
              </div>
            </div>
          </div>

          <div class="quantity-section">
            <span class="quantity-label">数量</span>
            <div class="quantity-control">
              <el-button-group>
                <el-button :disabled="quantity <= 1" @click="decreaseQuantity">
                  <el-icon><Minus /></el-icon>
                </el-button>
                <el-input 
                  v-model.number="quantity" 
                  :min="1" 
                  :max="product?.stock || 99"
                  style="width: 80px"
                />
                <el-button :disabled="quantity >= (product?.stock || 99)" @click="increaseQuantity">
                  <el-icon><Plus /></el-icon>
                </el-button>
              </el-button-group>
              <span class="stock-info" v-if="product?.stock">
                库存 {{ product.stock }} 件
              </span>
            </div>
          </div>

          <div class="action-section">
            <el-button type="primary" size="large" class="action-btn buy-btn" @click="buyNow">
              <el-icon><Wallet /></el-icon>
              立即购买
            </el-button>
            <el-button size="large" class="action-btn cart-btn" @click="addToCart">
              <el-icon><ShoppingCart /></el-icon>
              加入购物车
            </el-button>
            <el-button size="large" class="action-btn favorite-btn" @click="toggleFavorite">
              <el-icon><Heart /></el-icon>
              收藏
            </el-button>
          </div>

          <div class="service-section">
            <div class="service-item">
              <el-icon><CircleCheck /></el-icon>
              <span>正品保障</span>
            </div>
            <div class="service-item">
              <el-icon><Back /></el-icon>
              <span>7天无理由退换</span>
            </div>
            <div class="service-item">
              <el-icon><Van /></el-icon>
              <span>全国包邮</span>
            </div>
            <div class="service-item">
              <el-icon><Headset /></el-icon>
              <span>专属客服</span>
            </div>
          </div>

          <div class="share-section">
            <span>分享</span>
            <div class="share-icons">
              <el-icon><ChatDotRound /></el-icon>
              <el-icon><ChatLineRound /></el-icon>
              <el-icon><Connection /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="product-tabs">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <el-tab-pane label="商品详情" name="detail">
            <div class="tab-content">
              <div class="info-list">
                <div class="info-item">
                  <span class="info-label">品牌</span>
                  <span class="info-value">{{ product?.brand }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">商品名称</span>
                  <span class="info-value">{{ product?.name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">产地</span>
                  <span class="info-value">中国</span>
                </div>
                <div class="info-item">
                  <span class="info-label">商品毛重</span>
                  <span class="info-value">0.5kg</span>
                </div>
                <div class="info-item">
                  <span class="info-label">上市时间</span>
                  <span class="info-value">2024年</span>
                </div>
              </div>
              <div class="description-section">
                <h3>商品描述</h3>
                <p>{{ product?.description }}</p>
                <div class="description-images" v-if="product?.images?.length">
                  <el-image 
                    v-for="(img, index) in product.images" 
                    :key="index"
                    :src="img" 
                    fit="contain"
                    class="desc-image"
                  />
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="规格参数" name="specs">
            <div class="tab-content">
              <table class="specs-table">
                <tbody>
                  <tr>
                    <td class="specs-label-cell">品牌</td>
                    <td class="specs-value-cell">{{ product?.brand }}</td>
                  </tr>
                  <tr>
                    <td class="specs-label-cell">商品名称</td>
                    <td class="specs-value-cell">{{ product?.name }}</td>
                  </tr>
                  <tr>
                    <td class="specs-label-cell">价格区间</td>
                    <td class="specs-value-cell">¥{{ product?.discountPrice || product?.price }}</td>
                  </tr>
                  <tr>
                    <td class="specs-label-cell">适用人群</td>
                    <td class="specs-value-cell">通用</td>
                  </tr>
                  <tr v-if="product?.specs">
                    <td class="specs-label-cell">可选规格</td>
                    <td class="specs-value-cell">
                      <div v-for="spec in product.specs" :key="spec.name">
                        {{ spec.name }}: {{ spec.values.join(' / ') }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </el-tab-pane>
          <el-tab-pane label="用户评价" name="reviews">
            <div class="tab-content">
              <div class="reviews-summary">
                <div class="rating-display">
                  <div class="rating-score">{{ product?.rating || 4.8 }}</div>
                  <el-rate :model-value="product?.rating || 4.8" disabled show-score text-color="#ff6b6b" />
                  <div class="rating-count">{{ reviews.length }} 条评价</div>
                </div>
                <div class="rating-tags">
                  <span class="tag-item" :class="{ active: activeFilterTag === 'all' }" @click="filterReviews('all')">
                    全部 ({{ reviews.length }})
                  </span>
                  <span class="tag-item" :class="{ active: activeFilterTag === 'good' }" @click="filterReviews('good')">
                    好评 ({{ goodReviews.length }})
                  </span>
                  <span class="tag-item" :class="{ active: activeFilterTag === 'withImg' }" @click="filterReviews('withImg')">
                    有图 ({{ imgReviews.length }})
                  </span>
                </div>
              </div>
              <div class="reviews-list">
                <div v-for="review in filteredReviews" :key="review.id" class="review-item">
                  <div class="review-header">
                    <el-avatar :size="40" class="user-avatar">
                      {{ review.userName.charAt(0) }}
                    </el-avatar>
                    <div class="user-info">
                      <div class="user-name">{{ review.userName }}</div>
                      <el-rate :model-value="review.rating" disabled size="small" />
                    </div>
                    <div class="review-time">{{ review.time }}</div>
                  </div>
                  <div class="review-content">{{ review.content }}</div>
                  <div class="review-images" v-if="review.images?.length">
                    <el-image 
                      v-for="(img, index) in review.images" 
                      :key="index"
                      :src="img" 
                      fit="cover"
                      class="review-image"
                      :preview-src-list="review.images"
                    />
                  </div>
                  <div class="review-specs" v-if="review.specs">
                    购买规格: {{ review.specs }}
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore, useCartStore } from '@/store'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()
const cartStore = useCartStore()

const product = ref(null)
const currentImageIndex = ref(0)
const quantity = ref(1)
const selectedSpecs = ref({})
const activeTab = ref('detail')
const activeFilterTag = ref('all')

const allImages = computed(() => {
  if (!product.value) return []
  const images = [product.value.image]
  if (product.value.images?.length) {
    images.push(...product.value.images)
  }
  return images
})

const currentImage = computed(() => allImages.value[currentImageIndex.value] || '')

const promotions = ref([
  { id: 1, type: '满减', text: '满1000减100，满2000减200' },
  { id: 2, type: '优惠券', text: '领取优惠券再享95折' },
  { id: 3, type: '赠品', text: '下单即送精美礼品' }
])

const reviews = ref([
  {
    id: 1,
    userName: '用户***123',
    rating: 5,
    content: '非常好的产品，质量很棒，物流也很快，下次还会再来！',
    images: [
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=smartphone%20unboxing%20photo&image_size=square_hd',
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=product%20review%20photo&image_size=square_hd'
    ],
    time: '2024-01-15 10:30',
    specs: '黑色 / 256GB'
  },
  {
    id: 2,
    userName: '用户***456',
    rating: 4,
    content: '产品不错，就是发货稍微慢了一点，整体还是满意的。',
    images: [],
    time: '2024-01-14 15:20',
    specs: '白色 / 512GB'
  },
  {
    id: 3,
    userName: '用户***789',
    rating: 5,
    content: '第三次购买了，一直很信赖这个品牌，推荐给大家！',
    images: [
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=happy%20customer%20product%20photo&image_size=square_hd'
    ],
    time: '2024-01-13 09:15',
    specs: '蓝色 / 256GB'
  }
])

const goodReviews = computed(() => reviews.value.filter(r => r.rating >= 4))
const imgReviews = computed(() => reviews.value.filter(r => r.images?.length > 0))

const filteredReviews = computed(() => {
  switch (activeFilterTag.value) {
    case 'good':
      return goodReviews.value
    case 'withImg':
      return imgReviews.value
    default:
      return reviews.value
  }
})

const selectImage = (index) => {
  currentImageIndex.value = index
}

const selectSpec = (name, option) => {
  selectedSpecs.value[name] = option
}

const decreaseQuantity = () => {
  if (quantity.value > 1) {
    quantity.value--
  }
}

const increaseQuantity = () => {
  const maxStock = product.value?.stock || 99
  if (quantity.value < maxStock) {
    quantity.value++
  }
}

const addToCart = () => {
  console.time('add-to-cart-detail')
  
  if (!product.value) return
  
  const specsText = Object.keys(selectedSpecs.value).length > 0 
    ? Object.values(selectedSpecs.value).join(' / ') 
    : null
  
  const result = cartStore.addItem(product.value, quantity.value, specsText)
  
  if (result) {
    ElMessage.success({
      message: '已加入购物车',
      duration: 2000
    })
  }
  
  console.timeEnd('add-to-cart-detail')
}

const buyNow = () => {
  console.time('buy-now')
  
  if (!product.value) return
  
  const specsText = Object.keys(selectedSpecs.value).length > 0 
    ? Object.values(selectedSpecs.value).join(' / ') 
    : null
  
  cartStore.addItem(product.value, quantity.value, specsText)
  
  const item = cartStore.items.find(i => 
    i.id === product.value.id && 
    JSON.stringify(i.specs) === JSON.stringify(specsText)
  )
  
  if (item) {
    cartStore.items.forEach(i => i.selected = i.id === item.id)
    cartStore.saveToStorage()
  }
  
  router.push('/checkout')
  
  console.timeEnd('buy-now')
}

const toggleFavorite = () => {
  ElMessage.info('已添加到收藏')
}

const filterReviews = (type) => {
  activeFilterTag.value = type
}

onMounted(() => {
  console.time('product-detail-onMounted')
  
  const productId = parseInt(route.params.id)
  product.value = productStore.getProductById(productId)
  
  if (product.value?.specs) {
    product.value.specs.forEach(spec => {
      if (spec.values?.length > 0) {
        selectedSpecs.value[spec.name] = spec.values[0]
      }
    })
  }
  
  console.timeEnd('product-detail-onMounted')
})
</script>

<style scoped>
.product-detail-page {
  padding: 20px 0;
  min-height: calc(100vh - 200px);
}

.breadcrumb {
  margin-bottom: 20px;
  padding: 15px 20px;
  background: #fff;
  border-radius: 8px;
}

.product-main {
  display: flex;
  gap: 30px;
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 20px;
}

.product-gallery {
  width: 450px;
  flex-shrink: 0;
}

.main-image {
  width: 100%;
  height: 450px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 15px;
}

.thumbnail-list {
  display: flex;
  gap: 10px;
}

.thumbnail-item {
  width: 70px;
  height: 70px;
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.thumbnail-item:hover {
  border-color: #ffb3b3;
}

.thumbnail-item.active {
  border-color: #ff6b6b;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
}

.product-info {
  flex: 1;
}

.product-header {
  margin-bottom: 20px;
}

.product-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tag {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 4px;
  font-weight: 500;
}

.new-tag {
  background: #67c23a;
  color: #fff;
}

.hot-tag {
  background: #ff4757;
  color: #fff;
}

.product-name {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.product-summary {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.price-section {
  padding: 20px;
  background: #fff5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 15px;
  margin-bottom: 12px;
}

.price-label {
  font-size: 14px;
  color: #999;
}

.current-price {
  font-size: 28px;
  font-weight: 700;
  color: #ff4757;
}

.original-price {
  font-size: 14px;
  color: #999;
  text-decoration: line-through;
}

.discount-tag {
  padding: 2px 8px;
  background: #ff4757;
  color: #fff;
  font-size: 12px;
  border-radius: 4px;
  font-weight: 500;
}

.promo-row {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.promo-label {
  font-size: 14px;
  color: #999;
}

.promo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.promo-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.promo-tag {
  padding: 2px 6px;
  background: #ff6b6b;
  color: #fff;
  font-size: 12px;
  border-radius: 2px;
}

.promo-text {
  font-size: 13px;
  color: #666;
}

.specs-section {
  margin-bottom: 20px;
}

.specs-row {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  margin-bottom: 15px;
}

.specs-label {
  font-size: 14px;
  color: #999;
  width: 60px;
  flex-shrink: 0;
  padding-top: 8px;
}

.specs-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.specs-option {
  padding: 8px 20px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.specs-option:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.specs-option.active {
  border-color: #ff6b6b;
  background: #fff5f5;
  color: #ff6b6b;
}

.quantity-section {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
}

.quantity-label {
  font-size: 14px;
  color: #999;
  width: 60px;
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stock-info {
  font-size: 13px;
  color: #999;
}

.action-section {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.action-btn {
  height: 50px;
  min-width: 140px;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.buy-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
}

.cart-btn {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.cart-btn:hover {
  background: #fff5f5;
}

.favorite-btn {
  border-color: #e0e0e0;
  color: #666;
}

.service-section {
  display: flex;
  gap: 30px;
  padding: 15px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 15px;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.service-item .el-icon {
  color: #67c23a;
}

.share-section {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 13px;
  color: #999;
}

.share-icons {
  display: flex;
  gap: 15px;
  font-size: 20px;
}

.share-icons .el-icon {
  cursor: pointer;
  transition: color 0.2s;
}

.share-icons .el-icon:hover {
  color: #ff6b6b;
}

.product-tabs {
  background: #fff;
  border-radius: 8px;
}

.detail-tabs {
  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 20px;
    background: #fafafa;
    border-radius: 8px 8px 0 0;
  }
  
  :deep(.el-tabs__item) {
    height: 50px;
    line-height: 50px;
    font-size: 14px;
  }
  
  :deep(.el-tabs__item.is-active) {
    color: #ff6b6b;
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #ff6b6b;
  }
}

.tab-content {
  padding: 30px;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 30px;
}

.info-item {
  display: flex;
  font-size: 14px;
}

.info-label {
  color: #999;
  width: 80px;
}

.info-value {
  color: #333;
}

.description-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.description-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
}

.description-section p {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin-bottom: 20px;
}

.description-images {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}

.desc-image {
  max-width: 600px;
  border-radius: 8px;
}

.specs-table {
  width: 100%;
  border-collapse: collapse;
}

.specs-table tr {
  border-bottom: 1px solid #f0f0f0;
}

.specs-table td {
  padding: 15px 20px;
  font-size: 14px;
}

.specs-label-cell {
  width: 120px;
  background: #fafafa;
  color: #999;
}

.specs-value-cell {
  color: #333;
}

.reviews-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.rating-display {
  display: flex;
  align-items: center;
  gap: 20px;
}

.rating-score {
  font-size: 36px;
  font-weight: 700;
  color: #ff6b6b;
}

.rating-count {
  font-size: 13px;
  color: #999;
}

.rating-tags {
  display: flex;
  gap: 10px;
}

.tag-item {
  padding: 6px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-item:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.tag-item.active {
  background: #ff6b6b;
  border-color: #ff6b6b;
  color: #fff;
}

.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.review-item {
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-weight: 600;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.review-time {
  margin-left: auto;
  font-size: 13px;
  color: #999;
}

.review-content {
  font-size: 14px;
  color: #333;
  line-height: 1.8;
  margin-bottom: 12px;
}

.review-images {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.review-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  cursor: pointer;
}

.review-specs {
  font-size: 12px;
  color: #999;
  padding-top: 10px;
  border-top: 1px solid #e0e0e0;
}
</style>
