<template>
  <header class="header-container">
    <div class="top-bar">
      <div class="container">
        <div class="top-bar-content">
          <span class="welcome-text">欢迎来到优选商城！</span>
          <div class="top-bar-actions">
            <router-link v-if="!userStore.isLoggedIn" to="/login" class="action-item">
              <el-icon><UserFilled /></el-icon>
              <span>登录</span>
            </router-link>
            <router-link v-if="!userStore.isLoggedIn" to="/register" class="action-item">
              <el-icon><Edit /></el-icon>
              <span>注册</span>
            </router-link>
            <template v-else>
              <router-link to="/user" class="action-item">
                <el-icon><User /></el-icon>
                <span>{{ userStore.userName }}</span>
              </router-link>
              <router-link to="/orders" class="action-item">
                <el-icon><Document /></el-icon>
                <span>我的订单</span>
              </router-link>
              <a href="javascript:void(0)" class="action-item" @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出</span>
              </a>
            </template>
          </div>
        </div>
      </div>
    </div>
    
    <div class="main-header">
      <div class="container">
        <div class="header-content">
          <div class="logo-section" @click="goHome">
            <div class="logo-icon">
              <el-icon :size="40"><ShoppingBag /></el-icon>
            </div>
            <div class="logo-text">
              <h1 class="site-name">优选商城</h1>
              <p class="site-slogan">品质生活从这里开始</p>
            </div>
          </div>
          
          <div class="search-section">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索商品"
              class="search-input"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #append>
                <el-button type="primary" @click="handleSearch">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
              </template>
            </el-input>
            <div class="hot-keywords">
              <span class="label">热门搜索：</span>
              <span 
                v-for="keyword in hotKeywords" 
                :key="keyword" 
                class="keyword"
                @click="quickSearch(keyword)"
              >
                {{ keyword }}
              </span>
            </div>
          </div>
          
          <div class="cart-section" @click="goCart">
            <div class="cart-icon">
              <el-icon :size="24"><ShoppingCart /></el-icon>
              <el-badge :value="cartStore.totalCount" :max="99" class="cart-badge" />
            </div>
            <div class="cart-info">
              <span class="cart-label">购物车</span>
              <span class="cart-count">¥{{ cartStore.selectedTotal.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="nav-bar">
      <div class="container">
        <div class="nav-content">
          <div class="category-menu" @mouseenter="showCategory = true" @mouseleave="showCategory = false">
            <div class="category-trigger">
              <el-icon><Grid /></el-icon>
              <span>全部商品分类</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <div class="category-dropdown" v-show="showCategory">
              <div 
                v-for="category in categories" 
                :key="category.id" 
                class="category-item"
                @click="goCategory(category.id)"
              >
                <el-icon><component :is="category.icon" /></el-icon>
                <span class="category-name">{{ category.name }}</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
          
          <nav class="main-nav">
            <router-link 
              v-for="nav in navItems" 
              :key="nav.name"
              :to="nav.path"
              class="nav-item"
              :class="{ active: isActiveNav(nav) }"
            >
              {{ nav.name }}
              <span v-if="nav.badge" class="nav-badge">{{ nav.badge }}</span>
            </router-link>
          </nav>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, useCartStore, useProductStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const cartStore = useCartStore()
const productStore = useProductStore()

const searchKeyword = ref('')
const showCategory = ref(false)
const categories = ref([])

const hotKeywords = ['iPhone', '华为', 'MacBook', '戴森', '耳机', '洗衣机']

const navItems = [
  { name: '首页', path: '/', badge: null },
  { name: '新品上市', path: '/products?sort=new', badge: 'NEW' },
  { name: '热卖推荐', path: '/products?sort=sales', badge: 'HOT' },
  { name: '限时优惠', path: '/products?discount=true', badge: '5折' },
  { name: '品牌专区', path: '/products?brand=true', badge: null }
]

const isActiveNav = (nav) => {
  if (nav.path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(nav.path.split('?')[0])
}

onMounted(() => {
  categories.value = productStore.getCategories()
})

const goHome = () => {
  router.push('/')
}

const goCart = () => {
  router.push('/cart')
}

const goCategory = (categoryId) => {
  router.push({
    path: '/products',
    query: { category: categoryId }
  })
  showCategory.value = false
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/products',
      query: { keyword: searchKeyword.value.trim() }
    })
  }
}

const quickSearch = (keyword) => {
  searchKeyword.value = keyword
  router.push({
    path: '/products',
    query: { keyword }
  })
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.header-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.top-bar {
  background: #f5f5f5;
  border-bottom: 1px solid #eee;
  padding: 8px 0;
  font-size: 12px;
}

.top-bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text {
  color: #666;
}

.top-bar-actions {
  display: flex;
  gap: 20px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  text-decoration: none;
  transition: color 0.2s;
}

.action-item:hover {
  color: #ff6b6b;
}

.main-header {
  padding: 20px 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 40px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.site-name {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin: 0;
  line-height: 1.2;
}

.site-slogan {
  font-size: 12px;
  color: #999;
  margin: 0;
  line-height: 1.2;
}

.search-section {
  flex: 1;
  max-width: 600px;
}

.search-input {
  :deep(.el-input__wrapper) {
    border-radius: 25px 0 0 25px;
    box-shadow: 0 0 0 2px #ff6b6b;
  }
  
  :deep(.el-input-group__append) {
    padding: 0;
    border: none;
    background: transparent;
    
    .el-button {
      height: 100%;
      border-radius: 0 25px 25px 0;
      border: none;
    }
  }
}

.hot-keywords {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}

.label {
  color: #999;
}

.keyword {
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.keyword:hover {
  color: #ff6b6b;
}

.cart-section {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 2px solid #ff6b6b;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.cart-section:hover {
  background: #fff5f5;
}

.cart-icon {
  position: relative;
  color: #ff6b6b;
}

.cart-badge {
  position: absolute;
  top: -10px;
  right: -10px;
}

.cart-info {
  display: flex;
  flex-direction: column;
}

.cart-label {
  font-size: 12px;
  color: #666;
}

.cart-count {
  font-size: 14px;
  font-weight: 600;
  color: #ff6b6b;
}

.nav-bar {
  background: #333;
}

.nav-content {
  display: flex;
  align-items: stretch;
}

.category-menu {
  position: relative;
  width: 200px;
  background: #ff6b6b;
  cursor: pointer;
}

.category-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  color: #fff;
  font-weight: 500;
}

.category-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 200px;
  background: #fff;
  border: 1px solid #eee;
  border-top: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  color: #333;
  transition: all 0.2s;
  border-bottom: 1px solid #f5f5f5;
}

.category-item:hover {
  background: #fff5f5;
  color: #ff6b6b;
}

.category-name {
  flex: 1;
  margin-left: 10px;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 0;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 14px 30px;
  color: #fff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-item:hover,
.nav-item.active {
  background: #ff6b6b;
}

.nav-badge {
  position: absolute;
  top: 6px;
  right: 15px;
  font-size: 10px;
  color: #fff;
  background: #ff4757;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
