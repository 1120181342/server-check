<template>
  <div class="products-page">
    <div class="container">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item>
          <router-link to="/">首页</router-link>
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="currentCategory">
          {{ currentCategory.name }}
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="searchKeyword">
          搜索: "{{ searchKeyword }}"
        </el-breadcrumb-item>
        <el-breadcrumb-item v-else>商品列表</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="page-content">
        <aside class="filter-sidebar">
          <div class="filter-section">
            <h3 class="filter-title">
              <el-icon><Menu /></el-icon>
              商品分类
            </h3>
            <div class="category-list">
              <div 
                class="category-item" 
                :class="{ active: !selectedCategory }"
                @click="selectCategory(null)"
              >
                全部分类
              </div>
              <div 
                v-for="category in categories" 
                :key="category.id"
                class="category-item"
                :class="{ active: selectedCategory === category.id }"
                @click="selectCategory(category.id)"
              >
                <el-icon><component :is="category.icon" /></el-icon>
                {{ category.name }}
              </div>
            </div>
          </div>

          <div class="filter-section">
            <h3 class="filter-title">
              <el-icon><PriceTag /></el-icon>
              价格区间
            </h3>
            <div class="price-range">
              <div class="range-item" :class="{ active: isPriceRangeActive(0, 1000) }" @click="setPriceRange(0, 1000)">
                ¥1000以下
              </div>
              <div class="range-item" :class="{ active: isPriceRangeActive(1000, 3000) }" @click="setPriceRange(1000, 3000)">
                ¥1000-3000
              </div>
              <div class="range-item" :class="{ active: isPriceRangeActive(3000, 5000) }" @click="setPriceRange(3000, 5000)">
                ¥3000-5000
              </div>
              <div class="range-item" :class="{ active: isPriceRangeActive(5000, 10000) }" @click="setPriceRange(5000, 10000)">
                ¥5000-10000
              </div>
              <div class="range-item" :class="{ active: isPriceRangeActive(10000, null) }" @click="setPriceRange(10000, null)">
                ¥10000以上
              </div>
            </div>
            <div class="custom-range">
              <el-input v-model.number="customPriceMin" placeholder="最低" style="width: 80px" />
              <span class="separator">-</span>
              <el-input v-model.number="customPriceMax" placeholder="最高" style="width: 80px" />
              <el-button type="primary" size="small" @click="applyCustomRange">确定</el-button>
            </div>
          </div>

          <div class="filter-section">
            <h3 class="filter-title">
              <el-icon><Star /></el-icon>
              品牌筛选
            </h3>
            <div class="brand-list">
              <div 
                v-for="brand in brands" 
                :key="brand"
                class="brand-item"
                :class="{ active: selectedBrand === brand }"
                @click="selectBrand(brand)"
              >
                {{ brand }}
              </div>
            </div>
          </div>

          <div class="filter-section">
            <h3 class="filter-title">
              <el-icon><Filter /></el-icon>
              其他筛选
            </h3>
            <div class="other-filters">
              <el-checkbox v-model="filterNew" @change="applyFilters">新品上市</el-checkbox>
              <el-checkbox v-model="filterHot" @change="applyFilters">热卖推荐</el-checkbox>
              <el-checkbox v-model="filterDiscount" @change="applyFilters">限时折扣</el-checkbox>
            </div>
          </div>
        </aside>

        <main class="products-main">
          <div class="products-header">
            <div class="sort-bar">
              <span class="sort-label">排序：</span>
              <div class="sort-options">
                <span 
                  class="sort-item" 
                  :class="{ active: sortBy === 'default' }"
                  @click="setSort('default')"
                >
                  综合排序
                </span>
                <span 
                  class="sort-item" 
                  :class="{ active: sortBy === 'sales' }"
                  @click="setSort('sales')"
                >
                  销量优先
                </span>
                <span 
                  class="sort-item" 
                  :class="{ active: sortBy === 'price_asc' }"
                  @click="setSort('price_asc')"
                >
                  价格升序
                </span>
                <span 
                  class="sort-item" 
                  :class="{ active: sortBy === 'price_desc' }"
                  @click="setSort('price_desc')"
                >
                  价格降序
                </span>
                <span 
                  class="sort-item" 
                  :class="{ active: sortBy === 'new' }"
                  @click="setSort('new')"
                >
                  最新上架
                </span>
              </div>
            </div>
            <div class="result-info">
              共 <span class="highlight">{{ pagination.total }}</span> 件商品
            </div>
          </div>

          <div class="active-filters" v-if="hasActiveFilters">
            <span class="filter-tag" v-if="selectedCategory">
              分类: {{ currentCategory?.name }}
              <el-icon class="close" @click="selectCategory(null)"><CircleClose /></el-icon>
            </span>
            <span class="filter-tag" v-if="priceMin !== null || priceMax !== null">
              价格: ¥{{ priceMin || 0 }} - {{ priceMax ? '¥' + priceMax : '不限' }}
              <el-icon class="close" @click="clearPriceRange"><CircleClose /></el-icon>
            </span>
            <span class="filter-tag" v-if="selectedBrand">
              品牌: {{ selectedBrand }}
              <el-icon class="close" @click="selectBrand(null)"><CircleClose /></el-icon>
            </span>
            <span class="clear-all" @click="clearAllFilters">清除全部</span>
          </div>

          <div class="products-grid" v-loading="loading">
            <ProductCard 
              v-for="product in products" 
              :key="product.id" 
              :product="product"
            />
          </div>

          <div class="products-empty" v-if="products.length === 0 && !loading">
            <el-empty description="暂无符合条件的商品">
              <el-button type="primary" @click="clearAllFilters">清除筛选条件</el-button>
            </el-empty>
          </div>

          <div class="pagination-section" v-if="pagination.total > 0">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[20, 40, 60, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore } from '@/store'
