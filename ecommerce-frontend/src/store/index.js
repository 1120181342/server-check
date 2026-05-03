import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const CART_STORAGE_KEY = 'ecommerce_cart'
const USER_STORAGE_KEY = 'ecommerce_user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(`${USER_STORAGE_KEY}_token`) || '')
  const userInfo = ref(JSON.parse(localStorage.getItem(`${USER_STORAGE_KEY}_info`) || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value.name || '未登录')
  const userAvatar = computed(() => userInfo.value.avatar || '')
  const userLevel = computed(() => userInfo.value.level || 0)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem(`${USER_STORAGE_KEY}_token`, newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem(`${USER_STORAGE_KEY}_info`, JSON.stringify(info))
  }

  function login(token, userInfo) {
    setToken(token)
    setUserInfo(userInfo)
  }

  function logout() {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem(`${USER_STORAGE_KEY}_token`)
    localStorage.removeItem(`${USER_STORAGE_KEY}_info`)
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    userName,
    userAvatar,
    userLevel,
    setToken,
    setUserInfo,
    login,
    logout
  }
})

export const useCartStore = defineStore('cart', () => {
  const items = ref(JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '[]'))
  const loading = ref(false)

  const totalCount = computed(() => {
    return items.value.reduce((sum, item) => sum + item.quantity, 0)
  })

  const totalPrice = computed(() => {
    return items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  })

  const totalPriceWithDiscount = computed(() => {
    return items.value.reduce((sum, item) => {
      const price = item.discountPrice || item.price
      return sum + price * item.quantity
    }, 0)
  })

  const selectedItems = computed(() => {
    return items.value.filter(item => item.selected)
  })

  const selectedTotal = computed(() => {
    return selectedItems.value.reduce((sum, item) => {
      const price = item.discountPrice || item.price
      return sum + price * item.quantity
    }, 0)
  })

  const selectedCount = computed(() => {
    return selectedItems.value.reduce((sum, item) => sum + item.quantity, 0)
  })

  const isAllSelected = computed(() => {
    return items.value.length > 0 && items.value.every(item => item.selected)
  })

  function saveToStorage() {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items.value))
  }

  function addItem(product, quantity = 1, specs = null) {
    const existingIndex = items.value.findIndex(item => 
      item.id === product.id && 
      JSON.stringify(item.specs) === JSON.stringify(specs)
    )

    if (existingIndex > -1) {
      items.value[existingIndex].quantity += quantity
    } else {
      items.value.push({
        id: product.id,
        name: product.name,
        price: product.price,
        discountPrice: product.discountPrice,
        image: product.image,
        quantity,
        specs,
        selected: true,
        stock: product.stock
      })
    }
    saveToStorage()
    return true
  }

  function removeItem(itemId) {
    const index = items.value.findIndex(item => item.id === itemId)
    if (index > -1) {
      items.value.splice(index, 1)
      saveToStorage()
    }
  }

  function updateQuantity(itemId, quantity) {
    const item = items.value.find(i => i.id === itemId)
    if (item) {
      item.quantity = Math.max(1, Math.min(quantity, item.stock || 99))
      saveToStorage()
    }
  }

  function toggleSelect(itemId) {
    const item = items.value.find(i => i.id === itemId)
    if (item) {
      item.selected = !item.selected
      saveToStorage()
    }
  }

  function toggleSelectAll() {
    const newSelectAll = !isAllSelected.value
    items.value.forEach(item => {
      item.selected = newSelectAll
    })
    saveToStorage()
  }

  function clearSelected() {
    items.value = items.value.filter(item => !item.selected)
    saveToStorage()
  }

  function clearCart() {
    items.value = []
    saveToStorage()
  }

  return {
    items,
    loading,
    totalCount,
    totalPrice,
    totalPriceWithDiscount,
    selectedItems,
    selectedTotal,
    selectedCount,
    isAllSelected,
    addItem,
    removeItem,
    updateQuantity,
    toggleSelect,
    toggleSelectAll,
    clearSelected,
    clearCart
  }
})

