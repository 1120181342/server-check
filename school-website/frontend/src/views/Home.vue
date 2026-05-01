<template>
  <div class="home-container">
    <!-- 轮播图区域 -->
    <el-carousel
      :interval="4000"
      height="28rem"
      indicator-position="outside"
      arrow="always"
    >
      <el-carousel-item v-for="(banner, index) in banners" :key="index">
        <div class="banner-item">
          <img :src="banner.image" :alt="banner.title" class="banner-image" />
          <div class="banner-overlay">
            <div class="banner-content">
              <h2 class="banner-title">{{ banner.title }}</h2>
              <p class="banner-subtitle">{{ banner.subtitle }}</p>
            </div>
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>

    <!-- 快速导航 -->
    <div class="quick-nav-section">
      <div class="nav-container">
        <div class="nav-item card-hover" v-for="(nav, index) in quickNavs" :key="index">
          <div class="nav-icon">
            <el-icon :size="40"><component :is="nav.icon" /></el-icon>
          </div>
          <h3 class="nav-title">{{ nav.title }}</h3>
          <p class="nav-desc">{{ nav.description }}</p>
          <el-button type="primary" link @click="goToRoute(nav.path)">
            了解更多 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 学校简介 -->
    <section class="school-intro">
      <div class="section-inner">
        <h2 class="section-title">学校简介</h2>
        <div class="intro-content">
          <div class="intro-image">
            <img :src="schoolInfo.image" alt="校园风光" />
          </div>
          <div class="intro-text">
            <p class="intro-paragraph">{{ schoolInfo.intro }}</p>
            <p class="intro-paragraph">{{ schoolInfo.history }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 学校数据统计 -->
    <section class="stats-section">
      <div class="section-inner">
        <div class="stats-grid">
          <div class="stat-item" v-for="(stat, index) in stats" :key="index">
            <div class="stat-number">
              <span class="number-value">{{ stat.value }}</span>
              <span class="number-unit">{{ stat.unit }}</span>
            </div>
            <p class="stat-label">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 校园风光 -->
    <section class="campus-gallery">
      <div class="section-inner">
        <h2 class="section-title">校园风光</h2>
        <div class="gallery-grid">
          <div class="gallery-item card-hover" v-for="(img, index) in campusImages" :key="index">
            <div class="gallery-image">
              <img :src="img.image" :alt="img.title" />
            </div>
            <div class="gallery-info">
              <h4 class="gallery-title">{{ img.title }}</h4>
              <p class="gallery-desc">{{ img.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 最新公告 -->
    <section class="news-section">
      <div class="section-inner">
        <div class="news-header">
          <h2 class="section-title">最新公告</h2>
          <el-button type="primary" link>更多公告</el-button>
        </div>
        <div class="news-list">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12" :md="8" v-for="(news, index) in latestNews" :key="index">
              <el-card class="news-card card-hover" shadow="hover">
                <template #header>
                  <div class="news-card-header">
                    <span class="news-tag" :class="'tag-' + (index + 1)">
                      {{ ['重要通知', '招生公告', '学术动态'][index] }}
                    </span>
                    <span class="news-date">{{ news.date }}</span>
                  </div>
                </template>
                <h4 class="news-title">{{ news.title }}</h4>
                <p class="news-summary">{{ news.summary }}</p>
                <div class="news-footer">
                  <el-button type="primary" link size="small">查看详情</el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const banners = ref([
  {
    title: 'XX大学',
    subtitle: '厚德载物 自强不息',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=beautiful%20university%20campus%20entrance%20gate%20with%20modern%20architecture%20and%20green%20trees%20sunny%20day%20photorealistic&image_size=landscape_16_9'
  },
  {
    title: '欢迎2024级新同学',
    subtitle: '开启你的学术之旅',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=students%20walking%20on%20beautiful%20university%20campus%20with%20modern%20library%20building%20and%20lawn%20spring%20season&image_size=landscape_16_9'
  },
  {
    title: '研究生招生进行中',
    subtitle: '追求卓越 成就梦想',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20laboratory%20with%20modern%20equipment%20researchers%20working%20professional%20scientific%20environment&image_size=landscape_16_9'
  }
])

const quickNavs = ref([
  {
    title: '研究生教育',
    description: '探索前沿研究，培养学术精英',
    icon: 'User',
    path: '/graduate/admission'
  },
  {
    title: '本科生教育',
    description: '夯实基础，培养创新型人才',
    icon: 'Avatar',
    path: '/undergraduate/admission'
  },
  {
    title: '博士生教育',
    description: '攀登学术高峰，引领科技创新',
    icon: 'Trophy',
    path: '/doctoral/admission'
  }
])

const schoolInfo = ref({
  image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aerial%20view%20of%20beautiful%20university%20campus%20with%20modern%20buildings%20green%20trees%20lake%20and%20sports%20field%20sunny%20day&image_size=landscape_4_3',
  intro: 'XX大学是一所历史悠久、学科齐全的综合性研究型大学。学校坐落于风景秀丽的XX市，占地面积近5000亩，建筑面积超过200万平方米。学校秉承"厚德载物、自强不息"的校训精神，致力于培养具有创新精神和实践能力的高素质人才。',
  history: '学校创建于1920年，历经百年发展，已成为一所以工为主、理工结合、多学科协调发展的全国重点大学。学校现有教职工近4000人，其中两院院士15人，国家级教学名师20余人。全日制在校学生约5万人，其中研究生近2万人。'
})

const stats = ref([
  { value: '100+', unit: '年', label: '办学历史' },
  { value: '5', unit: '万+', label: '在校学生' },
  { value: '4000', unit: '+', label: '教职工' },
  { value: '15', unit: '位', label: '两院院士' }
])

const campusImages = ref([
  {
    title: '主教学楼',
    description: '现代化的教学设施，先进的多媒体教室',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20teaching%20building%20with%20glass%20facade%20students%20entering%20clean%20and%20bright&image_size=square_hd'
  },
  {
    title: '图书馆',
    description: '藏书丰富，安静舒适的学习环境',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20library%20interior%20with%20rows%20of%20books%20students%20studying%20natural%20light%20large%20windows&image_size=square_hd'
  },
  {
    title: '体育馆',
    description: '多功能运动场馆，完善的体育设施',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20indoor%20gymnasium%20with%20basketball%20court%20bright%20lighting%20spectator%20seats&image_size=square_hd'
  },
  {
    title: '实验楼',
    description: '先进的科研设备，一流的实验条件',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20science%20laboratory%20with%20advanced%20equipment%20researchers%20conducting%20experiments%20clean%20and%20professional&image_size=square_hd'
  }
])

const latestNews = ref([
  {
    title: '关于2024年秋季学期开学安排的通知',
    summary: '根据学校工作安排，2024年秋季学期将于9月2日正式开学，请各位师生做好准备...',
    date: '2024-08-15'
  },
  {
    title: '2025年硕士研究生招生简章发布',
    summary: '我校2025年硕士研究生招生工作即将启动，现将招生简章及专业目录公布...',
    date: '2024-08-10'
  },
  {
    title: '我校获批3个国家级一流本科专业建设点',
    summary: '近日，教育部公布了2024年度国家级一流本科专业建设点名单，我校计算机科学与技术、电子信息工程、机械设计制造及其自动化三个专业获批...',
    date: '2024-08-05'
  }
])

const goToRoute = (path) => {
  router.push(path)
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
}

/* 轮播图样式 */
.banner-item {
  position: relative;
  width: 100%;
  height: 100%;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(10, 75, 142, 0.7) 0%, rgba(103, 194, 58, 0.5) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-content {
  text-align: center;
  color: #fff;
}

.banner-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
}

.banner-subtitle {
  font-size: 1.25rem;
  opacity: 0.95;
  text-shadow: 0 0.0625rem 0.125rem rgba(0, 0, 0, 0.3);
}

/* 快速导航 */
.quick-nav-section {
  background: #fff;
  padding: 3rem 0;
  margin-top: -3.75rem;
  position: relative;
  z-index: 10;
}

.nav-container {
  max-width: 75rem;
  margin: 0 auto;
  padding: 0 1.25rem;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.nav-item {
  background: #fff;
  border-radius: 0.75rem;
  padding: 1.875rem;
  text-align: center;
  border: 0.0625rem solid #e4e7ed;
  transition: all 0.3s ease;
}

.nav-icon {
  width: 5rem;
  height: 5rem;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.25rem;
  color: #fff;
}

.nav-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.nav-desc {
  font-size: 0.875rem;
  color: #909399;
  margin-bottom: 1rem;
}

/* 学校简介 */
.school-intro {
  padding: 3.75rem 0;
  background: #fff;
}

.section-inner {
  max-width: 75rem;
  margin: 0 auto;
  padding: 0 1.25rem;
}

.intro-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}

.intro-image {
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 0.25rem 1.25rem rgba(0, 0, 0, 0.1);
}

.intro-image img {
  width: 100%;
  height: 25rem;
  object-fit: cover;
}

.intro-text {
  line-height: 2;
}

.intro-paragraph {
  font-size: 1rem;
  color: #606266;
  text-indent: 2em;
  margin-bottom: 1.5rem;
}

.intro-paragraph:last-child {
  margin-bottom: 0;
}

/* 数据统计 */
.stats-section {
  background: linear-gradient(135deg, #0a4b8e 0%, #1d6fb8 100%);
  padding: 3.75rem 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
}

.stat-item {
  text-align: center;
  color: #fff;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.number-value {
  color: #67c23a;
}

.number-unit {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.5rem;
}

.stat-label {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
}

/* 校园风光 */
.campus-gallery {
  padding: 3.75rem 0;
  background: #f5f7fa;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.gallery-item {
  background: #fff;
  border-radius: 0.75rem;
  overflow: hidden;
  border: 0.0625rem solid #e4e7ed;
}

.gallery-image {
  width: 100%;
  height: 12.5rem;
  overflow: hidden;
}

.gallery-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.gallery-item:hover .gallery-image img {
  transform: scale(1.1);
}

.gallery-info {
  padding: 1rem;
}

.gallery-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.gallery-desc {
  font-size: 0.8125rem;
  color: #909399;
  margin: 0;
}

/* 最新公告 */
.news-section {
  padding: 3.75rem 0;
  background: #fff;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.news-card {
  height: 100%;
}

.news-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.news-tag {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  color: #fff;
}

.tag-1 {
  background: #f56c6c;
}

.tag-2 {
  background: #67c23a;
}

.tag-3 {
  background: #409eff;
}

.news-date {
  font-size: 0.75rem;
  color: #909399;
}

.news-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-summary {
  font-size: 0.875rem;
  color: #606266;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 1rem;
}

.news-footer {
  padding-top: 0.75rem;
  border-top: 0.0625rem solid #ebeef5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .banner-title {
    font-size: 2rem;
  }
  
  .nav-container {
    grid-template-columns: 1fr;
  }
  
  .intro-content {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .gallery-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
