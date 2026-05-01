<template>
  <SubPageLayout
    pageTitle="博士生学院介绍"
    pageSubtitle="汇聚顶尖学者，攀登学术高峰"
    parentTitle="博士生教育"
    parentRoute="/doctoral"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="college-content">
        <!-- 博士生教育概况 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><OfficeBuilding /></el-icon>
            <span>博士生教育概况</span>
          </h3>
          <div class="intro-container">
            <div class="intro-image">
              <img :src="collegeIntro.image" alt="学院大楼" />
            </div>
            <div class="intro-text">
              <p class="intro-paragraph">{{ collegeIntro.intro }}</p>
              <p class="intro-paragraph">{{ collegeIntro.advantage }}</p>
              <div class="intro-stats">
                <div class="stat-item" v-for="(stat, index) in collegeStats" :key="index">
                  <span class="stat-number">{{ stat.value }}</span>
                  <span class="stat-label">{{ stat.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 重点学科 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Star /></el-icon>
            <span>重点学科</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="8" v-for="(discipline, index) in keyDisciplines" :key="index">
              <el-card class="discipline-card card-hover" shadow="hover">
                <div class="discipline-icon" :style="{ background: discipline.bgColor }">
                  <el-icon :size="36" :color="#fff">
                    <component :is="discipline.icon" />
                  </el-icon>
                </div>
                <h4 class="discipline-name">{{ discipline.name }}</h4>
                <el-tag type="danger" size="small" style="margin-bottom: 0.5rem">国家级重点学科</el-tag>
                <p class="discipline-desc">{{ discipline.description }}</p>
                <div class="discipline-meta">
                  <span class="meta-item">
                    <el-icon><User /></el-icon>
                    {{ discipline.supervisorCount }}位博士生导师
                  </span>
                  <span class="meta-item">
                    <el-icon><Trophy /></el-icon>
                    {{ discipline.projectCount }}项国家级项目
                  </span>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 科研平台 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><OfficeBuilding /></el-icon>
            <span>科研平台</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" v-for="(platform, index) in researchPlatforms" :key="index">
              <el-card class="platform-card" shadow="hover">
                <el-row :gutter="15">
                  <el-col :span="6">
                    <div class="platform-icon">
                      <el-icon :size="40" :color="platform.color">
                        <component :is="platform.icon" />
                      </el-icon>
                    </div>
                  </el-col>
                  <el-col :span="18">
                    <h4 class="platform-name">{{ platform.name }}</h4>
                    <el-tag :type="platform.level === 1 ? 'danger' : 'primary'" size="small">
                      {{ platform.level === 1 ? '国家重点实验室' : '省部级重点实验室' }}
                    </el-tag>
                    <p class="platform-desc">{{ platform.description }}</p>
                  </el-col>
                </el-row>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 培养特色 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Medal /></el-icon>
            <span>培养特色</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8" v-for="(feature, index) in trainingFeatures" :key="index">
              <div class="feature-card">
                <div class="feature-icon">
                  <el-icon :size="40" :color="feature.color">
                    <component :is="feature.icon" />
                  </el-icon>
                </div>
                <h4 class="feature-title">{{ feature.title }}</h4>
                <p class="feature-desc">{{ feature.description }}</p>
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20research%20center%20with%20scientists%20working%20in%20lab%20high%20tech%20equipment%20academic%20excellence&image_size=landscape_16_9'
)

const collegeIntro = ref({
  image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=grand%20university%20research%20building%20facade%20modern%20architecture%20with%20glass%20and%20steel%20academic%20environment&image_size=landscape_4_3',
  intro: 'XX大学博士生教育始于1984年，是我国首批设立博士学位授予权的高校之一。经过近40年的发展，已形成了完善的博士生培养体系，培养了一大批具有国际视野和创新能力的高层次学术领军人才。学校始终坚持"质量第一、创新驱动"的办学理念，致力于培养能够引领学科发展的拔尖创新人才。',
  advantage: '学校拥有一批国家级重点学科和高水平科研平台，汇聚了以两院院士、长江学者、国家杰青为代表的顶尖师资队伍。近年来，我校博士生在国际顶级期刊发表论文数量持续增长，获得国家级科技奖励的比例逐年提高，培养质量得到社会各界的高度认可。'
})

const collegeStats = ref([
  { value: '35个', label: '一级学科博士点' },
  { value: '200+', label: '博士生导师' },
  { value: '5000+', label: '在校博士生' },
  { value: '12个', label: '博士后流动站' }
])

const keyDisciplines = ref([
  {
    name: '计算机科学与技术',
    description: '研究计算机理论与应用的前沿领域，包括人工智能、大数据、云计算等方向',
    icon: 'Cpu',
    bgColor: 'linear-gradient(135deg, #409eff 0%, #67c23a 100%)',
    supervisorCount: 45,
    projectCount: 86
  },
  {
    name: '电子科学与技术',
    description: '专注于微电子、光电子、集成电路等核心技术研究',
    icon: 'Monitor',
    bgColor: 'linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%)',
    supervisorCount: 38,
    projectCount: 72
  },
  {
    name: '机械工程',
    description: '面向智能制造、先进制造等国家重大需求开展研究',
    icon: 'Setting',
    bgColor: 'linear-gradient(135deg, #909399 0%, #606266 100%)',
    supervisorCount: 42,
    projectCount: 68
  },
  {
    name: '材料科学与工程',
    description: '探索新材料研发和应用的前沿学科',
    icon: 'MagicStick',
    bgColor: 'linear-gradient(135deg, #67c23a 0%, #85ce61 100%)',
    supervisorCount: 35,
    projectCount: 55
  },
  {
    name: '控制科学与工程',
    description: '研究智能控制、机器人、自动化等前沿技术',
    icon: 'Connection',
    bgColor: 'linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%)',
    supervisorCount: 30,
    projectCount: 48
  },
  {
    name: '信息与通信工程',
    description: '研究通信理论与技术，引领5G/6G发展',
    icon: 'Share',
    bgColor: 'linear-gradient(135deg, #409eff 0%, #79bbff 100%)',
    supervisorCount: 28,
    projectCount: 45
  }
])

const researchPlatforms = ref([
  {
    name: '国家智能计算重点实验室',
    level: 1,
    description: '依托计算机科学与技术学科，在人工智能、大数据分析等领域取得重大突破',
    icon: 'Cpu',
    color: '#409eff'
  },
  {
    name: '国家先进制造技术工程实验室',
    level: 1,
    description: '聚焦智能制造、工业机器人等国家重大需求，承担多项国家级科研项目',
    icon: 'Setting',
    color: '#67c23a'
  },
  {
    name: '省部级微电子技术重点实验室',
    level: 2,
    description: '专注于集成电路设计、制造与测试技术研究',
    icon: 'Monitor',
    color: '#f56c6c'
  },
  {
    name: '省部级新能源材料重点实验室',
    level: 2,
    description: '研究新型储能材料、清洁能源材料等前沿方向',
    icon: 'Sunny',
    color: '#e6a23c'
  }
])

const trainingFeatures = ref([
  {
    title: '导师负责制',
    description: '每位博士生由一位资深教授担任指导教师，提供个性化的学术指导',
    icon: 'User',
    color: '#409eff'
  },
  {
    title: '国际化培养',
    description: '支持博士生参与国际合作项目，赴海外知名高校访学交流',
    icon: 'Global',
    color: '#67c23a'
  },
  {
    title: '科研项目驱动',
    description: '依托国家级科研项目，让博士生在实践中提升科研能力',
    icon: 'DataAnalysis',
    color: '#f56c6c'
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

.intro-image {
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 0.25rem 1.25rem rgba(0, 0, 0, 0.1);
}

.intro-image img {
  width: 100%;
  height: 20rem;
  object-fit: cover;
}

.intro-paragraph {
  font-size: 0.9375rem;
  color: #606266;
  text-indent: 2em;
  margin-bottom: 1rem;
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

/* 重点学科卡片 */
.discipline-card {
  text-align: center;
}

.discipline-icon {
  width: 4.375rem;
  height: 4.375rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.discipline-name {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.discipline-desc {
  font-size: 0.8125rem;
  color: #606266;
  line-height: 1.7;
  margin-bottom: 0.75rem;
}

.discipline-meta {
  display: flex;
  justify-content: space-around;
  padding-top: 0.75rem;
  border-top: 0.0625rem solid #e4e7ed;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #909399;
}

.meta-item .el-icon {
  color: #409eff;
}

/* 科研平台卡片 */
.platform-card {
  padding: 1.25rem;
}

.platform-icon {
  width: 4.375rem;
  height: 4.375rem;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9eb 100%);
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.platform-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.platform-desc {
  font-size: 0.8125rem;
  color: #606266;
  line-height: 1.7;
  margin-top: 0.5rem;
}

/* 培养特色 */
.feature-card {
  text-align: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #fafafa 0%, #f5f7fa 100%);
  border-radius: 0.75rem;
  border: 0.0625rem solid #e4e7ed;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-0.5rem);
  box-shadow: 0 0.5rem 1.25rem rgba(0, 0, 0, 0.1);
}

.feature-icon {
  margin-bottom: 1rem;
}

.feature-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.feature-desc {
  font-size: 0.8125rem;
  color: #606266;
  line-height: 1.6;
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
