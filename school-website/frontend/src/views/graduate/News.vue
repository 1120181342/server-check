<template>
  <SubPageLayout
    pageTitle="研究生重要新闻"
    pageSubtitle="关注学院动态，获取最新资讯"
    parentTitle="研究生教育"
    parentRoute="/graduate"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="news-content">
        <!-- 新闻筛选 -->
        <div class="news-filter">
          <el-radio-group v-model="activeCategory" @change="filterNews">
            <el-radio-button label="all">全部新闻</el-radio-button>
            <el-radio-button label="academic">学术动态</el-radio-button>
            <el-radio-button label="admission">招生资讯</el-radio-button>
            <el-radio-button label="activity">校园活动</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 头条新闻 -->
        <section class="section" v-if="featuredNews">
          <el-card class="featured-card card-hover" shadow="hover">
            <el-row :gutter="30">
              <el-col :xs="24" :md="10">
                <div class="featured-image">
                  <img :src="featuredNews.image" :alt="featuredNews.title" />
                  <el-tag type="danger" class="featured-tag">头条新闻</el-tag>
                </div>
              </el-col>
              <el-col :xs="24" :md="14">
                <div class="featured-content">
                  <div class="news-meta">
                    <el-tag size="small" :type="getCategoryType(featuredNews.category)">
                      {{ getCategoryName(featuredNews.category) }}
                    </el-tag>
                    <span class="news-date">{{ featuredNews.date }}</span>
                    <span class="news-views">
                      <el-icon><View /></el-icon>
                      {{ featuredNews.views }}次阅读
                    </span>
                  </div>
                  <h3 class="featured-title">{{ featuredNews.title }}</h3>
                  <p class="featured-summary">{{ featuredNews.summary }}</p>
                  <div class="featured-footer">
                    <span class="news-source">
                      <el-icon><User /></el-icon>
                      来源：{{ featuredNews.source }}
                    </span>
                    <el-button type="primary">
                      阅读全文
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </section>

        <!-- 新闻列表 -->
        <section class="section">
          <div class="news-list">
            <el-card v-for="(news, index) in filteredNews" :key="index" class="news-item-card card-hover">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="8" :md="6">
                  <div class="news-item-image">
                    <img :src="news.image" :alt="news.title" />
                  </div>
                </el-col>
                <el-col :xs="24" :sm="16" :md="18">
                  <div class="news-item-content">
                    <div class="news-item-meta">
                      <el-tag size="small" :type="getCategoryType(news.category)">
                        {{ getCategoryName(news.category) }}
                      </el-tag>
                      <span class="news-date">{{ news.date }}</span>
                    </div>
                    <h4 class="news-item-title">{{ news.title }}</h4>
                    <p class="news-item-summary">{{ news.summary }}</p>
                    <div class="news-item-footer">
                      <span class="news-views">
                        <el-icon><View /></el-icon>
                        {{ news.views }}次阅读
                      </span>
                      <el-button type="primary" link size="small">
                        查看详情 <el-icon><ArrowRight /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </el-card>
          </div>
        </section>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[5, 10, 20]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20graduation%20ceremony%20with%20students%20in%20caps%20and%20gowns%20confetti%20celebration%20happy%20moment&image_size=landscape_16_9'
)

const activeCategory = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)

