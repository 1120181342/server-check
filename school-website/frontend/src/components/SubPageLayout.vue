<template>
  <div class="sub-page-layout">
    <!-- 页面头部横幅 -->
    <div class="page-banner">
      <img :src="bannerImage" :alt="pageTitle" class="banner-image" />
      <div class="banner-overlay">
        <div class="banner-content">
          <h1 class="page-title">{{ pageTitle }}</h1>
          <p class="page-subtitle">{{ pageSubtitle }}</p>
        </div>
      </div>
    </div>

    <!-- 面包屑导航 -->
    <div class="breadcrumb-container">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-breadcrumb-item>
        <el-breadcrumb-item>{{ parentTitle }}</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentNav }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content-wrapper">
      <div class="content-container">
        <!-- 侧边导航 -->
        <aside class="side-nav">
          <div class="side-nav-header">
            <h3 class="nav-parent-title">{{ parentTitle }}</h3>
          </div>
          <el-menu
            :default-active="activeMenu"
            class="side-nav-menu"
            router
            background-color="#fff"
            text-color="#606266"
            active-text-color="#409eff"
          >
            <el-menu-item
              v-for="(item, index) in navItems"
              :key="index"
              :index="item.path"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </aside>

        <!-- 内容区域 -->
        <main class="content-area">
          <slot name="content"></slot>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  pageTitle: {
    type: String,
    required: true
  },
  pageSubtitle: {
    type: String,
    default: ''
  },
  parentTitle: {
    type: String,
    required: true
  },
  parentRoute: {
    type: String,
    required: true
  },
  bannerImage: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const router = useRouter()

const navItems = computed(() => {
  const basePath = props.parentRoute
  return [
    {
      title: '招生信息',
      icon: 'Document',
      path: `${basePath}/admission`
    },
    {
      title: '学院介绍',
      icon: 'OfficeBuilding',
      path: `${basePath}/college`
    },
    {
      title: '重要新闻',
      icon: 'Bell',
      path: `${basePath}/news`
    }
  ]
})

const activeMenu = computed(() => {
  return route.path
})

const currentNav = computed(() => {
  const item = navItems.value.find(i => i.path === route.path)
  return item ? item.title : ''
})
</script>

<style scoped>
.sub-page-layout {
  min-height: 100vh;
}

/* 页面横幅 */
.page-banner {
  position: relative;
  height: 18.75rem;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(10, 75, 142, 0.8) 0%, rgba(103, 194, 58, 0.6) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-content {
  text-align: center;
  color: #fff;
}

.page-title {
  font-size: 2.25rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  text-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
}

.page-subtitle {
  font-size: 1.125rem;
  opacity: 0.95;
}

/* 面包屑导航 */
.breadcrumb-container {
  background: #fff;
  padding: 1rem 0;
  border-bottom: 0.0625rem solid #e4e7ed;
}

.breadcrumb-container :deep(.el-breadcrumb) {
  max-width: 75rem;
  margin: 0 auto;
  padding: 0 1.25rem;
}

.breadcrumb-container :deep(.el-breadcrumb__inner) {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.breadcrumb-container :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #409eff;
  font-weight: 500;
}

/* 主要内容区域 */
.main-content-wrapper {
  background: #f5f7fa;
  padding: 1.5rem 0;
}

.content-container {
  max-width: 75rem;
  margin: 0 auto;
  padding: 0 1.25rem;
  display: grid;
  grid-template-columns: 15.625rem 1fr;
  gap: 1.5rem;
}

/* 侧边导航 */
.side-nav {
  background: #fff;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 0.125rem 0.75rem rgba(0, 0, 0, 0.05);
  height: fit-content;
}

.side-nav-header {
  background: linear-gradient(135deg, #0a4b8e 0%, #1d6fb8 100%);
  padding: 1.25rem;
  text-align: center;
}

.nav-parent-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.side-nav-menu {
  border-right: none;
  padding: 0.5rem 0;
}

.side-nav-menu :deep(.el-menu-item) {
  height: 3.125rem;
  line-height: 3.125rem;
  margin: 0.125rem 0.75rem;
  border-radius: 0.375rem;
}

.side-nav-menu :deep(.el-menu-item:hover) {
  background: #ecf5ff;
}

.side-nav-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  color: #fff;
}

.side-nav-menu :deep(.el-menu-item.is-active:hover) {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
}

/* 内容区域 */
.content-area {
  background: #fff;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 0.125rem 0.75rem rgba(0, 0, 0, 0.05);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-banner {
    height: 12.5rem;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .content-container {
    grid-template-columns: 1fr;
  }
  
  .side-nav {
    order: -1;
  }
  
  .side-nav-menu {
    display: flex;
    overflow-x: auto;
    padding: 0.5rem;
  }
  
  .side-nav-menu :deep(.el-menu-item) {
    margin: 0 0.25rem;
    padding: 0 0.75rem;
    white-space: nowrap;
  }
}
</style>
