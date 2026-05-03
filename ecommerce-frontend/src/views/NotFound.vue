<template>
  <div class="not-found-page">
    <div class="not-found-container">
      <div class="not-found-image">
        <el-icon :size="120"><WarningFilled /></el-icon>
      </div>
      <div class="not-found-content">
        <h1 class="error-code">404</h1>
        <h2 class="error-title">页面不存在</h2>
        <p class="error-desc">
          抱歉，您访问的页面不存在或已被移除
        </p>
        <div class="error-actions">
          <el-button type="primary" size="large" @click="goHome">
            <el-icon><HomeFilled /></el-icon>
            返回首页
          </el-button>
          <el-button size="large" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回上一页
          </el-button>
        </div>
        <div class="suggestions">
          <h3>您可能想访问：</h3>
          <div class="suggestion-list">
            <router-link to="/" class="suggestion-item">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </router-link>
            <router-link to="/products" class="suggestion-item">
              <el-icon><ShoppingBag /></el-icon>
              <span>商品列表</span>
            </router-link>
            <router-link to="/cart" class="suggestion-item">
              <el-icon><ShoppingCart /></el-icon>
              <span>购物车</span>
            </router-link>
            <router-link to="/orders" class="suggestion-item">
              <el-icon><Document /></el-icon>
              <span>我的订单</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-page {
  min-height: calc(100vh - 200px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.not-found-image {
  color: #ff6b6b;
  margin-bottom: 30px;
}

.not-found-content {
  max-width: 500px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: #ff6b6b;
  margin: 0 0 10px 0;
  line-height: 1;
  text-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.error-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
}

.error-desc {
  font-size: 16px;
  color: #999;
  margin: 0 0 30px 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 40px;
}

.suggestions {
  padding-top: 30px;
  border-top: 1px solid #f0f0f0;
}

.suggestions h3 {
  font-size: 16px;
  font-weight: 500;
  color: #666;
  margin: 0 0 20px 0;
}

.suggestion-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.suggestion-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  text-decoration: none;
  color: #666;
  transition: all 0.2s;
}

.suggestion-item:hover {
  background: #fff5f5;
  color: #ff6b6b;
  transform: translateY(-2px);
}

.suggestion-item .el-icon {
  font-size: 28px;
  color: #999;
  transition: color 0.2s;
}

.suggestion-item:hover .el-icon {
  color: #ff6b6b;
}

.suggestion-item span {
  font-size: 14px;
}
</style>
