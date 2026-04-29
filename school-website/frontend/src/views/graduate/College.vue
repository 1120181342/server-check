<template>
  <SubPageLayout
    pageTitle="研究生学院介绍"
    pageSubtitle="培养具有创新精神的高层次人才"
    parentTitle="研究生教育"
    parentRoute="/graduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="college-content">
        <!-- 学院概况 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><OfficeBuilding /></el-icon>
            <span>学院概况</span>
          </h3>
          <div class="intro-container">
            <div class="intro-image">
              <img :src="collegeIntro.image" alt="学院大楼" />
            </div>
            <div class="intro-text">
              <p class="intro-paragraph">{{ collegeIntro.intro }}</p>
              <p class="intro-paragraph">{{ collegeIntro.history }}</p>
              <div class="intro-stats">
                <div class="stat-item" v-for="(stat, index) in collegeStats" :key="index">
                  <span class="stat-number">{{ stat.value }}</span>
                  <span class="stat-label">{{ stat.label }}</span>
                </div>
              </div>
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
                  <div class="college-meta">
                    <span class="meta-item">
                      <el-icon><User /></el-icon>
                      {{ college.professorCount }}位教授
                    </span>
                    <span class="meta-item">
                      <el-icon><Collection /></el-icon>
                      {{ college.majorCount }}个专业
                    </span>
                  </div>
                  <el-button type="primary" size="small" style="margin-top: 1rem; width: 100%">
                    了解详情
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 师资力量 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><User /></el-icon>
            <span>师资力量</span>
          </h3>
          <el-carousel :interval="5000" height="18.75rem" indicator-position="none">
            <el-carousel-item v-for="(group, groupIndex) in teacherGroups" :key="groupIndex">
              <el-row :gutter="20">
                <el-col :xs="12" :sm="6" v-for="(teacher, index) in group" :key="index">
                  <div class="teacher-card">
                    <el-avatar :size="64" class="teacher-avatar">
                      <img :src="teacher.avatar" :alt="teacher.name" />
                    </el-avatar>
                    <h4 class="teacher-name">{{ teacher.name }}</h4>
                    <p class="teacher-title">{{ teacher.title }}</p>
                    <p class="teacher-major">{{ teacher.major }}</p>
                  </div>
                </el-col>
              </el-row>
            </el-carousel-item>
          </el-carousel>
        </section>

        <!-- 教学科研 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>教学科研</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8" v-for="(achievement, index) in achievements" :key="index">
              <div class="achievement-card">
                <el-icon :size="48" :color="achievement.color">
                  <component :is="achievement.icon" />
                </el-icon>
                <h4 class="achievement-count">{{ achievement.count }}</h4>
                <p class="achievement-label">{{ achievement.label }}</p>
                <p class="achievement-desc">{{ achievement.description }}</p>
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20university%20campus%20buildings%20with%20students%20studying%20outside%20sunny%20day%20academic%20environment&image_size=landscape_16_9'
)

const collegeIntro = ref({
  image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=grand%20university%20administration%20building%20with%20columns%20and%20flagpoles%20blue%20sky%20white%20clouds&image_size=landscape_4_3',
  intro: 'XX大学研究生院成立于1984年，是我国首批设立研究生院的高校之一。经过近40年的发展，已成为我国培养高层次人才的重要基地。研究生院始终坚持"质量第一、创新驱动"的办学理念，致力于培养具有国际视野、创新精神和实践能力的拔尖创新人才。',
  history: '学院现有博士生导师200余人，硕士生导师600余人，在校研究生近2万人。学院拥有国家级重点学科15个，省级重点学科25个，博士后科研流动站12个。近年来，学院承担国家级科研项目500余项，获得国家级科技奖励30余项，为国家经济社会发展做出了重要贡献。'
})

const collegeStats = ref([
  { value: '200+', label: '博士生导师' },
  { value: '600+', label: '硕士生导师' },
  { value: '2万+', label: '在校研究生' },
  { value: '15个', label: '国家级重点学科' }
])

