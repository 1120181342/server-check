<template>
  <SubPageLayout
    pageTitle="本科生学院介绍"
    pageSubtitle="探索知识殿堂，成就卓越人生"
    parentTitle="本科生教育"
    parentRoute="/undergraduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="college-content">
        <!-- 本科教育概况 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><OfficeBuilding /></el-icon>
            <span>本科教育概况</span>
          </h3>
          <div class="intro-container">
            <div class="intro-text">
              <p class="intro-paragraph">{{ educationIntro.intro }}</p>
              <div class="intro-stats">
                <div class="stat-item" v-for="(stat, index) in educationStats" :key="index">
                  <span class="stat-number">{{ stat.value }}</span>
                  <span class="stat-label">{{ stat.label }}</span>
                </div>
              </div>
            </div>
            <div class="intro-image">
              <img :src="educationIntro.image" alt="校园风光" />
            </div>
          </div>
        </section>

        <!-- 学院列表 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><School /></el-icon>
            <span>学院列表</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="8" v-for="(college, index) in colleges" :key="index">
              <el-card class="college-card card-hover" shadow="hover">
                <div class="college-image">
                  <img :src="college.image" :alt="college.name" />
                </div>
                <div class="college-info">
                  <h4 class="college-name">{{ college.name }}</h4>
                  <p class="college-desc">{{ college.description }}</p>
                  <div class="college-tags">
                    <el-tag v-for="(tag, idx) in college.tags" :key="idx" size="small" effect="plain">
                      {{ tag }}
                    </el-tag>
                  </div>
                  <div class="college-meta">
                    <span class="meta-item">
                      <el-icon><Collection /></el-icon>
                      {{ college.majorCount }}个本科专业
                    </span>
                    <span class="meta-item">
                      <el-icon><User /></el-icon>
                      {{ college.studentCount }}名本科生
                    </span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 特色专业 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Star /></el-icon>
            <span>特色专业</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8" v-for="(major, index) in featuredMajors" :key="index">
              <div class="featured-major-card">
                <div class="major-icon" :style="{ background: major.bgColor }">
                  <el-icon :size="40" :color="#fff">
                    <component :is="major.icon" />
                  </el-icon>
                </div>
                <h4 class="major-name">{{ major.name }}</h4>
                <p class="major-level">{{ major.level }}</p>
                <p class="major-desc">{{ major.description }}</p>
                <el-button type="primary" size="small" link>了解详情</el-button>
              </div>
            </el-col>
          </el-row>
        </section>

        <!-- 教学质量 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Medal /></el-icon>
            <span>教学质量</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="6" v-for="(item, index) in teachingQuality" :key="index">
              <div class="quality-card">
                <div class="quality-icon">
                  <el-icon :size="36" :color="item.color">
                    <component :is="item.icon" />
                  </el-icon>
                </div>
                <div class="quality-info">
                  <span class="quality-number">{{ item.count }}</span>
                  <span class="quality-label">{{ item.label }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </section>
      </div>
    </template>
  </SubPageLayout>
</template>

<script setup>
import { ref } from 'vue'
import SubPageLayout from '@/components/SubPageLayout.vue'

const bannerImage = ref(
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20students%20studying%20in%20modern%20library%20with%20large%20windows%20natural%20light%20peaceful%20learning%20environment&image_size=landscape_16_9'
)

const educationIntro = ref({
  image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aerial%20view%20of%20university%20campus%20with%20academic%20buildings%20green%20lawns%20and%20students%20walking%20around%20sunny%20day&image_size=landscape_4_3',
  intro: 'XX大学本科教育始于1920年，至今已有百年历史。学校始终坚持"以学生为中心"的教育理念，致力于培养具有国际视野、创新精神和实践能力的高素质人才。学校现有本科专业80余个，涵盖工学、理学、管理学、经济学、文学、法学、艺术学等多个学科门类。'
})

const educationStats = ref([
  { value: '80+', label: '本科专业' },
  { value: '3万+', label: '在校本科生' },
  { value: '25个', label: '国家级一流专业' },
  { value: '40个', label: '省级一流专业' }
])

const colleges = ref([
  {
    name: '计算机学院',
    description: '培养计算机科学与技术、软件工程、人工智能等领域的高素质工程技术人才',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20computer%20science%20building%20exterior%20with%20students%20entering%20tech%20university%20campus&image_size=square_hd',
    tags: ['双一流建设', '国家级重点学科'],
    majorCount: 6,
    studentCount: 3500
  },
  {
    name: '电子工程学院',
    description: '专注于电子信息、通信工程、微电子技术等前沿领域的人才培养',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=electronics%20engineering%20building%20with%20modern%20facility%20university%20campus%20architecture&image_size=square_hd',
    tags: ['省级重点学院', '校企合作基地'],
    majorCount: 5,
    studentCount: 2800
  },
  {
    name: '机械工程学院',
    description: '面向智能制造、先进制造等国家重大需求培养创新型工程人才',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=mechanical%20engineering%20building%20university%20campus%20modern%20industrial%20design&image_size=square_hd',
    tags: ['国家级特色专业', '工程教育认证'],
    majorCount: 7,
    studentCount: 3200
  },
  {
    name: '经济管理学院',
    description: '培养具有国际视野和创新精神的经济管理人才',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=business%20school%20building%20university%20campus%20modern%20architecture%20professional%20setting&image_size=square_hd',
    tags: ['省级重点学院', 'MBA授权点'],
    majorCount: 10,
    studentCount: 4000
  },
  {
    name: '材料科学与工程学院',
    description: '探索新材料研发和应用的前沿学科',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=materials%20science%20building%20university%20campus%20research%20laboratory%20exterior&image_size=square_hd',
    tags: ['双一流建设', '国家重点实验室'],
    majorCount: 4,
    studentCount: 1800
  },
  {
    name: '人文学院',
    description: '传承文化，培养人文精神与社会责任感',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=humanities%20building%20university%20campus%20classic%20architecture%20with%20columns%20academic%20setting&image_size=square_hd',
    tags: ['省级人文基地', '特色专业'],
    majorCount: 8,
    studentCount: 2500
  }
])

const featuredMajors = ref([
  {
    name: '计算机科学与技术',
    level: '国家级一流专业',
    description: '培养掌握计算机软硬件基础理论与应用技能的高级专门人才',
    icon: 'Cpu',
    bgColor: 'linear-gradient(135deg, #409eff 0%, #67c23a 100%)'
  },
  {
    name: '机械设计制造及其自动化',
    level: '国家级特色专业',
    description: '面向智能制造领域的创新型工程技术人才培养',
    icon: 'Setting',
    bgColor: 'linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%)'
  },
  {
    name: '金融学',
    level: '省级一流专业',
    description: '培养具有金融理论与实务能力的金融专门人才',
    icon: 'TrendCharts',
    bgColor: 'linear-gradient(135deg, #909399 0%, #606266 100%)'
  }
])

const teachingQuality = ref([
  {
    count: '200+',
    label: '国家级精品课程',
    icon: 'Document',
    color: '#409eff'
  },
  {
    count: '150+',
    label: '省级精品课程',
    icon: 'Collection',
    color: '#67c23a'
  },
  {
    count: '50+',
    label: '国家级教学名师',
    icon: 'User',
    color: '#f56c6c'
  },
  {
    count: '98%',
    label: '就业率',
    icon: 'TrendCharts',
    color: '#e6a23c'
  }
])
</script>

<style scoped>
.college-content {
  line-height: 1.8;
}

.section {
  margin-bottom: 2.5rem;
}

.section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 0.125rem solid #409eff;
}

