import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页 - XX大学' }
  },
  {
    path: '/graduate',
    name: 'Graduate',
    redirect: '/graduate/admission',
    meta: { title: '研究生教育 - XX大学' },
    children: [
      {
        path: 'admission',
        name: 'GraduateAdmission',
        component: () => import('@/views/graduate/Admission.vue'),
        meta: { title: '研究生招生信息 - XX大学' }
      },
      {
        path: 'college',
        name: 'GraduateCollege',
        component: () => import('@/views/graduate/College.vue'),
        meta: { title: '研究生学院介绍 - XX大学' }
      },
      {
        path: 'news',
        name: 'GraduateNews',
        component: () => import('@/views/graduate/News.vue'),
        meta: { title: '研究生重要新闻 - XX大学' }
      }
    ]
  },
  {
    path: '/undergraduate',
    name: 'Undergraduate',
    redirect: '/undergraduate/admission',
    meta: { title: '本科生教育 - XX大学' },
    children: [
      {
        path: 'admission',
        name: 'UndergraduateAdmission',
        component: () => import('@/views/undergraduate/Admission.vue'),
        meta: { title: '本科生招生信息 - XX大学' }
      },
      {
        path: 'college',
        name: 'UndergraduateCollege',
        component: () => import('@/views/undergraduate/College.vue'),
        meta: { title: '本科生学院介绍 - XX大学' }
      },
      {
        path: 'news',
        name: 'UndergraduateNews',
        component: () => import('@/views/undergraduate/News.vue'),
        meta: { title: '本科生重要新闻 - XX大学' }
      }
    ]
  },
  {
    path: '/doctoral',
    name: 'Doctoral',
    redirect: '/doctoral/admission',
    meta: { title: '博士生教育 - XX大学' },
    children: [
      {
        path: 'admission',
        name: 'DoctoralAdmission',
        component: () => import('@/views/doctoral/Admission.vue'),
        meta: { title: '博士生招生信息 - XX大学' }
      },
      {
        path: 'college',
        name: 'DoctoralCollege',
        component: () => import('@/views/doctoral/College.vue'),
        meta: { title: '博士生学院介绍 - XX大学' }
      },
      {
        path: 'news',
        name: 'DoctoralNews',
        component: () => import('@/views/doctoral/News.vue'),
        meta: { title: '博士生重要新闻 - XX大学' }
      }
    ]
  },
  {
    path: '/personal',
    name: 'Personal',
    redirect: '/personal/login',
    meta: { title: '个人中心 - XX大学' },
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/personal/Login.vue'),
        meta: { title: '用户登录 - XX大学' }
      },
      {
        path: 'info',
        name: 'UserInfo',
        component: () => import('@/views/personal/UserInfo.vue'),
        meta: { title: '个人信息 - XX大学', requiresAuth: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在 - XX大学' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'XX大学'
  
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
