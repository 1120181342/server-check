<template>
  <div class="login-container">
    <!-- 背景区域 -->
    <div class="login-background">
      <img :src="backgroundImage" alt="校园背景" class="bg-image" />
      <div class="bg-overlay"></div>
      <div class="bg-content">
        <div class="bg-logo">
          <el-icon :size="48"><School /></el-icon>
        </div>
        <h1 class="bg-title">XX大学</h1>
        <p class="bg-subtitle">XX University</p>
        <p class="bg-slogan">厚德载物 · 自强不息</p>
      </div>
    </div>

    <!-- 登录表单区域 -->
    <div class="login-form-wrapper">
      <div class="login-form-container">
        <div class="login-header">
          <h2 class="login-title">用户登录</h2>
          <p class="login-subtitle">欢迎登录XX大学个人中心</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <!-- 用户类型选择 -->
          <div class="user-type-section">
            <el-radio-group v-model="loginForm.userType" size="large">
              <el-radio-button label="student">
                <el-icon><User /></el-icon>
                <span>学生</span>
              </el-radio-button>
              <el-radio-button label="teacher">
                <el-icon><Avatar /></el-icon>
                <span>教师</span>
              </el-radio-button>
              <el-radio-button label="admin">
                <el-icon><UserFilled /></el-icon>
                <span>管理员</span>
              </el-radio-button>
            </el-radio-group>
          </div>

          <!-- 用户名 -->
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入学号/工号"
              size="large"
              prefix-icon="User"
              clearable
            />
          </el-form-item>

          <!-- 密码 -->
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

          <!-- 验证码 -->
          <el-form-item prop="captcha">
            <div class="captcha-row">
              <el-input
                v-model="loginForm.captcha"
                placeholder="请输入验证码"
                size="large"
                prefix-icon="Picture"
                clearable
                style="flex: 1"
                @keyup.enter="handleLogin"
              />
              <div class="captcha-image" @click="refreshCaptcha">
                <img :src="captchaImage" alt="验证码" />
                <span class="refresh-text">点击刷新</span>
              </div>
            </div>
          </el-form-item>

          <!-- 记住密码 -->
          <el-form-item>
            <div class="login-options">
              <el-checkbox v-model="loginForm.rememberMe">记住密码</el-checkbox>
              <el-button type="primary" link class="forgot-password" @click="showForgotPassword">
                忘记密码?
              </el-button>
            </div>
          </el-form-item>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>

          <!-- 其他登录方式 -->
          <div class="other-login">
            <div class="divider">
              <span>其他登录方式</span>
            </div>
            <div class="login-methods">
              <el-button circle size="large" class="wechat-btn" title="微信登录">
                <el-icon :size="22"><ChatDotRound /></el-icon>
              </el-button>
              <el-button circle size="large" class="qq-btn" title="QQ登录">
                <el-icon :size="22"><ChatLineSquare /></el-icon>
              </el-button>
              <el-button circle size="large" class="phone-btn" title="手机验证码登录">
                <el-icon :size="22"><Phone /></el-icon>
              </el-button>
            </div>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog
      v-model="forgotPasswordVisible"
      title="找回密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="forgotForm.username" placeholder="请输入学号/工号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="forgotForm.email" placeholder="请输入注册邮箱" />
        </el-form-item>
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input v-model="forgotForm.code" placeholder="请输入验证码" style="flex: 1" />
            <el-button
              type="primary"
              size="small"
              :disabled="codeDisabled"
              @click="sendCode"
            >
              {{ codeText }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="forgotForm.newPassword" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="forgotForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="forgotPasswordVisible = false">取消</el-button>
        <el-button type="primary" :loading="forgotLoading" @click="handleResetPassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 登录相关
const loginFormRef = ref(null)
const loading = ref(false)

// 验证码
const captchaImage = ref('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=4%20digit%20numeric%20captcha%20image%20with%20distorted%20numbers%20security%20code&image_size=square')

const refreshCaptcha = () => {
  captchaImage.value = `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${Date.now()}%204%20digit%20numeric%20captcha%20image%20with%20distorted%20numbers%20security%20code&image_size=square`
}

// 背景图片
const backgroundImage = ref(
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=beautiful%20university%20campus%20with%20modern%20buildings%20green%20trees%20and%20lake%20sunset%20scenery&image_size=landscape_16_9'
)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  captcha: '',
  userType: 'student',
  rememberMe: false
})

