<template>
  <div class="home-page">
    <section class="banner-section">
      <el-carousel :interval="4000" height="400px" indicator-position="outside">
        <el-carousel-item v-for="banner in banners" :key="banner.id">
          <div class="banner-item" :style="{ background: banner.background }">
            <div class="container">
              <div class="banner-content">
                <h2>{{ banner.title }}</h2>
                <p>{{ banner.subtitle }}</p>
                <el-button type="primary" size="large" @click="goToProducts(banner.link)">
                  {{ banner.buttonText }}
                </el-button>
              </div>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </section>

    <section class="category-section">
      <div class="container">
        <div class="category-grid">
          <div 
            v-for="category in categories" 
            :key="category.id" 
            class="category-card"
            @click="goToCategory(category.id)"
          >
            <div class="category-icon">
              <el-icon :size="36"><component :is="category.icon" /></el-icon>
            </div>
            <div class="category-info">
              <h3>{{ category.name }}</h3>
              <p>{{ category.children?.slice(0, 3).map(c => c.name).join(' / ') || '热门商品' }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="flash-sale-section">
      <div class="container">
        <div class="section-header">
          <h2>
            <el-icon><Fire /></el-icon>
            限时抢购
          </h2>
          <div class="countdown" v-if="flashSaleEndTime">
            <span>距结束</span>
            <span class="time-box">{{ countdown.hours }}</span>
            <span>:</span>
            <span class="time-box">{{ countdown.minutes }}</span>
            <span>:</span>
            <span class="time-box">{{ countdown.seconds }}</span>
          </div>
        </div>
        <div class="product-grid">
          <ProductCard 
            v-for="product in flashSaleProducts" 
            :key="product.id" 
            :product="product"
            :is-flash="true"
          />
        </div>
      </div>
    </section>

    <section class="hot-products-section">
      <div class="container">
        <div class="section-header">
          <h2>
            <el-icon><TrendCharts /></el-icon>
            热卖推荐
          </h2>
          <router-link to="/products?sort=sales" class="more-link">
            查看更多
            <el-icon><ArrowRight /></el-icon>
          </router-link>
        </div>
        <div class="product-grid">
          <ProductCard 
            v-for="product in hotProducts" 
            :key="product.id" 
            :product="product"
          />
        </div>
      </div>
    </section>

    <section class="new-products-section">
      <div class="container">
        <div class="section-header">
          <h2>
            <el-icon><Promotion /></el-icon>
            新品上市
          </h2>
          <router-link to="/products?sort=new" class="more-link">
            查看更多
            <el-icon><ArrowRight /></el-icon>
          </router-link>
        </div>
        <div class="product-grid">
          <ProductCard 
            v-for="product in newProducts" 
            :key="product.id" 
            :product="product"
          />
        </div>
      </div>
    </section>

    <section class="brand-section">
      <div class="container">
        <div class="section-header">
          <h2>
            <el-icon><Medal /></el-icon>
            品牌专区
          </h2>
        </div>
        <div class="brand-grid">
          <div 
            v-for="brand in brands" 
            :key="brand.id" 
            class="brand-card"
            @click="goToBrand(brand.name)"
          >
            <div class="brand-logo" :style="{ background: brand.color }">
              <span>{{ brand.name.charAt(0) }}</span>
            </div>
            <div class="brand-info">
              <h3>{{ brand.name }}</h3>
              <p>{{ brand.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProductStore } from '@/store'
import ProductCard from '@/components/ProductCard.vue'

const router = useRouter()
const productStore = useProductStore()

const categories = ref([])
const hotProducts = ref([])
const newProducts = ref([])
const flashSaleProducts = ref([])
const flashSaleEndTime = ref(null)
const countdownTimer = ref(null)

const countdown = computed(() => {
  if (!flashSaleEndTime.value) {
    return { hours: '00', minutes: '00', seconds: '00' }
  }
  const now = Date.now()
  const diff = flashSaleEndTime.value - now
  if (diff <= 0) {
    return { hours: '00', minutes: '00', seconds: '00' }
  }
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  return {
    hours: String(hours).padStart(2, '0'),
    minutes: String(minutes).padStart(2, '0'),
    seconds: String(seconds).padStart(2, '0')
  }
})

const banners = [
  {
    id: 1,
    title: '双11狂欢节',
    subtitle: '全场低至5折起',
    buttonText: '立即抢购',
    link: '/products?sort=sales',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    id: 2,
    title: '新品首发',
    subtitle: '最新科技产品抢先体验',
    buttonText: '查看新品',
    link: '/products?sort=new',
    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    id: 3,
    title: '品牌特卖',
    subtitle: '精选大牌 限时优惠',
    buttonText: '进入品牌',
    link: '/products',
    background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  }
]

const brands = [
  { id: 1, name: 'Apple', color: '#333', description: '创新科技，改变世界' },
  { id: 2, name: '华为', color: '#CF0A2C', description: '连接世界，共创未来' },
  { id: 3, name: '小米', color: '#FF6700', description: '让每个人都能享受科技的乐趣' },
  { id: 4, name: '索尼', color: '#000', description: '创新源于好奇' },
  { id: 5, name: '戴森', color: '#212121', description: '重新定义科技' },
  { id: 6, name: '海尔', color: '#009DE0', description: '以用户为中心的创新' }
]

onMounted(() => {
  console.time('home-onMounted')
  
  categories.value = productStore.getCategories()
  hotProducts.value = productStore.getHotProducts(8)
  newProducts.value = productStore.getNewProducts(8)
  flashSaleProducts.value = productStore.getHotProducts(4)
  
  flashSaleEndTime.value = Date.now() + 2 * 60 * 60 * 1000
  countdownTimer.value = setInterval(() => {
    if (Date.now() >= flashSaleEndTime.value) {
      clearInterval(countdownTimer.value)
    }
  }, 1000)
  
  console.timeEnd('home-onMounted')
})

onUnmounted(() => {
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
  }
})

const goToProducts = (path) => {
  console.time('navigate-to-products')
  router.push(path)
  console.timeEnd('navigate-to-products')
}

const goToCategory = (categoryId) => {
  console.time('navigate-to-category')
  router.push({
    path: '/products',
    query: { category: categoryId }
  })
  console.timeEnd('navigate-to-category')
}

const goToBrand = (brandName) => {
  router.push({
    path: '/products',
    query: { keyword: brandName }
  })
}
</script>

<style scoped>
.home-page {
  background: #f5f5f5;
}

.banner-section {
  margin-top: 20px;
}

.banner-item {
  height: 400px;
  display: flex;
  align-items: center;
}

.banner-content {
  color: #fff;
  padding: 0 60px;
}

.banner-content h2 {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 16px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.banner-content p {
  font-size: 24px;
  margin: 0 0 24px 0;
  opacity: 0.9;
}

.category-section {
  padding: 30px 0;
  background: #fff;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}

.category-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-card:hover {
  background: #fff5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.category-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
}

.category-info p {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.more-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #ff6b6b;
  text-decoration: none;
  transition: color 0.2s;
}

.more-link:hover {
  color: #ee5a6f;
}

.flash-sale-section,
.hot-products-section,
.new-products-section,
.brand-section {
  padding: 30px 0;
}

.flash-sale-section {
  background: #fff;
}

.countdown {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #666;
}

.time-box {
  background: #ff4757;
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  min-width: 30px;
  text-align: center;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.brand-section {
  background: #fff;
}

.brand-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.brand-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.brand-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.brand-logo {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.brand-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
}

.brand-info p {
  font-size: 13px;
  color: #999;
  margin: 0;
}
</style>
