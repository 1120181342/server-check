<template>
  <SubPageLayout
    pageTitle="博士生重要新闻"
    pageSubtitle="追踪学术前沿，见证科研突破"
    parentTitle="博士生教育"
    parentRoute="/doctoral"
    :bannerImage="bannerImage"
  >
    <template #content>
      <div class="news-content">
        <!-- 头条新闻 -->
        <section class="section" v-if="featuredNews">
          <el-card class="featured-card card-hover" shadow="hover">
            <el-row :gutter="30">
              <el-col :xs="24" :md="10">
                <div class="featured-image">
                  <img :src="featuredNews.image" :alt="featuredNews.title" />
                  <el-tag type="danger" class="featured-tag">科研突破</el-tag>
                </div>
              </el-col>
              <el-col :xs="24" :md="14">
                <div class="featured-content">
                  <div class="news-meta">
                    <el-tag size="small" type="danger">重要成果</el-tag>
                    <span class="news-date">{{ featuredNews.date }}</span>
                    <span class="news-views">
                      <el-icon><View /></el-icon>
                      {{ featuredNews.views }}次阅读
                    </span>
                  </div>
                  <h3 class="featured-title">{{ featuredNews.title }}</h3>
                  <p class="featured-summary">{{ featuredNews.summary }}</p>
                  <div class="featured-footer">
                    <span class="news-author">
                      <el-icon><User /></el-icon>
                      作者：{{ featuredNews.author }}
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

        <!-- 新闻分类 -->
        <div class="news-tabs">
          <el-radio-group v-model="activeCategory" @change="filterNews">
            <el-radio-button label="all">全部新闻</el-radio-button>
            <el-radio-button label="research">科研成果</el-radio-button>
            <el-radio-button label="academic">学术动态</el-radio-button>
            <el-radio-button label="admission">招生资讯</el-radio-button>
            <el-radio-button label="award">获奖荣誉</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 新闻列表 -->
        <div class="news-list">
          <el-card v-for="(news, index) in filteredNews" :key="index" class="news-item-card card-hover">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="6">
                <div class="news-item-image">
                  <img :src="news.image" :alt="news.title" />
                </div>
              </el-col>
              <el-col :xs="24" :sm="18">
                <div class="news-item-info">
                  <div class="news-item-meta">
                    <el-tag :type="getTagType(news.category)" size="small">
                      {{ getCategoryName(news.category) }}
                    </el-tag>
                    <span class="news-date">{{ news.date }}</span>
                    <span class="news-views">
                      <el-icon><View /></el-icon>
                      {{ news.views }}次阅读
                    </span>
                  </div>
                  <h4 class="news-item-title">{{ news.title }}</h4>
                  <p class="news-item-summary">{{ news.summary }}</p>
                  <div class="news-item-footer">
                    <span class="news-source">
                      <el-icon><OfficeBuilding /></el-icon>
                      来源：{{ news.source }}
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=scientists%20celebrating%20research%20breakthrough%20in%20modern%20laboratory%20with%20high%20tech%20equipment%20academic%20success&image_size=landscape_16_9'
)

const activeCategory = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)

const newsList = ref([
  {
    id: 1,
    title: '我校计算机学院团队在人工智能领域取得重大突破',
    summary: '近日，我校计算机学院张院士团队在自然语言处理领域取得重大突破，相关研究成果发表于国际顶级期刊《Nature Machine Intelligence》。该研究提出了一种新的深度学习模型架构，在多项国际评测中取得了领先成绩...',
    category: 'research',
    date: '2024-07-25',
    views: 8560,
    source: '计算机学院',
    author: '张院士团队',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=scientists%20working%20on%20AI%20research%20in%20modern%20lab%20with%20computer%20screens%20showing%20neural%20network%20visualization&image_size=square_hd'
  },
  {
    id: 2,
    title: '关于2025年博士生招生工作的重要通知',
    summary: '根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下。2025年我校继续采用"申请-考核"制招收博士生，同时保留硕博连读和直博生招生渠道...',
    category: 'admission',
    date: '2024-07-20',
    views: 6789,
    source: '研究生院',
    author: '招生办公室',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20admission%20office%20with%20students%20submitting%20applications%20professional%20environment&image_size=square_hd'
  },
  {
    id: 3,
    title: '我校博士生在国际顶级会议发表论文并获最佳论文奖',
    summary: '在近日召开的第45届国际计算机体系结构会议(ISCA 2024)上，我校电子工程学院李教授指导的博士生王同学的论文荣获最佳论文奖。这是我校首次在该顶级会议上获得此项殊荣...',
    category: 'award',
    date: '2024-07-18',
    views: 5432,
    source: '电子工程学院',
    author: '李教授团队',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=student%20receiving%20best%20paper%20award%20at%20international%20conference%20on%20stage%20with%2 trophy%20academic%20celebration&image_size=square_hd'
  },
  {
    id: 4,
    title: '国际知名学术大师来校讲学并与博士生交流',
    summary: '应研究生院邀请，美国工程院院士、斯坦福大学著名教授Johnson于7月15日至20日来校访问讲学。期间，Johnson教授为我校师生作了题为"人工智能的未来发展趋势"的精彩学术报告...',
    category: 'academic',
    date: '2024-07-15',
    views: 4123,
    source: '国际交流处',
    author: '外事办公室',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=international%20professor%20giving%20lecture%20in%20university%20auditorium%20with%20students%20listening%20attentively%20academic%20conference&image_size=square_hd'
  },
  {
    id: 5,
    title: '我校材料学院团队在新能源材料领域取得重要进展',
    summary: '我校材料科学与工程学院陈教授团队在新型储能材料研究领域取得重要进展。相关研究成果发表于国际顶级期刊《Advanced Materials》。该研究开发了一种新型正极材料，使电池能量密度提升了30%以上...',
    category: 'research',
    date: '2024-07-10',
    views: 3876,
    source: '材料学院',
    author: '陈教授团队',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=materials%20science%20research%20laboratory%20with%2 scientists%20examining%20battery%20materials%20high%20tech%20equipment&image_size=square_hd'
  },
  {
    id: 6,
    title: '2024年博士生国家奖学金评审结果公示',
    summary: '根据《财政部 教育部关于印发<研究生国家奖学金管理暂行办法>的通知》文件精神，经学生申请、学院初评、学校评审委员会审核通过，现将2024年博士生国家奖学金拟获奖学生名单予以公示...',
    category: 'award',
    date: '2024-07-08',
    views: 9876,
    source: '学生工作处',
    author: '奖助中心',
    image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20award%20ceremony%20with%20students%20receiving%20scholarship%20certificates%20formal%20academic%20setting&image_size=square_hd'
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

const getTagType = (category) => {
  const types = {
    research: 'danger',
    academic: 'primary',
    admission: 'success',
    award: 'warning'
  }
  return types[category] || 'info'
}

const getCategoryName = (category) => {
  const names = {
    research: '科研成果',
    academic: '学术动态',
    admission: '招生资讯',
    award: '获奖荣誉'
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
  gap: 0.75rem;
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

.news-author {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: #909399;
}

/* 新闻分类 */
.news-tabs {
  margin-bottom: 1.5rem;
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
  height: 8.75rem;
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

.news-item-info {
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
  font-size: 1rem;
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