// 登录校验规则
const loginRules = {
  username: [
    { required: true, message: '请输入学号/工号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

// 忘记密码相关
const forgotPasswordVisible = ref(false)
const forgotFormRef = ref(null)
const forgotLoading = ref(false)
const codeDisabled = ref(false)
const codeText = ref('获取验证码')
const codeTimer = ref(null)

const forgotForm = reactive({
  username: '',
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== forgotForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const forgotRules = {
  username: [
    { required: true, message: '请输入学号/工号', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const showForgotPassword = () => {
  forgotPasswordVisible.value = true
  // 重置表单
  forgotForm.username = ''
  forgotForm.email = ''
  forgotForm.code = ''
  forgotForm.newPassword = ''
  forgotForm.confirmPassword = ''
}

const sendCode = () => {
  if (!forgotForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  
  codeDisabled.value = true
  let countdown = 60
  codeText.value = `${countdown}s后重发`
  
  codeTimer.value = setInterval(() => {
    countdown--
    codeText.value = `${countdown}s后重发`
    if (countdown <= 0) {
      clearInterval(codeTimer.value)
      codeDisabled.value = false
      codeText.value = '获取验证码'
    }
  }, 1000)
  
  ElMessage.success('验证码已发送到您的邮箱')
}

const handleResetPassword = () => {
  forgotFormRef.value.validate(async (valid) => {
    if (valid) {
      forgotLoading.value = true
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      ElMessage.success('密码重置成功，请使用新密码登录')
      forgotPasswordVisible.value = false
      forgotLoading.value = false
    }
  })
}

// 登录处理
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      // 模拟登录API调用
      setTimeout(() => {
        // 模拟成功登录
        const userInfo = {
          id: 'U' + loginForm.username,
          name: loginForm.userType === 'student' ? '张三' : loginForm.userType === 'teacher' ? '李老师' : '管理员',
          role: loginForm.userType,
          email: `${loginForm.username}@xxuniversity.edu.cn`,
          phone: '138****8888',
          department: loginForm.userType === 'student' ? '计算机学院' : loginForm.userType === 'teacher' ? '电子工程学院' : '信息化管理处',
          avatar: '',
          enrollDate: '2021-09-01'
        }
        
        // 保存登录状态
        userStore.login('mock_token_' + Date.now(), userInfo)
        
        ElMessage.success('登录成功！')
        loading.value = false
        
        // 跳转到个人信息页面或之前访问的页面
        const redirect = route.query.redirect || '/personal/info'
        router.push(redirect)
      }, 1500)
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: calc(100vh - 3.75rem);
  display: flex;
  position: relative;
  overflow: hidden;
}

/* 背景区域 */
.login-background {
  flex: 1;
  position: relative;
  display: none;
}

@media (min-width: 992px) {
  .login-background {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.bg-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(10, 75, 142, 0.9) 0%, rgba(103, 194, 58, 0.8) 100%);
}

.bg-content {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #fff;
  padding: 2rem;
}

.bg-logo {
  width: 6.25rem;
  height: 6.25rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
}

.bg-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
}

.bg-subtitle {
  font-size: 1.25rem;
  opacity: 0.9;
  margin-bottom: 1.5rem;
  font-style: italic;
}

.bg-slogan {
  font-size: 1.125rem;
  opacity: 0.85;
  letter-spacing: 0.25rem;
}

/* 登录表单区域 */
.login-form-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.25rem;
  background: linear-gradient(180deg, #f5f7fa 0%, #e4e7ed 100%);
}

@media (min-width: 992px) {
  .login-form-wrapper {
    flex: 0 0 28.125rem;
    background: #fff;
  }
}

.login-form-container {
  width: 100%;
  max-width: 25rem;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.login-subtitle {
  font-size: 0.875rem;
  color: #909399;
}

/* 用户类型选择 */
.user-type-section {
  margin-bottom: 1.5rem;
}

.user-type-section :deep(.el-radio-button__inner) {
  width: 33.33%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.75rem 0;
  border: none;
}

/* 验证码 */
.captcha-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.captcha-image {
  width: 7.5rem;
  height: 2.5rem;
  border-radius: 0.25rem;
  overflow: hidden;
  border: 0.0625rem solid #dcdfe6;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  position: relative;
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
}

.refresh-text {
  position: relative;
  z-index: 1;
  font-size: 0.75rem;
  color: #606266;
  background: rgba(255, 255, 255, 0.9);
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}

.captcha-image:hover img {
  filter: blur(0.0625rem);
}

/* 登录选项 */
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.forgot-password {
  padding: 0 !important;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  background: linear-gradient(135deg, #0a4b8e 0%, #1d6fb8 100%);
  border: none;
  letter-spacing: 0.125rem;
  font-weight: 500;
}

.login-btn:hover {
  background: linear-gradient(135deg, #083d77 0%, #0a4b8e 100%);
}

/* 其他登录方式 */
.other-login {
  margin-top: 1.5rem;
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 0.0625rem;
  background: #e4e7ed;
}

.divider span {
  padding: 0 1rem;
  font-size: 0.75rem;
  color: #909399;
}

.login-methods {
  display: flex;
  justify-content: center;
  gap: 1.25rem;
}

.wechat-btn {
  background: #07c160;
  color: #fff;
  border: none;
}

.wechat-btn:hover {
  background: #06ad56;
  color: #fff;
}

.qq-btn {
  background: #12b7f5;
  color: #fff;
  border: none;
}

.qq-btn:hover {
  background: #0da5df;
  color: #fff;
}

.phone-btn {
  background: #ff6b00;
  color: #fff;
  border: none;
}

.phone-btn:hover {
  background: #e65f00;
  color: #fff;
}

/* 找回密码 */
.code-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
</style>
