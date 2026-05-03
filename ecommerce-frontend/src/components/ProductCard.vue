<template>
  <el-card class="product-card" :class="{ 'flash-card': isFlash }" shadow="hover">
    <div class="product-image" @click="goToDetail">
      <el-image
        :src="product.image"
        :lazy="true"
        fit="cover"
        class="image"
      >
        <template #placeholder>
          <div class="image-placeholder">
            <el-icon :size="40"><Picture /></el-icon>
          </div>
        </template>
        <template #error>
          <div class="image-placeholder">
            <el-icon :size="40"><PictureFilled /></el-icon>
          </div>
        </template>
      </el-image>
      <div class="product-tags" v-if="product.isNew || product.isHot">
        <span v-if="product.isNew" class="tag new-tag">新品</span>
        <span v-if="product.isHot" class="tag hot-tag">热卖</span>
      </div>
      <div class="product-actions">
        <el-button type="primary" size="small" @click.stop="addToCart">
          <el-icon><ShoppingCart /></el-icon>
          加入购物车
        </el-button>
      </div>
    </div>
    <div class="product-info">
      <h3 class="product-name" @click="goToDetail">{{ product.name }}</h3>
      <p class="product-desc">{{ product.description }}</p>
      <div class="product-price">
        <span class="current-price">¥{{ product.discountPrice || product.price }}</span>
        <span v-if="product.discountPrice" class="original-price">¥{{ product.price }}</span>
      </div>
      <div class="product-meta">
        <span class="sales">销量 {{ product.sales }}</span>
        <span class="rating">
          <el-rate :model-value="product.rating" disabled :max="5" show-score text-color="#ff6b6b" />
        </span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useCartStore } from '@/store'
import { ElMessage } from 'element-plus'

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  isFlash: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()
const cartStore = useCartStore()

const goToDetail = () => {
  console.time('navigate-to-detail')
  router.push(`/products/${props.product.id}`)
  console.timeEnd('navigate-to-detail')
}

const addToCart = () => {
  console.time('add-to-cart')
  const result = cartStore.addItem(props.product, 1)
  if (result) {
    ElMessage.success('已加入购物车')
  }
  console.timeEnd('add-to-cart')
}
</script>

<style scoped>
.product-card {
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.flash-card {
  border: 2px solid #ff4757;
}

.product-image {
  position: relative;
  height: 240px;
  overflow: hidden;
}

.image {
  width: 100%;
  height: 100%;
  transition: transform 0.3s ease;
}

.product-image:hover .image {
  transform: scale(1.05);
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #ccc;
}

.product-tags {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
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

.product-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  opacity: 0;
  transform: translateY(100%);
  transition: all 0.3s ease;
}

.product-image:hover .product-actions {
  opacity: 1;
  transform: translateY(0);
}

.product-info {
  padding: 16px;
}

.product-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px 0;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-name:hover {
  color: #ff6b6b;
}

.product-desc {
  font-size: 12px;
  color: #999;
  margin: 0 0 12px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}

.current-price {
  font-size: 18px;
  font-weight: 700;
  color: #ff4757;
}

.original-price {
  font-size: 12px;
  color: #999;
  text-decoration: line-through;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #999;
}
</style>
