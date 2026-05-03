<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-left">
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
          <h2>加入我们</h2>
          <p>注册新账户，享受专属优惠</p>
        </div>
        <div class="benefits">
          <div class="benefit-item">
            <div class="benefit-icon">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="benefit-info">
              <h4>新人专享</h4>
              <p>注册即送50元优惠券</p>
            </div>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon">
              <el-icon><Star /></el-icon>
            </div>
            <div class="benefit-info">
              <h4>会员特权</h4>
              <p>专属折扣 积分翻倍</p>
            </div>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon">
              <el-icon><Gift /></el-icon>
            </div>
            <div class="benefit-info">
              <h4>生日礼包</h4>
              <p>生日当月享好礼</p>
            </div>
          </div>
        </div>
      </div>

      <div class="register-right">
        <div class="register-header">
          <h2>用户注册</h2>
          <p>已有账户？<router-link to="/login" class="login-link">立即登录</router-link></p>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="register-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请设置用户名"
              size="large"
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="phone">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号"
              size="large"
              prefix-icon="Phone"
              maxlength="11"
            />
          </el-form-item>

          <el-form-item prop="code">
            <div class="code-input">
              <el-input
                v-model="registerForm.code"
                placeholder="请输入验证码"
                size="large"
                prefix-icon="Key"
                maxlength="6"
              />
              <el-button
                type="primary"
                size="large"
                :disabled="countdown > 0"
                @click="sendCode"
                class="code-btn"
              >
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </el-button>
            </div>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请设置密码（6-20位）"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <div class="agreement">
              <el-checkbox v-model="registerForm.agreed" />
              <span>我已阅读并同意</span>
              <a href="javascript:void(0)" class="agreement-link">《用户协议》</a>
              <span>和</span>
              <a href="javascript:void(0)" class="agreement-link">《隐私政策》</a>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="register-btn"
              :loading="loading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()

const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const countdown = ref(0)

const registerForm = reactive({
  username: '',
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
  agreed: false
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateAgreement = (rule: any, value: boolean, callback: any) => {
  if (!value) {
    callback(new Error('请先阅读并同意用户协议'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请设置用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度为2-20位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6-20位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreed: [
    { validator: validateAgreement, trigger: 'change' }
  ]
}

const sendCode = () => {
  if (!registerForm.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(registerForm.phone)) {
    ElMessage.warning('手机号格式不正确')
    return
  }
  
  countdown.value = 60
  ElMessage.success('验证码已发送')
  
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      console.time('register')
      loading.value = true
      
      setTimeout(() => {
        ElMessage.success('注册成功！请登录')
        router.push('/login')
        loading.value = false
        console.timeEnd('register')
      }, 800)
    }
  })
}

onMounted(() => {
  console.time('register-page-onMounted')
  console.timeEnd('register-page-onMounted')
})
</script>

<style scoped>
.register-page {
  min-height: calc(100vh - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 0;
}

.register-container {
  display: flex;
  width: 950px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-left {
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
  margin-bottom: 50px;
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

.benefits {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.benefit-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.benefit-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.benefit-info h4 {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.benefit-info p {
  font-size: 12px;
  opacity: 0.9;
  margin: 0;
}

.register-right {
  flex: 1;
  padding: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.register-header {
  margin-bottom: 30px;
}

.register-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin: 0 0 8px 0;
}

.register-header p {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.login-link {
  color: #ff6b6b;
  text-decoration: none;
}

.register-form {
  width: 100%;
}

.register-form :deep(.el-input__wrapper) {
  padding: 12px 15px;
  box-shadow: 0 0 0 1px #e0e0e0;
  border-radius: 8px;
}

.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #ff6b6b;
}

.code-input {
  display: flex;
  gap: 12px;
}

.code-input :deep(.el-form-item__content) {
  display: flex;
  gap: 12px;
}

.code-btn {
  width: 130px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
}

.code-btn:disabled {
  background: #e0e0e0;
}

.agreement {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  flex-wrap: wrap;
}

.agreement-link {
  color: #ff6b6b;
  text-decoration: none;
}

.register-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border: none;
  border-radius: 8px;
}
</style>
