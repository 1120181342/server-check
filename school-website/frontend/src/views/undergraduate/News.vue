<template>
  <SubPageLayout
    pageTitle="本科生重要新闻"
    pageSubtitle="关注校园动态，成长与你同行"
    parentTitle="本科生教育"
    parentRoute="/undergraduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="news-content">
        <!-- 新闻分类 -->
        <div class="news-tabs">
          <el-tabs v-model="activeCategory" @tab-change="filterNews">
            <el-tab-pane label="全部新闻" name="all" />
            <el-tab-pane label="教学资讯" name="teaching" />
            <el-tab-pane label="校园活动" name="activity" />
            <el-tab-pane label="招生就业" name="career" />
            <el-tab-pane label="学生风采" name="student" />
          </el-tabs>
        </div>

        <!-- 新闻列表 -->
        <div class="news-list">
          <el-card v-for="(news, index) in filteredNews" :key="index" class="news-card card-hover">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="6">
                <div class="news-image">
                  <img :src="news.image" :alt="news.title" />
                </div>
              </el-col>
              <el-col :xs="24" :sm="18">
                <div class="news-info">
                  <div class="news-meta">
                    <el-tag :type="getTagType(news.category)" size="small">
                      {{ getCategoryName(news.category) }}
                    </el-tag>
                    <span class="news-date">{{ news.date }}</span>
                    <span class="news-views">
                      <el-icon><View /></el-icon>
                      {{ news.views }}次阅读
                    </span>
                  </div>
                  <h4 class="news-title">{{ news.title }}</h4>
                  <p class="news-summary">{{ news.summary }}</p>
                  <div class="news-footer">
                    <span class="news-source">
                      <el-icon><OfficeBuilding /></el-icon>
                      来源：{{ news.source }}
                    </span>
                    <el-button type="primary" link size="small">
                      阅读全文 <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </div>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[5, 10, 20]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </template>
  </SubPageLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import SubPageLayout from '@/components/SubPageLayout.vue'

const bannerImage = ref(
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20students%20celebrating%20graduation%20with%20caps%20and%20gowns%20colorful%20balloons%20happy%20moment%20campus&image_size=landscape_16_9'
)

const activeCategory = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)

const newsList = ref([
  {
    id: 1,
    title: '我校学子在全国大学生程序设计竞赛中斩获金奖',
    summary: '在刚刚落幕的第15届全国大学生程序设计竞赛中，由我校计算机学院本科生组成的代表队表现优异，从全国500余支代表队中脱颖而出，一举斩获金奖...',
    category: 'student',
    date: '2024-06-25',
    views: 3256,
    source: '计算机学院',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20students%20winning%20competition%20award%20on%20stage%20holding%20trophy%20happy%20celebration%20academic%20event&image_size=square_hd'
  },
  {
    id: 2,
    title: '关于2024-2025学年第一学期选课安排的通知',
    summary: '为做好2024-2025学年第一学期的选课工作，现将有关事项通知如下：选课时间、选课流程、注意事项等，请各位同学务必在规定时间内完成选课...',
    category: 'teaching',
    date: '2024-06-20',
    views: 5678,
    source: '教务处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20computer%20lab%20students%20using%20computers%20for%20course%20registration%20academic%20setting&image_size=square_hd'
  },
  {
    id: 3,
    title: '2024届毕业生就业质量报告发布',
    summary: '我校2024届毕业生就业质量报告今日正式发布。报告显示，2024届毕业生总体就业率达98.5%，平均起薪较去年增长12%，就业质量持续提升...',
    category: 'career',
    date: '2024-06-18',
    views: 4321,
    source: '就业指导中心',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20career%20fair%20with%20students%20talking%20to%20recruiters%20professional%20setting%20job%20interview&image_size=square_hd'
  },
  {
    id: 4,
    title: '校园文化艺术节精彩开幕',
    summary: 'XX大学第20届校园文化艺术节于6月15日在主校区体育馆精彩开幕。本届艺术节以"青春飞扬，梦想启航"为主题，为期一周，将举办文艺演出、书画展览、演讲比赛等系列活动...',
    category: 'activity',
    date: '2024-06-15',
    views: 2890,
    source: '校团委',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20campus%20culture%20festival%20colorful%20stage%20performance%20students%20dancing%20celebration%20atmosphere&image_size=square_hd'
  },
  {
    id: 5,
    title: '我校新增3个国家级一流本科专业建设点',
    summary: '近日，教育部办公厅公布了2024年度国家级和省级一流本科专业建设点名单。我校计算机科学与技术、电子信息工程、机械设计制造及其自动化三个专业获批国家级一流本科专业建设点...',
    category: 'teaching',
    date: '2024-06-10',
    views: 3567,
    source: '教务处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20academic%20building%20exterior%20modern%20architecture%20blue%20sky%20white%20clouds%20education%20environment&image_size=square_hd'
  },
  {
    id: 6,
    title: '2024年暑期社会实践活动报名通知',
    summary: '为深入学习贯彻习近平新时代中国特色社会主义思想，引导广大青年学生在社会实践中受教育、长才干、作贡献，学校决定组织开展2024年暑期社会实践活动...',
    category: 'activity',
    date: '2024-06-08',
    views: 4123,
    source: '学生工作处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20students%20volunteering%20in%20community%20service%20helping%20people%20social%20practice%20activity&image_size=square_hd'
  }
])

const filteredNews = computed(() => {
  if (activeCategory.value === 'all') {
    return newsList.value
  }
  return newsList.value.filter(n => n.category === activeCategory.value)
})

const total = computed(() => filteredNews.value.length)

const getTagType = (category) => {
  const types = {
    teaching: 'primary',
    activity: 'success',
    career: 'warning',
    student: 'danger'
  }
  return types[category] || 'info'
}

const getCategoryName = (category) => {
  const names = {
    teaching: '教学资讯',
    activity: '校园活动',
    career: '招生就业',
    student: '学生风采'
  }
  return names[category] || '新闻'
}

const filterNews = () => {
  currentPage.value = 1
}

const handleSizeChange = (val) => {
  pageSize.value = val
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}
</script>

<style scoped>
.news-content {
  line-height: 1.8;
}

/* 新闻分类标签 */
.news-tabs {
  margin-bottom: 1.5rem;
}

/* 新闻列表 */
.news-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.news-card {
  padding: 1.25rem;
}

.news-image {
  width: 100%;
  height: 8.75rem;
  border-radius: 0.375rem;
  overflow: hidden;
}

.news-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.news-card:hover .news-image img {
  transform: scale(1.05);
}

.news-info {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.news-date {
  font-size: 0.8125rem;
  color: #909399;
}

.news-views {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: #909399;
}

.news-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.news-card:hover .news-title {
  color: #409eff;
}

.news-summary {
  font-size: 0.875rem;
  color: #606266;
  line-height: 1.7;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.5rem;
}

.news-source {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: #909399;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .news-image {
    height: 9.375rem;
    margin-bottom: 1rem;
  }
}
</style>
