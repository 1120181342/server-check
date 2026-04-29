<template>
  <SubPageLayout
    pageTitle="本科生招生信息"
    pageSubtitle="选择XX大学，开启精彩人生"
    parentTitle="本科生教育"
    parentRoute="/undergraduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="admission-content">
        <!-- 招生公告 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Notification /></el-icon>
            <span>最新公告</span>
          </h3>
          <div class="notice-list">
            <el-card v-for="(notice, index) in notices" :key="index" class="notice-card card-hover">
              <div class="notice-header">
                <el-tag :type="notice.type === 1 ? 'danger' : notice.type === 2 ? 'success' : 'primary'" size="small">
                  {{ notice.type === 1 ? '重要通知' : notice.type === 2 ? '招生政策' : '常见问题' }}
                </el-tag>
                <span class="notice-date">{{ notice.date }}</span>
              </div>
              <h4 class="notice-title">{{ notice.title }}</h4>
              <p class="notice-summary">{{ notice.summary }}</p>
              <el-button type="primary" link size="small">
                查看详情 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-card>
          </div>
        </section>

        <!-- 本科专业 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Collection /></el-icon>
            <span>本科招生专业</span>
          </h3>
          <el-tabs v-model="activeTab">
            <el-tab-pane v-for="(category, idx) in majorCategories" :key="idx" :label="category.name" :name="category.name">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12" :md="8" v-for="(major, index) in getMajorsByCategory(category.name)" :key="index">
                  <el-card class="major-card card-hover" shadow="hover">
                    <template #header>
                      <div class="major-header">
                        <span class="major-code">专业代码：{{ major.code }}</span>
                        <el-tag v-if="major.isTop" type="warning" size="small">国家级一流专业</el-tag>
                      </div>
                    </template>
                    <h4 class="major-name">{{ major.name }}</h4>
                    <p class="major-desc">{{ major.description }}</p>
                    <div class="major-footer">
                      <span class="major-duration">学制：{{ major.duration }}年</span>
                      <el-button type="primary" size="small" link>了解更多</el-button>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </el-tab-pane>
          </el-tabs>
        </section>

        <!-- 招生计划 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>2024年招生计划</span>
          </h3>
          <el-table :data="admissionPlans" style="width: 100%" stripe border>
            <el-table-column prop="province" label="省份" width="100" />
            <el-table-column prop="scienceCount" label="理工类(人)" width="100" align="center" />
            <el-table-column prop="artsCount" label="文史类(人)" width="100" align="center" />
            <el-table-column prop="totalCount" label="合计(人)" width="100" align="center">
              <template #default="scope">
                <span style="font-weight: 600; color: #409eff;">{{ scope.row.scienceCount + scope.row.artsCount }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" />
          </el-table>
        </section>

        <!-- 历年分数线 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><TrendCharts /></el-icon>
            <span>历年录取分数线</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :md="12" v-for="(yearData, index) in scoreLines" :key="index">
              <el-card class="score-card">
                <h4 class="score-year">{{ yearData.year }}年录取分数线</h4>
                <el-table :data="yearData.data" size="small" style="width: 100%">
                  <el-table-column prop="type" label="科类" width="80" />
                  <el-table-column prop="batch" label="批次" width="80" />
                  <el-table-column prop="minScore" label="最低分" width="80" align="center" />
                  <el-table-column prop="avgScore" label="平均分" width="80" align="center" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 联系方式 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Phone /></el-icon>
            <span>招生咨询</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><PhoneFilled /></el-icon>
                <h4>招生热线</h4>
                <p>010-XXXXXXX</p>
                <p class="contact-note">工作日 8:30-17:00</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><Message /></el-icon>
                <h4>电子邮箱</h4>
                <p>zsb@xxuniversity.edu.cn</p>
                <p class="contact-note">24小时内回复</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><ChatDotRound /></el-icon>
                <h4>在线咨询</h4>
                <p>QQ群：XXXXXXXXX</p>
                <p class="contact-note">扫码加入咨询群</p>
              </div>
            </el-col>
          </el-row>
        </section>
      </div>
    </template>
  </SubPageLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import SubPageLayout from '@/components/SubPageLayout.vue'

const bannerImage = ref(
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=happy%20university%20students%20walking%20on%20campus%20lawn%20with%20backpacks%20sunny%20day%20youthful%20atmosphere&image_size=landscape_16_9'
)

const activeTab = ref('工学类')

const notices = ref([
  {
    type: 1,
    date: '2024-06-20',
    title: 'XX大学2024年本科招生章程',
    summary: '根据《中华人民共和国教育法》《中华人民共和国高等教育法》和教育部有关规定，为更好地贯彻教育部"依法治招"的要求，规范学校全日制普通本科招生工作，特制定本章程...'
  },
  {
    type: 2,
    date: '2024-06-15',
    title: '关于2024年招生政策调整的说明',
    summary: '为适应新高考改革，我校2024年招生政策进行了相应调整，现将主要变化说明如下...'
  },
  {
    type: 3,
    date: '2024-06-10',
    title: '2024年本科招生常见问题解答',
    summary: '为帮助广大考生和家长更好地了解我校2024年本科招生政策，我们整理了考生常见问题及解答...'
  }
])

const majorCategories = ref([
  { name: '工学类' },
  { name: '理学类' },
  { name: '经管类' },
  { name: '人文社科类' }
])

const allMajors = ref([
  {
    category: '工学类',
    code: '080901',
    name: '计算机科学与技术',
    description: '培养掌握计算机软硬件基础理论与应用技能的高级专门人才',
    duration: 4,
    isTop: true
  },
  {
    category: '工学类',
    code: '080902',
    name: '软件工程',
    description: '培养具备软件设计、开发、测试能力的工程技术人才',
    duration: 4,
    isTop: true
  },
  {
    category: '工学类',
    code: '080701',
    name: '电子信息工程',
    description: '培养电子信息系统设计、开发与应用的工程技术人才',
    duration: 4,
    isTop: false
  },
  {
    category: '工学类',
    code: '080202',
    name: '机械设计制造及其自动化',
    description: '培养机械工程领域的高级工程技术人才',
    duration: 4,
    isTop: true
  },
  {
    category: '理学类',
    code: '070101',
    name: '数学与应用数学',
    description: '培养具有扎实数学理论基础的应用研究人才',
    duration: 4,
    isTop: true
  },
  {
    category: '理学类',
    code: '070201',
    name: '物理学',
    description: '培养掌握物理学基本理论与实验技能的专门人才',
    duration: 4,
    isTop: false
  },
  {
    category: '理学类',
    code: '070301',
    name: '化学',
    description: '培养具有扎实化学基础的研究与应用人才',
    duration: 4,
    isTop: true
  },
  {
    category: '经管类',
    code: '120201K',
    name: '工商管理',
    description: '培养具备现代企业管理理论与实践能力的管理人才',
    duration: 4,
    isTop: false
  },
  {
    category: '经管类',
    code: '020301K',
    name: '金融学',
    description: '培养具有金融理论与实务能力的金融专门人才',
    duration: 4,
    isTop: true
  },
  {
    category: '经管类',
    code: '120203K',
    name: '会计学',
    description: '培养具有会计理论与实务能力的会计专门人才',
    duration: 4,
    isTop: false
  },
  {
    category: '人文社科类',
    code: '050101',
    name: '汉语言文学',
    description: '培养具有扎实汉语言文学基础的专门人才',
    duration: 4,
    isTop: true
  },
  {
    category: '人文社科类',
    code: '030101K',
    name: '法学',
    description: '培养具有法律理论与实务能力的法律专门人才',
    duration: 4,
    isTop: false
  }
])

const getMajorsByCategory = (category) => {
  return allMajors.value.filter(m => m.category === category)
}

const admissionPlans = ref([
  { province: '北京', scienceCount: 120, artsCount: 30, remark: '本科一批' },
  { province: '上海', scienceCount: 80, artsCount: 20, remark: '本科批' },
  { province: '广东', scienceCount: 150, artsCount: 40, remark: '本科批' },
  { province: '江苏', scienceCount: 100, artsCount: 25, remark: '本科批' },
  { province: '浙江', scienceCount: 90, artsCount: 35, remark: '第一段' },
  { province: '其他', scienceCount: 500, artsCount: 120, remark: '详见各省招生计划' }
])

const scoreLines = ref([
  {
    year: 2023,
    data: [
      { type: '理工', batch: '本科一批', minScore: 580, avgScore: 600 },
      { type: '文史', batch: '本科一批', minScore: 560, avgScore: 580 }
    ]
  },
  {
    year: 2022,
    data: [
      { type: '理工', batch: '本科一批', minScore: 575, avgScore: 595 },
      { type: '文史', batch: '本科一批', minScore: 555, avgScore: 575 }
    ]
  }
])
</script>

<style scoped>
.admission-content {
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

/* 公告列表 */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notice-card {
  transition: all 0.3s ease;
}

.notice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.notice-date {
  font-size: 0.8125rem;
  color: #909399;
}

.notice-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.notice-summary {
  font-size: 0.875rem;
  color: #606266;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 专业卡片 */
.major-card {
  height: 100%;
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.major-code {
  font-size: 0.75rem;
  color: #909399;
}

.major-name {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.major-desc {
  font-size: 0.875rem;
  color: #606266;
  margin-bottom: 1rem;
  line-height: 1.7;
}

.major-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 0.0625rem solid #e4e7ed;
}

.major-duration {
  font-size: 0.8125rem;
  color: #909399;
}

/* 分数线卡片 */
.score-card {
  margin-bottom: 1rem;
}

.score-year {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 1rem;
  text-align: center;
}

/* 联系方式 */
.contact-card {
  text-align: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9eb 100%);
  border-radius: 0.75rem;
  transition: transform 0.3s ease;
}

.contact-card:hover {
  transform: translateY(-0.25rem);
}

.contact-icon {
  color: #409eff;
  margin-bottom: 1rem;
}

.contact-card h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.contact-card p {
  font-size: 0.875rem;
  color: #606266;
  margin: 0;
}

.contact-note {
  font-size: 0.75rem !important;
  color: #909399 !important;
  margin-top: 0.25rem !important;
}
</style>