export const useProductStore = defineStore('product', () => {
  const categories = ref([])
  const products = ref([])
  const currentProduct = ref(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0
  })

  const productsCache = ref(new Map())
  const categoryCache = ref(null)

  const mockProducts = [
    {
      id: 1,
      name: 'Apple iPhone 15 Pro Max',
      price: 9999,
      discountPrice: 9599,
      categoryId: 1,
      categoryName: '手机数码',
      brand: 'Apple',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPhone%2015%20Pro%20Max%20smartphone%20product%20photo&image_size=square_hd',
      images: [
        'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPhone%2015%20Pro%20Max%20front%20view%20product%20photo&image_size=square_hd',
        'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPhone%2015%20Pro%20Max%20back%20view%20product%20photo&image_size=square_hd',
        'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPhone%2015%20Pro%20Max%20side%20view%20product%20photo&image_size=square_hd'
      ],
      description: '搭载A17 Pro芯片，钛金属设计，专业级摄像系统',
      specs: [
        { name: '颜色', values: ['钛金属黑', '钛金属白', '钛金属蓝', '钛金属自然色'] },
        { name: '存储', values: ['256GB', '512GB', '1TB'] }
      ],
      stock: 100,
      sales: 5000,
      rating: 4.9,
      isNew: true,
      isHot: true
    },
    {
      id: 2,
      name: '华为Mate 60 Pro+',
      price: 8999,
      discountPrice: 8499,
      categoryId: 1,
      categoryName: '手机数码',
      brand: '华为',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Huawei%20Mate%2060%20Pro%20smartphone%20product%20photo&image_size=square_hd',
      images: [
        'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Huawei%20Mate%2060%20Pro%20front%20view%20product%20photo&image_size=square_hd',
        'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Huawei%20Mate%2060%20Pro%20back%20view%20product%20photo&image_size=square_hd'
      ],
      description: '麒麟芯片回归，卫星通话，超可靠玄武架构',
      specs: [
        { name: '颜色', values: ['雅丹黑', '宣白', '砚黑'] },
        { name: '存储', values: ['256GB', '512GB', '1TB'] }
      ],
      stock: 50,
      sales: 3000,
      rating: 4.8,
      isNew: true,
      isHot: true
    },
    {
      id: 3,
      name: 'MacBook Pro 14英寸 M3 Pro',
      price: 14999,
      discountPrice: 13999,
      categoryId: 2,
      categoryName: '电脑办公',
      brand: 'Apple',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=MacBook%20Pro%2014%20inch%20laptop%20product%20photo&image_size=square_hd',
      images: [],
      description: 'M3 Pro芯片，18小时续航，Liquid Retina XDR显示屏',
      specs: [
        { name: '颜色', values: ['深空灰', '银色'] },
        { name: '配置', values: ['18GB+512GB', '18GB+1TB', '36GB+2TB'] }
      ],
      stock: 30,
      sales: 1200,
      rating: 4.9,
      isNew: true,
      isHot: false
    },
    {
      id: 4,
      name: '索尼WH-1000XM5 无线降噪耳机',
      price: 2499,
      discountPrice: 1999,
      categoryId: 3,
      categoryName: '音频设备',
      brand: '索尼',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Sony%20WH-1000XM5%20wireless%20headphones%20product%20photo&image_size=square_hd',
      images: [],
      description: '行业领先降噪，30小时续航，舒适轻盈设计',
      specs: [
        { name: '颜色', values: ['黑色', '银色'] }
      ],
      stock: 200,
      sales: 8000,
      rating: 4.7,
      isNew: false,
      isHot: true
    },
    {
      id: 5,
      name: '戴森V15 Detect无线吸尘器',
      price: 4990,
      discountPrice: 4490,
      categoryId: 4,
      categoryName: '家居生活',
      brand: '戴森',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Dyson%20V15%20cordless%20vacuum%20cleaner%20product%20photo&image_size=square_hd',
      images: [],
      description: '激光探测灰尘，智能分析，60分钟续航',
      specs: [
        { name: '颜色', values: ['紫镍色', '金铜色'] }
      ],
      stock: 80,
      sales: 2500,
      rating: 4.8,
      isNew: false,
      isHot: true
    },
    {
      id: 6,
      name: 'iPad Pro 12.9英寸 M2',
      price: 8499,
      discountPrice: 7999,
      categoryId: 2,
      categoryName: '电脑办公',
      brand: 'Apple',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iPad%20Pro%2012.9%20inch%20tablet%20product%20photo&image_size=square_hd',
      images: [],
      description: 'M2芯片，Liquid Retina XDR显示屏，支持Apple Pencil悬停',
      specs: [
        { name: '颜色', values: ['深空灰', '银色'] },
        { name: '存储', values: ['128GB', '256GB', '512GB', '1TB', '2TB'] },
        { name: '网络', values: ['仅WiFi', 'WiFi+蜂窝网络'] }
      ],
      stock: 60,
      sales: 3500,
      rating: 4.9,
      isNew: false,
      isHot: true
    },
    {
      id: 7,
      name: '小米14 Ultra',
      price: 5999,
      discountPrice: 5699,
      categoryId: 1,
      categoryName: '手机数码',
      brand: '小米',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Xiaomi%2014%20Ultra%20smartphone%20product%20photo&image_size=square_hd',
      images: [],
      description: '徕卡光学Summilux镜头，一英寸大底，专业影像系统',
      specs: [
        { name: '颜色', values: ['黑色', '白色', '钛金属特别版'] },
        { name: '存储', values: ['256GB', '512GB', '1TB'] }
      ],
      stock: 150,
      sales: 6000,
      rating: 4.8,
      isNew: true,
      isHot: true
    },
    {
      id: 8,
      name: 'Switch OLED 游戏机',
      price: 2599,
      discountPrice: 2299,
      categoryId: 5,
      categoryName: '游戏娱乐',
      brand: '任天堂',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Nintendo%20Switch%20OLED%20gaming%20console%20product%20photo&image_size=square_hd',
      images: [],
      description: '7英寸OLED屏幕，64GB存储，增强型底座',
      specs: [
        { name: '颜色', values: ['白色', '电光蓝·电光红'] }
      ],
      stock: 100,
      sales: 4500,
      rating: 4.7,
      isNew: false,
      isHot: true
    },
    {
      id: 9,
      name: 'AirPods Pro 2',
      price: 1899,
      discountPrice: 1599,
      categoryId: 3,
      categoryName: '音频设备',
      brand: 'Apple',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=AirPods%20Pro%202%20wireless%20earbuds%20product%20photo&image_size=square_hd',
      images: [],
      description: 'H2芯片，自适应音频，个性化空间音频，30小时续航',
      specs: [
        { name: '版本', values: ['USB-C充电盒', 'Lightning充电盒'] }
      ],
      stock: 200,
      sales: 12000,
      rating: 4.8,
      isNew: true,
      isHot: true
    },
    {
      id: 10,
      name: '海尔滚筒洗衣机 10kg',
      price: 3999,
      discountPrice: 3499,
      categoryId: 4,
      categoryName: '家居生活',
      brand: '海尔',
      image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Haier%2010kg%20front%20load%20washing%20machine%20product%20photo&image_size=square_hd',
      images: [],
      description: '直驱变频，紫外除菌，智能投放，10公斤大容量',
      specs: [
        { name: '颜色', values: ['玉墨银', '水晶银'] }
      ],
      stock: 40,
      sales: 1800,
      rating: 4.6,
      isNew: false,
      isHot: false
    }
  ]

  const mockCategories = [
    { id: 1, name: '手机数码', icon: 'Phone', children: [
      { id: 11, name: '手机' },
      { id: 12, name: '平板电脑' },
      { id: 13, name: '智能手表' }
    ]},
    { id: 2, name: '电脑办公', icon: 'Monitor', children: [
      { id: 21, name: '笔记本' },
      { id: 22, name: '台式机' },
      { id: 23, name: '外设' }
    ]},
    { id: 3, name: '音频设备', icon: 'Headset', children: [
      { id: 31, name: '耳机' },
      { id: 32, name: '音箱' },
      { id: 33, name: '播放器' }
    ]},
    { id: 4, name: '家居生活', icon: 'House', children: [
      { id: 41, name: '大家电' },
      { id: 42, name: '小家电' },
      { id: 43, name: '家居用品' }
    ]},
    { id: 5, name: '游戏娱乐', icon: 'Gamepad', children: [
      { id: 51, name: '游戏机' },
      { id: 52, name: '游戏配件' },
      { id: 53, name: '游戏软件' }
    ]}
  ]

  function getCategories() {
    if (categoryCache.value) {
      categories.value = categoryCache.value
      return categories.value
    }
    categories.value = mockCategories
    categoryCache.value = mockCategories
    return categories.value
  }

  function getProducts(params = {}) {
    loading.value = true
    
    const cacheKey = JSON.stringify(params)
    if (productsCache.value.has(cacheKey)) {
      const cached = productsCache.value.get(cacheKey)
      products.value = cached.products
      pagination.value = cached.pagination
      loading.value = false
      return { products: products.value, pagination: pagination.value }
    }

    let filteredProducts = [...mockProducts]
    
    if (params.categoryId) {
      filteredProducts = filteredProducts.filter(p => p.categoryId === params.categoryId)
    }
    
    if (params.keyword) {
      const keyword = params.keyword.toLowerCase()
      filteredProducts = filteredProducts.filter(p => 
        p.name.toLowerCase().includes(keyword) || 
        p.brand.toLowerCase().includes(keyword) ||
        p.description.toLowerCase().includes(keyword)
      )
    }
    
    if (params.priceMin !== undefined) {
      filteredProducts = filteredProducts.filter(p => p.discountPrice >= params.priceMin)
    }
    if (params.priceMax !== undefined) {
      filteredProducts = filteredProducts.filter(p => p.discountPrice <= params.priceMax)
    }

    if (params.sortBy) {
      switch (params.sortBy) {
        case 'price_asc':
          filteredProducts.sort((a, b) => a.discountPrice - b.discountPrice)
          break
        case 'price_desc':
          filteredProducts.sort((a, b) => b.discountPrice - a.discountPrice)
          break
        case 'sales':
          filteredProducts.sort((a, b) => b.sales - a.sales)
          break
        case 'rating':
          filteredProducts.sort((a, b) => b.rating - a.rating)
          break
        case 'new':
          filteredProducts.sort((a, b) => (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0))
          break
      }
    }

    const page = params.page || 1
    const pageSize = params.pageSize || 20
    const start = (page - 1) * pageSize
    const end = start + pageSize
    
    const paginatedProducts = filteredProducts.slice(start, end)
    
    pagination.value = {
      page,
      pageSize,
      total: filteredProducts.length
    }
    
    products.value = paginatedProducts
    productsCache.value.set(cacheKey, {
      products: paginatedProducts,
      pagination: { ...pagination.value }
    })
    
    loading.value = false
    return { products: paginatedProducts, pagination: pagination.value }
  }

  function getProductById(id) {
    const product = mockProducts.find(p => p.id === id)
    currentProduct.value = product || null
    return currentProduct.value
  }

  function getHotProducts(limit = 8) {
    return mockProducts.filter(p => p.isHot).slice(0, limit)
  }

  function getNewProducts(limit = 8) {
    return mockProducts.filter(p => p.isNew).slice(0, limit)
  }

  function clearCache() {
    productsCache.value.clear()
    categoryCache.value = null
  }

  return {
    categories,
    products,
    currentProduct,
    loading,
    pagination,
    getCategories,
    getProducts,
    getProductById,
    getHotProducts,
    getNewProducts,
    clearCache
  }
})

