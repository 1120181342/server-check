<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">
        <span class="code">404</span>
      </div>
      <div class="error-info">
        <h2 class="error-title">页面不存在</h2>
        <p class="error-message">抱歉，您访问的页面不存在或已被移除</p>
        <div class="error-actions">
          <el-button type="primary" @click="goHome">
            <el-icon><HomeFilled /></el-icon>
            返回首页
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回上一页
          </el-button>
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
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.not-found-container {
  min-height: calc(100vh - 3.75rem - 18.75rem);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f5f7fa 0%, #e4e7ed 100%);
  padding: 3rem 1.25rem;
}

.not-found-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.error-code {
  margin-bottom: 2rem;
}

.code {
  font-size: 10rem;
  font-weight: 700;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0.25rem 3.75rem rgba(64, 158, 255, 0.3);
  line-height: 1;
}

.error-info {
  max-width: 25rem;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.75rem;
}

.error-message {
  font-size: 1rem;
  color: #606266;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

@media (max-width: 768px) {
  .code {
    font-size: 6rem;
  }
  
  .error-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .error-actions .el-button {
    width: 100%;
  }
}
</style>
