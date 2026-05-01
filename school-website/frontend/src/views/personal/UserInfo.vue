<template>
  <div class="user-info-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <img :src="bannerImage" alt="背景" class="header-bg" />
        <div class="header-overlay"></div>
        <div class="user-card">
          <div class="avatar-section">
            <el-avatar :size="80" class="user-avatar">
              <img :src="userAvatar" v-if="userStore.userInfo.avatar" :alt="userStore.userInfo.name" />
              <span v-else>{{ userStore.userName.charAt(0) }}</span>
            </el-avatar>
            <el-button type="primary" size="small" class="change-avatar-btn" @click="showAvatarUpload">
              更换头像
            </el-button>
          </div>
          <div class="user-info-basic">
            <h2 class="user-name">{{ userStore.userInfo.name }}</h2>
            <div class="user-tags">
              <el-tag :type="getUserRoleType(userStore.userRole)" size="small">
                {{ getUserRoleName(userStore.userRole) }}
              </el-tag>
              <el-tag type="info" size="small" effect="plain">
                {{ userStore.userInfo.department }}
              </el-tag>
            </div>
            <p class="user-id">学号/工号：{{ userStore.userInfo.id }}</p>
          </div>
          <div class="user-actions">
            <el-button type="primary" @click="activeTab = 'edit'">
              <el-icon><Edit /></el-icon>
              编辑资料
            </el-button>
            <el-button @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-tabs v-model="activeTab" class="user-tabs">
        <!-- 个人信息 -->
        <el-tab-pane label="个人信息" name="info">
          <div class="tab-content">
            <el-row :gutter="30">
              <el-col :xs="24" :md="16">
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span class="card-title">基本信息</span>
                    </div>
                  </template>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="姓名">
                      {{ userStore.userInfo.name }}
                    </el-descriptions-item>
                    <el-descriptions-item label="性别">
                      {{ userForm.gender || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="学号/工号">
                      {{ userStore.userInfo.id }}
                    </el-descriptions-item>
                    <el-descriptions-item label="民族">
                      {{ userForm.nation || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="学院/部门">
                      {{ userStore.userInfo.department }}
                    </el-descriptions-item>
                    <el-descriptions-item label="政治面貌">
                      {{ userForm.politicalStatus || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="入学时间">
                      {{ userStore.userInfo.enrollDate || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="学制">
                      {{ userForm.studyYears || '未填写' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>

                <el-card class="info-card" style="margin-top: 1.5rem">
                  <template #header>
                    <div class="card-header">
                      <span class="card-title">联系方式</span>
                    </div>
                  </template>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="手机号码">
                      {{ userStore.userInfo.phone || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="电子邮箱">
                      {{ userStore.userInfo.email || '未填写' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="家庭住址" :span="2">
                      {{ userForm.address || '未填写' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </el-col>

              <el-col :xs="24" :md="8">
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span class="card-title">快捷入口</span>
                    </div>
                  </template>
                  <div class="quick-actions">
                    <div class="action-item" @click="activeTab = 'edit'">
                      <el-icon :size="24" color="#409eff"><Edit /></el-icon>
                      <span>编辑资料</span>
                    </div>
                    <div class="action-item" @click="activeTab = 'security'">
                      <el-icon :size="24" color="#67c23a"><Lock /></el-icon>
                      <span>安全设置</span>
                    </div>
                    <div class="action-item">
                      <el-icon :size="24" color="#e6a23c"><Document /></el-icon>
                      <span>我的申请</span>
                    </div>
                    <div class="action-item">
                      <el-icon :size="24" color="#f56c6c"><Bell /></el-icon>
                      <span>消息通知</span>
                    </div>
                  </div>
                </el-card>

                <el-card class="info-card" style="margin-top: 1.5rem">
                  <template #header>
                    <div class="card-header">
                      <span class="card-title">登录记录</span>
                    </div>
                  </template>
                  <div class="login-records">
                    <div class="record-item" v-for="(record, index) in loginRecords.slice(0, 5)" :key="index">
                      <div class="record-icon">
                        <el-icon :size="18" :color="index === 0 ? '#67c23a' : '#909399'">
                          <component :is="index === 0 ? 'CircleCheck' : 'CircleClose'" />
                        </el-icon>
                      </div>
                      <div class="record-info">
                        <p class="record-time">{{ record.time }}</p>
                        <p class="record-location">{{ record.location }}</p>
                      </div>
                      <el-tag :type="index === 0 ? 'success' : 'info'" size="small">
                        {{ index === 0 ? '当前' : '历史' }}
                      </el-tag>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 编辑资料 -->
        <el-tab-pane label="编辑资料" name="edit">
          <div class="tab-content">
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">编辑个人信息</span>
                  <el-button type="primary" :loading="saving" @click="saveUserInfo">
                    保存修改
                  </el-button>
                </div>
              </template>
              <el-form
                ref="editFormRef"
                :model="userForm"
                :rules="editRules"
                label-width="100px"
                style="max-width: 37.5rem"
              >
                <el-form-item label="姓名">
                  <el-input v-model="userForm.name" placeholder="请输入姓名" disabled />
                </el-form-item>
                <el-form-item label="性别" prop="gender">
                  <el-radio-group v-model="userForm.gender">
                    <el-radio label="男">男</el-radio>
                    <el-radio label="女">女</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="民族" prop="nation">
                  <el-input v-model="userForm.nation" placeholder="请输入民族" />
                </el-form-item>
                <el-form-item label="政治面貌" prop="politicalStatus">
                  <el-select v-model="userForm.politicalStatus" placeholder="请选择政治面貌" style="width: 100%">
                    <el-option label="中共党员" value="中共党员" />
                    <el-option label="中共预备党员" value="中共预备党员" />
                    <el-option label="共青团员" value="共青团员" />
                    <el-option label="群众" value="群众" />
                    <el-option label="其他党派" value="其他党派" />
                  </el-select>
                </el-form-item>
                <el-form-item label="手机号码" prop="phone">
                  <el-input v-model="userForm.phone" placeholder="请输入手机号码" />
                </el-form-item>
                <el-form-item label="电子邮箱" prop="email">
                  <el-input v-model="userForm.email" placeholder="请输入电子邮箱" />
                </el-form-item>
                <el-form-item label="学制" prop="studyYears">
                  <el-select v-model="userForm.studyYears" placeholder="请选择学制" style="width: 100%">
                    <el-option label="3年" value="3年" />
                    <el-option label="4年" value="4年" />
                    <el-option label="5年" value="5年" />
                  </el-select>
                </el-form-item>
                <el-form-item label="家庭住址" prop="address">
                  <el-input
                    v-model="userForm.address"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入家庭住址"
                  />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 安全设置 -->
        <el-tab-pane label="安全设置" name="security">
          <div class="tab-content">
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">安全设置</span>
                </div>
              </template>
              <div class="security-items">
                <div class="security-item">
                  <div class="security-left">
                    <el-icon :size="32" color="#409eff"><Lock /></el-icon>
                    <div class="security-info">
                      <h4 class="security-title">修改密码</h4>
                      <p class="security-desc">定期修改密码可以保护您的账号安全</p>
                    </div>
                  </div>
                  <el-button type="primary" link @click="showPasswordDialog = true">
                    修改
                  </el-button>
                </div>

                <el-divider />

                <div class="security-item">
                  <div class="security-left">
                    <el-icon :size="32" color="#67c23a"><Phone /></el-icon>
                    <div class="security-info">
                      <h4 class="security-title">绑定手机</h4>
                      <p class="security-desc">已绑定：{{ userStore.userInfo.phone || '未绑定' }}</p>
                    </div>
                  </div>
                  <el-button type="primary" link>
                    {{ userStore.userInfo.phone ? '更换' : '绑定' }}
                  </el-button>
                </div>

                <el-divider />

                <div class="security-item">
                  <div class="security-left">
                    <el-icon :size="32" color="#e6a23c"><Message /></el-icon>
                    <div class="security-info">
                      <h4 class="security-title">绑定邮箱</h4>
                      <p class="security-desc">已绑定：{{ userStore.userInfo.email || '未绑定' }}</p>
                    </div>
                  </div>
                  <el-button type="primary" link>
                    {{ userStore.userInfo.email ? '更换' : '绑定' }}
                  </el-button>
                </div>

                <el-divider />

                <div class="security-item">
                  <div class="security-left">
                    <el-icon :size="32" color="#f56c6c"><View /></el-icon>
                    <div class="security-info">
                      <h4 class="security-title">登录记录</h4>
                      <p class="security-desc">查看账号的登录历史记录</p>
                    </div>
                  </div>
                  <el-button type="primary" link>查看</el-button>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="31.25rem"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 头像上传弹窗 -->
    <el-dialog
      v-model="showAvatarDialog"
      title="更换头像"
      width="31.25rem"
      :close-on-click-modal="false"
    >
      <div class="avatar-upload">
        <el-upload
          class="avatar-uploader"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :on-success="handleAvatarSuccess"
          action="#"
          :auto-upload="false"
        >
          <img v-if="userAvatar" :src="userAvatar" class="avatar" />
          <div v-else class="avatar-placeholder">
            <el-icon :size="56" color="#c0c4cc"><Plus /></el-icon>
            <p>点击上传头像</p>
          </div>
        </el-upload>
        <div class="upload-tips">
          <p>支持 JPG、PNG、GIF 格式</p>
          <p>建议尺寸 200 x 200 像素</p>
          <p>文件大小不超过 2MB</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAvatarDialog = false">取消</el-button>
        <el-button type="primary">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// 页面状态
const activeTab = ref('info')
const saving = ref(false)
const passwordLoading = ref(false)

// 弹窗状态
const showPasswordDialog = ref(false)
const showAvatarDialog = ref(false)

// 表单引用
const editFormRef = ref(null)
const passwordFormRef = ref(null)

// 头像
const bannerImage = ref(
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=beautiful%20university%20campus%20garden%20with%20green%20trees%20and%20modern%20buildings%20sunny%20day%20education%20background&image_size=landscape_16_9'
)

const userAvatar = ref('')

// 用户表单数据
const userForm = reactive({
  name: userStore.userInfo.name || '',
  gender: '',
  nation: '',
  politicalStatus: '',
  phone: userStore.userInfo.phone || '',
  email: userStore.userInfo.email || '',
  studyYears: '',
  address: ''
})

// 密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 编辑资料校验规则
const editRules = {
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 密码校验规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 登录记录
const loginRecords = ref([
  { time: '2024-07-25 14:30:00', location: '北京市 电信' },
  { time: '2024-07-24 09:15:00', location: '北京市 校园网' },
  { time: '2024-07-23 16:45:00', location: '北京市 联通' },
  { time: '2024-07-22 10:20:00', location: '北京市 移动' },
  { time: '2024-07-21 19:05:00', location: '北京市 校园网' }
])

// 用户角色相关
const getUserRoleType = (role) => {
  const types = {
    student: 'primary',
    teacher: 'success',
    admin: 'danger'
  }
  return types[role] || 'info'
}

const getUserRoleName = (role) => {
  const names = {
    student: '学生',
    teacher: '教师',
    admin: '管理员'
  }
  return names[role] || '用户'
}

// 方法
const showAvatarUpload = () => {
  showAvatarDialog.value = true
}

const beforeAvatarUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/gif'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('头像图片只能是 JPG、PNG、GIF 格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('头像图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleAvatarSuccess = () => {
  ElMessage.success('头像上传成功')
}

const saveUserInfo = () => {
  if (!editFormRef.value) return
  editFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      // 模拟保存
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 更新store中的用户信息
      userStore.setUserInfo({
        ...userStore.userInfo,
        phone: userForm.phone,
        email: userForm.email
      })
      
      ElMessage.success('保存成功')
      saving.value = false
      activeTab.value = 'info'
    }
  })
}

const handleChangePassword = () => {
  if (!passwordFormRef.value) return
  passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      passwordLoading.value = true
      // 模拟修改密码
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      ElMessage.success('密码修改成功，请重新登录')
      passwordLoading.value = false
      showPasswordDialog.value = false
      
      // 退出登录
      userStore.logout()
      router.push('/personal/login')
    }
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
    router.push('/personal/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.user-info-container {
  min-height: calc(100vh - 3.75rem);
  background: #f5f7fa;
}

/* 页面头部 */
.page-header {
  position: relative;
  height: 15.625rem;
  overflow: hidden;
}

.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(10, 75, 142, 0.85) 0%, rgba(103, 194, 58, 0.6) 100%);
}

.header-content {
  position: relative;
  z-index: 1;
  height: 100%;
}

.user-card {
  position: absolute;
  bottom: -3.125rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  background: #fff;
  padding: 1.5rem 2rem;
  border-radius: 0.75rem;
  box-shadow: 0 0.25rem 1.25rem rgba(0, 0, 0, 0.1);
}

.avatar-section {
  position: relative;
}

.user-avatar {
  border: 0.25rem solid #fff;
  box-shadow: 0 0.125rem 0.5rem rgba(0, 0, 0, 0.1);
}

.user-avatar :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar :deep(span) {
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  font-size: 2rem;
  font-weight: 600;
}

.change-avatar-btn {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-section:hover .change-avatar-btn {
  opacity: 1;
}

.user-info-basic {
  flex: 1;
}

.user-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.user-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.user-id {
  font-size: 0.875rem;
  color: #909399;
  margin: 0;
}

.user-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* 主要内容 */
.main-content {
  padding: 5rem 1.25rem 2rem;
  max-width: 75rem;
  margin: 0 auto;
}

.user-tabs {
  background: #fff;
  border-radius: 0.5rem;
  padding: 0 1.5rem;
  box-shadow: 0 0.125rem 0.5rem rgba(0, 0, 0, 0.05);
}

.tab-content {
  padding: 1.5rem 0;
}

.info-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
}

/* 快捷入口 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: #ecf5ff;
}

.action-item span {
  font-size: 0.8125rem;
  color: #606266;
  margin-top: 0.25rem;
}

/* 登录记录 */
.login-records {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f5f7fa;
  border-radius: 0.375rem;
}

.record-info {
  flex: 1;
}

.record-time {
  font-size: 0.8125rem;
  color: #1a1a1a;
  margin: 0 0 0.125rem;
}

.record-location {
  font-size: 0.75rem;
  color: #909399;
  margin: 0;
}

/* 安全设置 */
.security-items {
  max-width: 37.5rem;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.security-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.security-title {
  font-size: 1rem;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.security-desc {
  font-size: 0.8125rem;
  color: #909399;
  margin: 0;
}

/* 头像上传 */
.avatar-upload {
  text-align: center;
}

.avatar-uploader {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.avatar {
  width: 9.375rem;
  height: 9.375rem;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
  border: 0.125rem solid #e4e7ed;
}

.avatar-placeholder {
  width: 9.375rem;
  height: 9.375rem;
  border-radius: 50%;
  border: 0.0625rem dashed #c0c4cc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.avatar-placeholder:hover {
  border-color: #409eff;
}

.avatar-placeholder p {
  font-size: 0.875rem;
  color: #909399;
  margin-top: 0.5rem;
}

.upload-tips {
  text-align: center;
}

.upload-tips p {
  font-size: 0.75rem;
  color: #909399;
  margin: 0.25rem 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
    bottom: -9.375rem;
  }
  
  .user-tags {
    justify-content: center;
  }
  
  .user-actions {
    flex-direction: row;
    margin-top: 0.5rem;
  }
  
  .main-content {
    padding: 11.25rem 1.25rem 2rem;
  }
  
  .quick-actions {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