const newsList = ref([
  {
    id: 1,
    title: '我校计算机学院获批国家重点实验室',
    summary: '近日，科技部正式批准依托我校计算机学院建设"智能计算与应用"国家重点实验室。这是我校在科研平台建设方面取得的重大突破...',
    category: 'academic',
    date: '2024-08-15',
    views: 5280,
    source: '科研处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20research%20laboratory%20interior%20with%20scientists%20working%20high%20tech%20equipment%20professional%20environment&image_size=square_hd'
  },
  {
    id: 2,
    title: '2025年研究生招生咨询会成功举办',
    summary: '为帮助广大考生更好地了解我校2025年研究生招生政策，研究生院于8月10日成功举办了线上招生咨询会，来自全国各地的近万名考生参加...',
    category: 'admission',
    date: '2024-08-12',
    views: 3456,
    source: '研究生院',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=online%20webinar%20conference%20with%20professor%20giving%20presentation%20students%20listening%20virtual%20meeting&image_size=square_hd'
  },
  {
    id: 3,
    title: '我校研究生在国际学术竞赛中斩获金奖',
    summary: '在刚刚落幕的国际计算机科学竞赛(ICSC)中，由我校计算机学院研究生组成的代表队表现优异，一举斩获金奖...',
    category: 'academic',
    date: '2024-08-10',
    views: 4123,
    source: '计算机学院',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=students%20team%20winning%20award%20trophy%20celebration%20on%20stage%20happy%20moment%20academic%20competition&image_size=square_hd'
  },
  {
    id: 4,
    title: '研究生院举办新生适应系列活动',
    summary: '为帮助2024级新生尽快适应研究生生活，研究生院于8月8日至15日举办了为期一周的新生适应系列活动，包括学术规划讲座、心理健康咨询、校园文化体验等...',
    category: 'activity',
    date: '2024-08-08',
    views: 2890,
    source: '学生工作处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20student%20orientation%20event%20with%20many%20students%20gathering%20colorful%20banners%20welcome%20atmosphere&image_size=square_hd'
  },
  {
    id: 5,
    title: '关于2025年推免生接收工作的重要通知',
    summary: '为做好2025年推荐优秀应届本科毕业生免试攻读硕士学位研究生工作，根据教育部有关文件精神，结合我校实际情况，现将有关事项通知如下...',
    category: 'admission',
    date: '2024-08-05',
    views: 6789,
    source: '研究生院',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=important%20announcement%20notice%20board%20in%20university%20campus%20students%20reading%20information%20academic%20setting&image_size=square_hd'
  },
  {
    id: 6,
    title: '知名学术大师来校作学术报告',
    summary: '应研究生院邀请，国际知名计算机科学家、美国工程院院士Smith教授于8月3日来校作题为"人工智能的未来发展趋势"的学术报告...',
    category: 'academic',
    date: '2024-08-03',
    views: 3567,
    source: '国际交流处',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20lecture%20hall%20with%20professor%20giving%20speech%20audience%20listening%20attentively%20academic%20conference&image_size=square_hd'
  }
])

const featuredNews = computed(() => newsList.value[0])

const filteredNews = computed(() => {
  if (activeCategory.value === 'all') {
    return newsList.value.slice(1)
  }
  return newsList.value.filter(n => n.category === activeCategory.value)
})

const total = computed(() => filteredNews.value.length)

const getCategoryType = (category) => {
  const types = {
    academic: 'primary',
    admission: 'success',
    activity: 'warning'
  }
  return types[category] || 'info'
}

const getCategoryName = (category) => {
  const names = {
    academic: '学术动态',
    admission: '招生资讯',
    activity: '校园活动'
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

.section {
  margin-bottom: 1.5rem;
}

/* 新闻筛选 */
.news-filter {
  margin-bottom: 1.5rem;
}

/* 头条新闻 */
.featured-card {
  padding: 1.5rem;
}

.featured-image {
  position: relative;
  width: 100%;
  height: 15.625rem;
  border-radius: 0.5rem;
  overflow: hidden;
}

.featured-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.featured-tag {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
}

.featured-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
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

.featured-title {
  font-size: 1.375rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.featured-summary {
  font-size: 0.9375rem;
  color: #606266;
  line-height: 1.8;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.featured-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 0.0625rem solid #e4e7ed;
}

.news-source {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: #909399;
}

/* 新闻列表 */
.news-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.news-item-card {
  padding: 1.25rem;
}

.news-item-image {
  width: 100%;
  height: 9.375rem;
  border-radius: 0.375rem;
  overflow: hidden;
}

.news-item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.news-item-card:hover .news-item-image img {
  transform: scale(1.05);
}

.news-item-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.news-item-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.news-item-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.news-item-card:hover .news-item-title {
  color: #409eff;
}

.news-item-summary {
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

.news-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .featured-image {
    height: 12.5rem;
    margin-bottom: 1rem;
  }
  
  .featured-content {
    height: auto;
  }
  
  .featured-footer {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .news-item-image {
    height: 9.375rem;
    margin-bottom: 1rem;
  }
}
</style>
