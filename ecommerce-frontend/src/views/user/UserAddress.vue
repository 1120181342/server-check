<template>
  <div class="user-address-page">
    <div class="page-header">
      <h2>收货地址</h2>
      <el-button type="primary" @click="showAddressForm = true">
        <el-icon><Plus /></el-icon>
        新增地址
      </el-button>
    </div>

    <div class="address-list" v-if="addressStore.addresses.length > 0">
      <div 
        v-for="addr in addressStore.addresses" 
        :key="addr.id"
        class="address-card"
        :class="{ default: addr.isDefault }"
      >
        <div class="address-info">
          <div class="address-header">
            <span class="receiver">{{ addr.receiverName }}</span>
            <span class="phone">{{ addr.phone }}</span>
            <el-tag v-if="addr.isDefault" type="danger" size="small">默认</el-tag>
          </div>
          <div class="address-detail">
            {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
          </div>
        </div>
        <div class="address-actions">
          <el-button 
            v-if="!addr.isDefault"
            type="text" 
            size="small"
            @click="setDefault(addr.id)"
          >
            设为默认
          </el-button>
          <el-button type="text" size="small" @click="editAddress(addr)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="text" size="small" class="delete-btn" @click="deleteAddress(addr.id)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </div>

    <div class="address-empty" v-else>
      <el-empty description="暂无收货地址">
        <el-button type="primary" @click="showAddressForm = true">
          <el-icon><Plus /></el-icon>
          添加收货地址
        </el-button>
      </el-empty>
    </div>

    <el-dialog 
      v-model="showAddressForm" 
      :title="editingAddress ? '编辑收货地址' : '新增收货地址'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addressFormRef"
        :model="addressForm"
        :rules="addressRules"
        label-width="80px"
      >
        <el-form-item label="收货人" prop="receiverName">
          <el-input v-model="addressForm.receiverName" placeholder="请输入收货人姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="addressForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="所在地区" prop="region">
          <el-cascader
            v-model="addressForm.region"
            :options="regionOptions"
            placeholder="请选择省/市/区"
            clearable
          />
        </el-form-item>
        <el-form-item label="详细地址" prop="detail">
          <el-input
            v-model="addressForm.detail"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址"
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="addressForm.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddressForm = false">取消</el-button>
        <el-button type="primary" @click="saveAddress">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAddressStore } from '@/store'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const addressStore = useAddressStore()

const showAddressForm = ref(false)
const editingAddress = ref(null)
const addressFormRef = ref<FormInstance>()

const addressForm = reactive({
  receiverName: '',
  phone: '',
  region: [],
  detail: '',
  isDefault: false
})

const addressRules: FormRules = {
  receiverName: [{ required: true, message: '请输入收货人姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  region: [{ required: true, message: '请选择所在地区', trigger: 'change' }],
  detail: [{ required: true, message: '请输入详细地址', trigger: 'blur' }]
}

const regionOptions = ref([
  {
    value: '北京市',
    label: '北京市',
    children: [
      {
        value: '东城区',
        label: '东城区',
        children: [{ value: '东城区', label: '东城区' }]
      },
      {
        value: '西城区',
        label: '西城区',
        children: [{ value: '西城区', label: '西城区' }]
      },
      {
        value: '朝阳区',
        label: '朝阳区',
        children: [{ value: '朝阳区', label: '朝阳区' }]
      }
    ]
  },
  {
    value: '上海市',
    label: '上海市',
    children: [
      {
        value: '黄浦区',
        label: '黄浦区',
        children: [{ value: '黄浦区', label: '黄浦区' }]
      },
      {
        value: '浦东新区',
        label: '浦东新区',
        children: [{ value: '浦东新区', label: '浦东新区' }]
      }
    ]
  },
  {
    value: '广东省',
    label: '广东省',
    children: [
      {
        value: '广州市',
        label: '广州市',
        children: [
          { value: '天河区', label: '天河区' },
          { value: '越秀区', label: '越秀区' }
        ]
      },
      {
        value: '深圳市',
        label: '深圳市',
        children: [
          { value: '南山区', label: '南山区' },
          { value: '福田区', label: '福田区' }
        ]
      }
    ]
  }
])

const resetAddressForm = () => {
  editingAddress.value = null
  addressForm.receiverName = ''
  addressForm.phone = ''
  addressForm.region = []
  addressForm.detail = ''
  addressForm.isDefault = false
}

const setDefault = (addrId) => {
  console.time('set-default-address')
  addressStore.setDefault(addrId)
  ElMessage.success('已设为默认地址')
  console.timeEnd('set-default-address')
}

const editAddress = (addr) => {
  editingAddress.value = addr
  addressForm.receiverName = addr.receiverName
  addressForm.phone = addr.phone
  addressForm.region = [addr.province, addr.city, addr.district]
  addressForm.detail = addr.detail
  addressForm.isDefault = addr.isDefault
  showAddressForm.value = true
}

const deleteAddress = async (addrId) => {
  try {
    await ElMessageBox.confirm('确定要删除该地址吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    console.time('delete-address')
    addressStore.deleteAddress(addrId)
    ElMessage.success('已删除')
    console.timeEnd('delete-address')
  } catch {
    // 用户取消
  }
}

const saveAddress = async () => {
  if (!addressFormRef.value) return
  
  await addressFormRef.value.validate((valid) => {
    if (valid) {
      const addressData = {
        receiverName: addressForm.receiverName,
        phone: addressForm.phone,
        province: addressForm.region[0],
        city: addressForm.region[1],
        district: addressForm.region[2],
        detail: addressForm.detail,
        isDefault: addressForm.isDefault
      }
      
      if (editingAddress.value) {
        addressStore.updateAddress(editingAddress.value.id, addressData)
        ElMessage.success('修改成功')
      } else {
        addressStore.addAddress(addressData)
        ElMessage.success('添加成功')
      }
      
      showAddressForm.value = false
      resetAddressForm()
    }
  })
}

onMounted(() => {
  console.time('user-address-onMounted')
  console.timeEnd('user-address-onMounted')
})
</script>

<style scoped>
.user-address-page {
  min-height: 500px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.address-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.address-card {
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
}

.address-card:hover {
  border-color: #ffb3b3;
}

.address-card.default {
  border-color: #ff6b6b;
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
}

.address-card.default::before {
  content: '默认';
  position: absolute;
  top: 0;
  right: 0;
  padding: 2px 8px;
  background: #ff6b6b;
  color: #fff;
  font-size: 12px;
  border-radius: 0 8px 0 4px;
}

.address-info {
  margin-bottom: 15px;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.receiver {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.phone {
  font-size: 14px;
  color: #666;
}

.address-detail {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.address-actions {
  display: flex;
  gap: 10px;
  padding-top: 15px;
  border-top: 1px dashed #f0f0f0;
}

.delete-btn {
  color: #f56c6c !important;
}

.address-empty {
  padding: 60px 0;
}
</style>