const colleges = ref([
  {
    name: '计算机学院',
    description: '培养计算机科学与技术、软件工程、人工智能等领域的高层次人才',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20computer%20science%20building%20with%20glass%20facade%20students%20working%20on%20laptops%20tech%20environment&image_size=square_hd',
    professorCount: 45,
    majorCount: 8
  },
  {
    name: '电子工程学院',
    description: '专注于电子信息、通信工程、微电子技术等前沿领域研究',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=electronics%20engineering%20laboratory%20with%20oscilloscopes%20and%20circuit%20boards%20students%20conducting%20experiments&image_size=square_hd',
    professorCount: 38,
    majorCount: 6
  },
  {
    name: '机械工程学院',
    description: '面向智能制造、先进制造等国家重大需求培养创新人才',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=mechanical%20engineering%20workshop%20with%20CNC%20machines%20and%20robotic%20arms%20modern%20manufacturing&image_size=square_hd',
    professorCount: 42,
    majorCount: 5
  },
  {
    name: '经济管理学院',
    description: '培养具有国际视野的经济管理人才和企业家',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=business%20school%20building%20with%20students%20in%20business%20attire%20meeting%20rooms%20professional%20environment&image_size=square_hd',
    professorCount: 55,
    majorCount: 10
  },
  {
    name: '材料科学与工程学院',
    description: '探索新材料研发和应用的前沿学科',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=materials%20science%20laboratory%20with%20high%20tech%20equipment%20researchers%20analyzing%20samples&image_size=square_hd',
    professorCount: 35,
    majorCount: 4
  },
  {
    name: '环境科学与工程学院',
    description: '致力于环境保护和可持续发展研究',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=environmental%20science%20lab%20with%20water%20testing%20equipment%20green%20plants%20sustainable%20design&image_size=square_hd',
    professorCount: 30,
    majorCount: 5
  }
])

const teachers = ref([
  {
    name: '张教授',
    title: '博士生导师',
    major: '人工智能与机器学习',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20male%20professor%20portrait%20wearing%20suit%20and%20glasses%20academic%20style&image_size=square'
  },
  {
    name: '李教授',
    title: '博士生导师',
    major: '计算机视觉与图像处理',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20female%20professor%20portrait%20wearing%20blazer%20confident%20academic%20style&image_size=square'
  },
  {
    name: '王教授',
    title: '博士生导师',
    major: '网络与信息安全',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20male%20professor%20portrait%20mid%20age%20friendly%20smile%20academic%20style&image_size=square'
  },
  {
    name: '陈教授',
    title: '博士生导师',
    major: '大数据与云计算',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20female%20professor%20portrait%20young%20energetic%20modern%20academic%20style&image_size=square'
  },
  {
    name: '刘教授',
    title: '博士生导师',
    major: '嵌入式系统设计',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20male%20professor%20portrait%20senior%20wise%20experienced%20academic%20style&image_size=square'
  },
  {
    name: '赵教授',
    title: '博士生导师',
    major: '软件工程与方法学',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20female%20professor%20portrait%20mid%20career%20accomplished%20academic%20style&image_size=square'
  },
  {
    name: '孙教授',
    title: '硕士生导师',
    major: '分布式计算',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20male%20professor%20portrait%20young%20dynamic%20research%20style&image_size=square'
  },
  {
    name: '周教授',
    title: '硕士生导师',
    major: '计算机图形学',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20female%20professor%20portrait%2 creative%20artistic%20tech%20academic%20style&image_size=square'
  }
])

const teacherGroups = ref([
  teachers.value.slice(0, 4),
  teachers.value.slice(4, 8)
])

const achievements = ref([
  {
    count: '500+',
    label: '国家级科研项目',
    description: '近年来承担国家自然科学基金、863计划、973计划等国家级项目',
    icon: 'Trophy',
    color: '#f56c6c'
  },
  {
    count: '30+',
    label: '国家级科技奖励',
    description: '获得国家自然科学奖、国家技术发明奖、国家科技进步奖等',
    icon: 'Medal',
    color: '#67c23a'
  },
  {
    count: '2000+',
    label: 'SCI/EI论文',
    description: '在国际顶级期刊和会议发表高水平学术论文',
    icon: 'Document',
    color: '#409eff'
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

/* 学院概况 */
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
  margin-top: 1.5rem;
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
  font-size: 1.125rem;
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

.college-meta {
  display: flex;
  gap: 1rem;
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

/* 师资力量 */
.teacher-card {
  text-align: center;
  padding: 1.5rem 0.5rem;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9eb 100%);
  border-radius: 0.75rem;
  margin: 0.5rem;
}

.teacher-avatar {
  margin-bottom: 0.75rem;
  border: 0.1875rem solid #409eff;
}

.teacher-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.teacher-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.teacher-title {
  font-size: 0.8125rem;
  color: #409eff;
  margin-bottom: 0.25rem;
}

.teacher-major {
  font-size: 0.75rem;
  color: #909399;
  margin: 0;
}

/* 教学科研 */
.achievement-card {
  text-align: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #fafafa 0%, #f5f7fa 100%);
  border-radius: 0.75rem;
  border: 0.0625rem solid #e4e7ed;
  transition: all 0.3s ease;
}

.achievement-card:hover {
  transform: translateY(-0.5rem);
  box-shadow: 0 0.5rem 1.25rem rgba(0, 0, 0, 0.1);
}

.achievement-count {
  font-size: 2.25rem;
  font-weight: 700;
  margin: 0.75rem 0 0.25rem;
}

.achievement-label {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.achievement-desc {
  font-size: 0.8125rem;
  color: #909399;
  margin: 0;
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