export const useOrderStore = defineStore('order', () => {
  const orders = ref(JSON.parse(localStorage.getItem('ecommerce_orders') || '[]'))
  const currentOrder = ref(null)
  const loading = ref(false)

  const generateOrderId = () => {
    const timestamp = Date.now().toString()
    const random = Math.random().toString(36).substring(2, 8).toUpperCase()
    return `ORD${timestamp}${random}`
  }

  function createOrder(orderData) {
    const order = {
      id: generateOrderId(),
      items: orderData.items,
      totalAmount: orderData.totalAmount,
      shippingAddress: orderData.shippingAddress,
      paymentMethod: orderData.paymentMethod,
      shippingMethod: orderData.shippingMethod,
      couponCode: orderData.couponCode,
      discountAmount: orderData.discountAmount || 0,
      status: 'pending',
      statusText: '待付款',
      createTime: new Date().toISOString(),
      payTime: null,
      shipTime: null,
      deliverTime: null,
      cancelTime: null
    }
    
    orders.value.unshift(order)
    saveOrders()
    currentOrder.value = order
    return order
  }

  function payOrder(orderId) {
    const order = orders.value.find(o => o.id === orderId)
    if (order && order.status === 'pending') {
      order.status = 'paid'
      order.statusText = '待发货'
      order.payTime = new Date().toISOString()
      saveOrders()
      return true
    }
    return false
  }

  function cancelOrder(orderId, reason = '') {
    const order = orders.value.find(o => o.id === orderId)
    if (order && order.status === 'pending') {
      order.status = 'cancelled'
      order.statusText = '已取消'
      order.cancelTime = new Date().toISOString()
      order.cancelReason = reason
      saveOrders()
      return true
    }
    return false
  }

  function confirmReceive(orderId) {
    const order = orders.value.find(o => o.id === orderId)
    if (order && order.status === 'shipped') {
      order.status = 'completed'
      order.statusText = '已完成'
      order.deliverTime = new Date().toISOString()
      saveOrders()
      return true
    }
    return false
  }

  function getOrderById(orderId) {
    return orders.value.find(o => o.id === orderId) || null
  }

  function getOrdersByStatus(status) {
    if (status === 'all') {
      return orders.value
    }
    return orders.value.filter(o => o.status === status)
  }

  function saveOrders() {
    localStorage.setItem('ecommerce_orders', JSON.stringify(orders.value))
  }

  return {
    orders,
    currentOrder,
    loading,
    createOrder,
    payOrder,
    cancelOrder,
    confirmReceive,
    getOrderById,
    getOrdersByStatus
  }
})

