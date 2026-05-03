<template>
  <SubPageLayout
    pageTitle="研究生招生信息"
    pageSubtitle="追求卓越，成就梦想"
    parentTitle="研究生教育"
    parentRoute="/graduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="admission-content">
        <!-- 招生公告 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Notification /></el-icon>
            <span>招生公告</span>
          </h3>
          <div class="notice-list">
            <el-card v-for="(notice, index) in notices" :key="index" class="notice-card card-hover">
              <div class="notice-header">
                <span class="notice-tag" :class="'type-' + notice.type">
                  {{ notice.type === 1 ? '重要通知' : notice.type === 2 ? '招生政策' : '常见问题' }}
                </span>
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

        <!-- 招生专业 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Collection /></el-icon>
            <span>招生专业目录</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="8" v-for="(major, index) in majors" :key="index">
              <el-card class="major-card card-hover" shadow="hover">
                <template #header>
                  <div class="major-header">
                    <el-icon :size="32" class="major-icon"><component :is="major.icon" /></el-icon>
                    <span class="major-count">{{ major.count }}个专业方向</span>
                  </div>
                </template>
                <h4 class="major-name">{{ major.name }}</h4>
                <p class="major-desc">{{ major.description }}</p>
                <div class="major-tags">
                  <el-tag v-for="(tag, idx) in major.tags" :key="idx" size="small" effect="plain">
                    {{ tag }}
                  </el-tag>
                </div>
                <el-button type="primary" size="small" style="margin-top: 1rem; width: 100%">
                  查看专业详情
                </el-button>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 招生简章 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Document /></el-icon>
            <span>招生简章</span>
          </h3>
          <el-table :data="admissionDocs" style="width: 100%" stripe>
            <el-table-column prop="title" label="文件名称" min-width="200">
              <template #default="scope">
                <div class="doc-item">
                  <el-icon class="doc-icon"><Document /></el-icon>
                  <span>{{ scope.row.title }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="文件类型" width="120">
              <template #default="scope">
                <el-tag size="small">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updateTime" label="更新时间" width="120" />
            <el-table-column prop="size" label="文件大小" width="100" />
            <el-table-column label="操作" width="120">
              <template #default>
                <el-button type="primary" link size="small">下载</el-button>
                <el-button type="primary" link size="small">预览</el-button>
              </template>
            </el-table-column>
          </el-table>
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
                <p>yzb@xxuniversity.edu.cn</p>
                <p class="contact-note">24小时内回复</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><Location /></el-icon>
                <h4>办公地址</h4>
                <p>行政楼202室</p>
                <p class="contact-note">欢迎现场咨询</p>
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20graduate%20school%20entrance%20with%20modern%20architecture%20students%20in%20graduation%20gowns%20cherry%20blossom%20spring&image_size=landscape_16_9'
)

const notices = ref([
  {
    type: 1,
    date: '2024-08-15',
    title: '2025年硕士研究生招生简章发布',
    summary: '我校2025年硕士研究生招生工作即将启动，现将招生简章及专业目录公布，请广大考生仔细阅读...'
  },
  {
    type: 2,
    date: '2024-08-10',
    title: '关于2025年推免生接收工作的通知',
    summary: '为做好2025年推荐优秀应届本科毕业生免试攻读硕士学位研究生工作，现将有关事项通知如下...'
  },
  {
    type: 3,
    date: '2024-08-05',
    title: '2025年研究生招生常见问题解答',
    summary: '为帮助广大考生更好地了解我校2025年研究生招生政策，我们整理了考生常见问题及解答...'
  }
])

const majors = ref([
  {
    name: '计算机科学与技术',
    description: '培养具有扎实理论基础和创新能力的计算机专业高层次人才',
    count: 8,
    icon: 'Cpu',
    tags: ['国家级重点学科', '博士点授权', '双一流建设']
  },
  {
    name: '电子信息工程',
    description: '研究信息获取、处理、传输等关键技术的前沿领域',
    count: 6,
    icon: 'Monitor',
    tags: ['省级重点学科', '硕士点授权', '校企合作']
  },
  {
    name: '机械工程',
    description: '面向智能制造、先进制造等国家重大需求的学科',
    count: 5,
    icon: 'Setting',
    tags: ['国家级特色专业', '工程博士点', '产学研结合']
  },
  {
    name: '应用经济学',
    description: '研究经济运行规律和政策制定的应用型学科',
    count: 7,
    icon: 'TrendCharts',
    tags: ['省级重点学科', '金融硕士点', '实习基地']
  },
  {
    name: '材料科学与工程',
    description: '探索新材料研发和应用的前沿学科',
    count: 4,
    icon: 'MagicStick',
    tags: ['双一流建设', '国家重点实验室', '博士后流动站']
  },
  {
    name: '环境科学与工程',
    description: '致力于环境保护和可持续发展的交叉学科',
    count: 5,
    icon: 'Sunny',
    tags: ['绿色发展', '校企联合培养', '国际合作']
  }
])

const admissionDocs = ref([
  {
    title: 'XX大学2025年硕士研究生招生简章',
    type: 'PDF',
    updateTime: '2024-08-15',
    size: '2.5 MB'
  },
  {
    title: '2025年硕士研究生招生专业目录',
    type: 'PDF',
    updateTime: '2024-08-15',
    size: '1.8 MB'
  },
  {
    title: '推免生申请材料模板',
    type: 'DOC',
    updateTime: '2024-08-10',
    size: '520 KB'
  },
  {
    title: '研究生奖助学金政策说明',
    type: 'PDF',
    updateTime: '2024-08-01',
    size: '890 KB'
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

.notice-tag {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  color: #fff;
}

.type-1 {
  background: #f56c6c;
}

.type-2 {
  background: #67c23a;
}

.type-3 {
  background: #409eff;
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

.major-icon {
  color: #409eff;
}

.major-count {
  font-size: 0.75rem;
  color: #909399;
}

.major-name {
  font-size: 1.125rem;
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

.major-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

/* 文档列表 */
.doc-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.doc-icon {
  color: #409eff;
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