.section-header .el-icon {
  color: #409eff;
}

/* 教育概况 */
.intro-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}

.intro-text {
  display: flex;
  flex-direction: column;
}

.intro-paragraph {
  font-size: 0.9375rem;
  color: #606266;
  text-indent: 2em;
  margin-bottom: 1.5rem;
  line-height: 2;
}

.intro-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 0.0625rem solid #e4e7ed;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  font-size: 0.8125rem;
  color: #909399;
}

.intro-image {
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 0.25rem 1.25rem rgba(0, 0, 0, 0.1);
}

.intro-image img {
  width: 100%;
  height: 18.75rem;
  object-fit: cover;
}

/* 学院卡片 */
.college-card {
  overflow: hidden;
}

.college-image {
  width: 100%;
  height: 9.375rem;
  overflow: hidden;
  margin: -1.25rem -1.25rem 1rem;
}

.college-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.college-card:hover .college-image img {
  transform: scale(1.1);
}

.college-name {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.college-desc {
  font-size: 0.875rem;
  color: #606266;
  margin-bottom: 0.75rem;
  line-height: 1.7;
}

.college-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.college-meta {
  display: flex;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 0.0625rem solid #e4e7ed;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: #909399;
}

.meta-item .el-icon {
  color: #409eff;
}

/* 特色专业 */
.featured-major-card {
  text-align: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #fafafa 0%, #f5f7fa 100%);
  border-radius: 0.75rem;
  border: 0.0625rem solid #e4e7ed;
  transition: all 0.3s ease;
}

.featured-major-card:hover {
  transform: translateY(-0.5rem);
  box-shadow: 0 0.5rem 1.25rem rgba(0, 0, 0, 0.1);
}

.major-icon {
  width: 5rem;
  height: 5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.featured-major-card .major-name {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.major-level {
  font-size: 0.75rem;
  color: #409eff;
  margin-bottom: 0.5rem;
}

.major-desc {
  font-size: 0.8125rem;
  color: #909399;
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

/* 教学质量 */
.quality-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9eb 100%);
  border-radius: 0.5rem;
}

.quality-info {
  display: flex;
  flex-direction: column;
}

.quality-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.2;
}

.quality-label {
  font-size: 0.8125rem;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .intro-container {
    grid-template-columns: 1fr;
  }
  
  .intro-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
