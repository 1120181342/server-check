<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="logo-section">
          <div class="logo-icon">
            <el-icon :size="48"><ShoppingBag /></el-icon>
          </div>
          <div class="logo-text">
            <h1>优选商城</h1>
            <p>品质生活从这里开始</p>
          </div>
        </div>
        <div class="welcome-text">
          <h2>欢迎回来</h2>
          <p>登录您的账户，享受更多优惠</p>
        </div>
        <div class="features">
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>正品保障 假一赔十</span>
          </div>
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>7天无理由退换</span>
          </div>
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>专属会员优惠</span>
          </div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-header">
          <h2>用户登录</h2>
          <p>还没有账户？<router-link to="/register" class="register-link">立即注册</router-link></p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名/手机号"
              size="large"
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <div class="login-options">
              <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
              <a href="javascript:void(0)" class="forgot-link">忘记密码？</a>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>

          <el-divider content-position="center">其他登录方式</el-divider>

          <div class="other-login">
            <el-button type="text" class="login-method">
              <el-icon :size="28" style="color: #07c160"><ChatDotRound /></el-icon>
              <span>微信</span>
            </el-button>
            <el-button type="text" class="login-method">
              <el-icon :size="28" style="color: #1677ff"><Wallet /></el-icon>
              <span>支付宝</span>
            </el-button>
            <el-button type="text" class="login-method">
              <el-icon :size="28" style="color: #1da1f2"><Message /></el-icon>
              <span>微博</span>
            </el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: true
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      console.time('login')
      loading.value = true
      
      setTimeout(() => {
        userStore.login(
          'mock_token_' + Date.now(),
          {
            name: loginForm.username,
            avatar: '',
            level: 1,
            phone: loginForm.username.length === 11 ? loginForm.username : '138****0000',
            email: `${loginForm.username}@example.com`
          }
        )
        
        ElMessage.success('登录成功！')
        
        const redirect = route.query.redirect as string || '/'
        router.push(redirect)
        
        loading.value = false
        console.timeEnd('login')
      }, 500)
    }
  })
}

onMounted(() => {
  console.time('login-page-onMounted')
  console.timeEnd('login-page-onMounted')
})
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 0;
}

.login-container {
  display: flex;
  width: 900px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-left {
  width: 380px;
  padding: 50px 40px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 60px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.logo-text p {
  font-size: 12px;
  opacity: 0.9;
  margin: 0;
}

.welcome-text {
  margin-bottom: 40px;
}

.welcome-text h2 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.welcome-text p {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.features {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  opacity: 0.95;
}

.login-right {
  flex: 1;
  padding: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-header {
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin: 0 0 8px 0;
}

.login-header p {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.register-link {
  color: #ff6b6b;
  text-decoration: none;
}

.login-form {
  width: 100%;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 15px;
  box-shadow: 0 0 0 1px #e0e0e0;
  border-radius: 8px;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #ff6b6b;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-size: 13px;
}

.forgot-link {
  color: #999;
  text-decoration: none;
}

.forgot-link:hover {
  color: #ff6b6b;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
  border-radius: 8px;
}

.other-login {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.login-method {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0;
}

.login-method span {
  font-size: 12px;
  color: #999;
}
</style>
