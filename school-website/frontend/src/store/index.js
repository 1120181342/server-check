import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value.name || '未登录')
  const userRole = computed(() => userInfo.value.role || '')

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  function login(token, userInfo) {
    setToken(token)
    setUserInfo(userInfo)
  }

  function logout() {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    userName,
    userRole,
    setToken,
    setUserInfo,
    login,
    logout
  }
})

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const currentRoute = ref('home')

  function setLoading(status) {
    loading.value = status
  }

  function setCurrentRoute(route) {
    currentRoute.value = route
  }

  return {
    loading,
    currentRoute,
    setLoading,
    setCurrentRoute
  }
})
