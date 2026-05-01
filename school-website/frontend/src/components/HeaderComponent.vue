<template>
  <header class="header-container">
    <el-container>
      <el-header class="main-header">
        <div class="header-content">
          <div class="logo-section" @click="goHome">
            <div class="logo-icon">
              <el-icon :size="36"><School /></el-icon>
            </div>
            <div class="logo-text">
              <h1 class="school-name">XX大学</h1>
              <p class="school-motto">XX University</p>
            </div>
          </div>
          
          <nav class="nav-section">
            <el-menu
              :default-active="activeMenu"
              class="nav-menu"
              mode="horizontal"
              :ellipsis="false"
              router
            >
              <el-menu-item index="/">
                <el-icon><HomeFilled /></el-icon>
                <span>首页</span>
              </el-menu-item>
              
              <el-sub-menu index="graduate">
                <template #title>
                  <el-icon><User /></el-icon>
                  <span>研究生</span>
                </template>
                <el-menu-item index="/graduate/admission">
                  <el-icon><Document /></el-icon>
                  <span>招生信息</span>
                </el-menu-item>
                <el-menu-item index="/graduate/college">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>学院介绍</span>
                </el-menu-item>
                <el-menu-item index="/graduate/news">
                  <el-icon><Bell /></el-icon>
                  <span>重要新闻</span>
                </el-menu-item>
              </el-sub-menu>
              
              <el-sub-menu index="undergraduate">
                <template #title>
                  <el-icon><Avatar /></el-icon>
                  <span>本科生</span>
                </template>
                <el-menu-item index="/undergraduate/admission">
                  <el-icon><Document /></el-icon>
                  <span>招生信息</span>
                </el-menu-item>
                <el-menu-item index="/undergraduate/college">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>学院介绍</span>
                </el-menu-item>
                <el-menu-item index="/undergraduate/news">
                  <el-icon><Bell /></el-icon>
                  <span>重要新闻</span>
                </el-menu-item>
              </el-sub-menu>
              
              <el-sub-menu index="doctoral">
                <template #title>
                  <el-icon><Trophy /></el-icon>
                  <span>博士生</span>
                </template>
                <el-menu-item index="/doctoral/admission">
                  <el-icon><Document /></el-icon>
                  <span>招生信息</span>
                </el-menu-item>
                <el-menu-item index="/doctoral/college">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>学院介绍</span>
                </el-menu-item>
                <el-menu-item index="/doctoral/news">
                  <el-icon><Bell /></el-icon>
                  <span>重要新闻</span>
                </el-menu-item>
              </el-sub-menu>
              
              <el-menu-item index="/personal/login">
                <el-icon v-if="!userStore.isLoggedIn"><UserFilled /></el-icon>
                <el-icon v-else><User /></el-icon>
                <span>{{ userStore.isLoggedIn ? '个人中心' : '登录' }}</span>
              </el-menu-item>
            </el-menu>
          </nav>
          
          <div class="user-section" v-if="userStore.isLoggedIn">
            <el-dropdown trigger="click">
              <span class="user-dropdown">
                <el-avatar :size="36" class="user-avatar">
                  {{ userStore.userName.charAt(0) }}
                </el-avatar>
                <span class="user-name">{{ userStore.userName }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goToUserInfo">
                    <el-icon><User /></el-icon>
                    <span>个人信息</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    <span>退出登录</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
    </el-container>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/') return '/'
  if (path.startsWith('/graduate')) return 'graduate'
  if (path.startsWith('/undergraduate')) return 'undergraduate'
  if (path.startsWith('/doctoral')) return 'doctoral'
  if (path.startsWith('/personal')) return '/personal/login'
  return path
})

const goHome = () => {
  router.push('/')
}

const goToUserInfo = () => {
  router.push('/personal/info')
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
  background: linear-gradient(135deg, #0a4b8e 0%, #1d6fb8 100%);
  box-shadow: 0 0.125rem 0.75rem rgba(0, 0, 0, 0.1);
}

.main-header {
  height: 3.75rem !important;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 75rem;
  margin: 0 auto;
  padding: 0 1.25rem;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.logo-icon {
  width: 3.125rem;
  height: 3.125rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo-text {
  color: #fff;
}

.school-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.2;
}

.school-motto {
  font-size: 0.75rem;
  opacity: 0.9;
  margin: 0;
  line-height: 1.2;
  font-style: italic;
}

.nav-section {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-menu {
  background: transparent;
  border: none;
}

.nav-menu :deep(.el-menu-item),
.nav-menu :deep(.el-sub-menu__title) {
  height: 3.75rem;
  line-height: 3.75rem;
  color: rgba(255, 255, 255, 0.9);
  border-bottom: 0.125rem solid transparent;
  padding: 0 1rem;
  transition: all 0.3s ease;
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.15);
  border-bottom-color: #fff;
  color: #fff;
}

.nav-menu :deep(.el-sub-menu .el-menu) {
  background: #0a4b8e;
  border: none;
}

.nav-menu :deep(.el-sub-menu .el-menu-item) {
  color: rgba(255, 255, 255, 0.9);
}

.nav-menu :deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.user-section {
  margin-left: 1.25rem;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 1.25rem;
  transition: background 0.3s ease;
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: #fff;
  font-weight: 600;
}

.user-name {
  color: #fff;
  font-size: 0.875rem;
}
</style>