import ProductCard from '@/components/ProductCard.vue'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()

const categories = ref([])
const products = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const selectedCategory = ref(null)
const sortBy = ref('default')
const priceMin = ref(null)
const priceMax = ref(null)
const selectedBrand = ref(null)
const filterNew = ref(false)
const filterHot = ref(false)
const filterDiscount = ref(false)

const customPriceMin = ref(null)
const customPriceMax = ref(null)

const brands = computed(() => {
  const brandSet = new Set()
  productStore.products.forEach(p => brandSet.add(p.brand))
  return Array.from(brandSet)
})

const currentCategory = computed(() => {
  if (!selectedCategory.value) return null
  return categories.value.find(c => c.id === selectedCategory.value)
})

const searchKeyword = computed(() => route.query.keyword)

const hasActiveFilters = computed(() => {
  return selectedCategory.value || 
         priceMin.value !== null || 
         priceMax.value !== null || 
         selectedBrand.value ||
         filterNew.value ||
         filterHot.value ||
         filterDiscount.value
})

onMounted(() => {
  console.time('products-onMounted')
  
  categories.value = productStore.getCategories()
  
  if (route.query.category) {
    selectedCategory.value = parseInt(route.query.category)
  }
  if (route.query.keyword) {
    selectedBrand.value = route.query.keyword
  }
  if (route.query.sort) {
    sortBy.value = route.query.sort
  }
  if (route.query.discount === 'true') {
    filterDiscount.value = true
  }
  if (route.query.brand === 'true') {
    // 品牌专区
  }
  
  fetchProducts()
  
  console.timeEnd('products-onMounted')
})

watch([selectedCategory, sortBy, priceMin, priceMax, selectedBrand, filterNew, filterHot, filterDiscount], () => {
  pagination.value.page = 1
  fetchProducts()
})

const fetchProducts = () => {
  console.time('fetch-products')
  loading.value = true
  
  const params = {
    page: pagination.value.page,
    pageSize: pagination.value.pageSize,
    categoryId: selectedCategory.value,
    keyword: searchKeyword.value,
    sortBy: sortBy.value === 'default' ? null : sortBy.value,
    priceMin: priceMin.value,
    priceMax: priceMax.value
  }
  
  if (selectedBrand.value && !searchKeyword.value) {
    params.keyword = selectedBrand.value
  }
  
  const result = productStore.getProducts(params)
  products.value = result.products
  pagination.value = { ...result.pagination }
  
  loading.value = false
  console.timeEnd('fetch-products')
}

const selectCategory = (categoryId) => {
  selectedCategory.value = categoryId
}

const setSort = (sort) => {
  sortBy.value = sort
}

const setPriceRange = (min, max) => {
  priceMin.value = min
  priceMax.value = max
  customPriceMin.value = min
  customPriceMax.value = max
}

const isPriceRangeActive = (min, max) => {
  return priceMin.value === min && priceMax.value === max
}

const clearPriceRange = () => {
  priceMin.value = null
  priceMax.value = null
  customPriceMin.value = null
  customPriceMax.value = null
}

const applyCustomRange = () => {
  if (customPriceMin.value !== null || customPriceMax.value !== null) {
    priceMin.value = customPriceMin.value
    priceMax.value = customPriceMax.value
  }
}

const selectBrand = (brand) => {
  selectedBrand.value = brand
}

const applyFilters = () => {
  fetchProducts()
}

const clearAllFilters = () => {
  selectedCategory.value = null
  priceMin.value = null
  priceMax.value = null
  selectedBrand.value = null
  filterNew.value = false
  filterHot.value = false
  filterDiscount.value = false
  customPriceMin.value = null
  customPriceMax.value = null
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  fetchProducts()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  fetchProducts()
}
</script>

<style scoped>
.products-page {
  padding: 20px 0;
  min-height: calc(100vh - 200px);
}

.breadcrumb {
  margin-bottom: 20px;
  padding: 15px 20px;
  background: #fff;
  border-radius: 8px;
}

.page-content {
  display: flex;
  gap: 20px;
}

.filter-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.filter-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #666;
}

.category-item:hover {
  background: #fff5f5;
  color: #ff6b6b;
}

.category-item.active {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: #fff;
}

.price-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.range-item {
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.range-item:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.range-item.active {
  background: #ff6b6b;
  border-color: #ff6b6b;
  color: #fff;
}

.custom-range {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.separator {
  color: #999;
}

.brand-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.brand-item {
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.brand-item:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.brand-item.active {
  background: #ff6b6b;
  border-color: #ff6b6b;
  color: #fff;
}

.other-filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.products-main {
  flex: 1;
}

.products-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.sort-bar {
  display: flex;
  align-items: center;
  gap: 15px;
}

.sort-label {
  font-size: 14px;
  color: #666;
}

.sort-options {
  display: flex;
  gap: 20px;
}

.sort-item {
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
}

.sort-item:hover {
  color: #ff6b6b;
}

.sort-item.active {
  color: #ff6b6b;
  font-weight: 600;
  background: #fff5f5;
}

.result-info {
  font-size: 14px;
  color: #666;
}

.highlight {
  color: #ff6b6b;
  font-weight: 600;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff5f5;
  border: 1px solid #ffb3b3;
  border-radius: 4px;
  font-size: 13px;
  color: #ff6b6b;
}

.filter-tag .close {
  cursor: pointer;
}

.clear-all {
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.clear-all:hover {
  color: #ff6b6b;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.products-empty {
  padding: 60px 0;
  background: #fff;
  border-radius: 8px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}
</style>
