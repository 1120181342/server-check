import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore, useAddressStore } from '@/store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '优选商城 - 品质生活从这里开始' }
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('@/views/Products.vue'),
    meta: { title: '商品列表 - 优选商城' }
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: () => import('@/views/ProductDetail.vue'),
    meta: { title: '商品详情 - 优选商城' }
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('@/views/Cart.vue'),
    meta: { title: '购物车 - 优选商城' }
  },
  {
    path: '/checkout',
    name: 'Checkout',
    component: () => import('@/views/Checkout.vue'),
    meta: { title: '结算 - 优选商城', requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/Orders.vue'),
    meta: { title: '我的订单 - 优选商城', requiresAuth: true },
    children: [
      {
        path: '',
        name: 'OrderList',
        component: () => import('@/views/orders/OrderList.vue'),
        meta: { title: '我的订单 - 优选商城' }
      },
      {
        path: ':id',
        name: 'OrderDetail',
        component: () => import('@/views/orders/OrderDetail.vue'),
        meta: { title: '订单详情 - 优选商城' }
      }
    ]
  },
  {
    path: '/user',
    name: 'User',
    component: () => import('@/views/User.vue'),
    meta: { title: '个人中心 - 优选商城', requiresAuth: true },
    children: [
      {
        path: '',
        name: 'UserInfo',
        component: () => import('@/views/user/UserInfo.vue'),
        meta: { title: '个人信息 - 优选商城' }
      },
      {
        path: 'address',
        name: 'UserAddress',
        component: () => import('@/views/user/UserAddress.vue'),
        meta: { title: '收货地址 - 优选商城' }
      },
      {
        path: 'coupons',
        name: 'UserCoupons',
        component: () => import('@/views/user/UserCoupons.vue'),
        meta: { title: '我的优惠券 - 优选商城' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '用户登录 - 优选商城' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '用户注册 - 优选商城' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在 - 优选商城' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0, behavior: 'smooth' }
    }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '优选商城'
  
  const userStore = useUserStore()
  const addressStore = useAddressStore()
  
  if (userStore.isLoggedIn) {
    addressStore.initDefaultAddress()
  }
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  else if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn) {
    next({ name: 'Home' })
  }
  else if (to.name === 'Checkout') {
    const { useCartStore } = await import('@/store')
    const cartStore = useCartStore()
    
    if (cartStore.selectedItems.length === 0) {
      next({ name: 'Cart' })
    } else {
      next()
    }
  }
  else {
    next()
  }
})

router.afterEach((to, from) => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

export default router