export const useAddressStore = defineStore('address', () => {
  const addresses = ref(JSON.parse(localStorage.getItem('ecommerce_addresses') || '[]'))
  const defaultAddress = ref(null)

  function initDefaultAddress() {
    defaultAddress.value = addresses.value.find(a => a.isDefault) || null
  }

  function addAddress(address) {
    const newAddress = {
      id: Date.now().toString(),
      ...address
    }
    
    if (address.isDefault || addresses.value.length === 0) {
      addresses.value.forEach(a => a.isDefault = false)
      newAddress.isDefault = true
      defaultAddress.value = newAddress
    }
    
    addresses.value.push(newAddress)
    saveAddresses()
    return newAddress
  }

  function updateAddress(id, updatedAddress) {
    const index = addresses.value.findIndex(a => a.id === id)
    if (index > -1) {
      if (updatedAddress.isDefault) {
        addresses.value.forEach(a => a.isDefault = false)
      }
      addresses.value[index] = { ...addresses.value[index], ...updatedAddress }
      if (updatedAddress.isDefault) {
        defaultAddress.value = addresses.value[index]
      }
      saveAddresses()
      return true
    }
    return false
  }

  function deleteAddress(id) {
    const index = addresses.value.findIndex(a => a.id === id)
    if (index > -1) {
      const deleted = addresses.value[index]
      addresses.value.splice(index, 1)
      
      if (deleted.isDefault && addresses.value.length > 0) {
        addresses.value[0].isDefault = true
        defaultAddress.value = addresses.value[0]
      } else if (addresses.value.length === 0) {
        defaultAddress.value = null
      }
      
      saveAddresses()
      return true
    }
    return false
  }

  function setDefault(id) {
    addresses.value.forEach(a => a.isDefault = a.id === id)
    defaultAddress.value = addresses.value.find(a => a.id === id) || null
    saveAddresses()
  }

  function saveAddresses() {
    localStorage.setItem('ecommerce_addresses', JSON.stringify(addresses.value))
  }

  return {
    addresses,
    defaultAddress,
    initDefaultAddress,
    addAddress,
    updateAddress,
    deleteAddress,
    setDefault
  }
})
