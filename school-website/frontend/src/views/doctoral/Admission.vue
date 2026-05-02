<template>
  <SubPageLayout
    pageTitle="博士生招生信息"
    pageSubtitle="攀登学术高峰，引领科技创新"
    parentTitle="博士生教育"
    parentRoute="/doctoral"
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
                <el-tag :type="notice.type === 1 ? 'danger' : 'primary'" size="small">
                  {{ notice.type === 1 ? '重要通知' : '常见问题' }}
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

        <!-- 招生类型 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Collection /></el-icon>
            <span>招生类型</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8" v-for="(type, index) in admissionTypes" :key="index">
              <el-card class="type-card card-hover" shadow="hover">
                <div class="type-icon" :style="{ background: type.bgColor }">
                  <el-icon :size="40" :color="#fff">
                    <component :is="type.icon" />
                  </el-icon>
                </div>
                <h4 class="type-name">{{ type.name }}</h4>
                <p class="type-desc">{{ type.description }}</p>
                <el-divider />
                <div class="type-info">
                  <div class="info-item">
                    <span class="info-label">招生对象</span>
                    <span class="info-value">{{ type.target }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">招生方式</span>
                    <span class="info-value">{{ type.method }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">学制</span>
                    <span class="info-value">{{ type.duration }}</span>
                  </div>
                </div>
                <el-button type="primary" size="small" style="width: 100%; margin-top: 1rem">
                  了解详情
                </el-button>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 博士生导师 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><User /></el-icon>
            <span>博士生导师</span>
          </h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="8" v-for="(supervisor, index) in supervisors" :key="index">
              <el-card class="supervisor-card card-hover" shadow="hover">
                <div class="supervisor-avatar">
                  <el-avatar :size="80">
                    <img :src="supervisor.avatar" :alt="supervisor.name" />
                  </el-avatar>
                </div>
                <div class="supervisor-info">
                  <h4 class="supervisor-name">{{ supervisor.name }}</h4>
                  <p class="supervisor-title">{{ supervisor.title }}</p>
                  <div class="supervisor-tags">
                    <el-tag v-for="(tag, idx) in supervisor.tags" :key="idx" size="small" effect="plain">
                      {{ tag }}
                    </el-tag>
                  </div>
                  <p class="supervisor-major">研究方向：{{ supervisor.research }}</p>
                  <el-button type="primary" link size="small">查看导师主页</el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <!-- 招生简章文件 -->
        <section class="section">
          <h3 class="section-header">
            <el-icon><Document /></el-icon>
            <span>招生简章与文件</span>
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
            <el-table-column prop="type" label="文件类型" width="100">
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
                <p class="contact-note">工作日 8:30-11:30, 14:00-17:00</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><Message /></el-icon>
                <h4>电子邮箱</h4>
                <p>bss@xxuniversity.edu.cn</p>
                <p class="contact-note">24小时内回复</p>
              </div>
            </el-col>
            <el-col :xs="24" :sm="8">
              <div class="contact-card">
                <el-icon :size="40" class="contact-icon"><Location /></el-icon>
                <h4>办公地址</h4>
                <p>研究生院博士生招生办公室</p>
                <p class="contact-note">行政楼305室</p>
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
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=university%20research%20laboratory%20with%20scientists%20working%20high%20tech%20equipment%20phd%20students%20academic%20research&image_size=landscape_16_9'
)

const notices = ref([
  {
    type: 1,
    date: '2024-07-20',
    title: 'XX大学2025年博士研究生招生简章',
    summary: '根据教育部有关文件精神，结合我校实际情况，现将2025年博士研究生招生工作安排如下...'
  },
  {
    type: 1,
    date: '2024-07-15',
    title: '关于2025年"申请-考核"制博士生招生工作的通知',
    summary: '为深化博士生招生制度改革，提高博士生选拔质量，我校2025年继续采用"申请-考核"制招收博士生...'
  },
  {
    type: 2,
    date: '2024-07-10',
    title: '2025年博士生招生常见问题解答',
    summary: '为帮助广大考生更好地了解我校2025年博士生招生政策，我们整理了考生常见问题及解答...'
  }
])

const admissionTypes = ref([
  {
    name: '申请-考核制',
    description: '通过申请材料审核与综合考核相结合的方式选拔优秀博士生',
    icon: 'DocumentChecked',
    bgColor: 'linear-gradient(135deg, #409eff 0%, #67c23a 100%)',
    target: '全日制硕士毕业生',
    method: '材料审核+综合考核',
    duration: '3-4年'
  },
  {
    name: '硕博连读',
    description: '选拔优秀在读硕士生直接攻读博士学位',
    icon: 'TrendCharts',
    bgColor: 'linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%)',
    target: '在读优秀硕士生',
    method: '选拔考核',
    duration: '5年'
  },
  {
    name: '直博生',
    description: '选拔优秀应届本科毕业生直接攻读博士学位',
    icon: 'Medal',
    bgColor: 'linear-gradient(135deg, #909399 0%, #606266 100%)',
    target: '应届优秀本科生',
    method: '推免选拔',
    duration: '5年'
  }
])

const supervisors = ref([
  {
    name: '张院士',
    title: '中国工程院院士、博士生导师',
    tags: ['长江学者', '国家杰青'],
    research: '人工智能、机器学习、计算机视觉',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20senior%20asian%20male%20professor%20portrait%20academic%20style%20with%20glasses&image_size=square'
  },
  {
    name: '李教授',
    title: '国家杰出青年基金获得者、博士生导师',
    tags: ['千人计划', '长江学者'],
    research: '数据科学、大数据分析、云计算',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20asian%20female%20professor%20portrait%20academic%20style%20confident&image_size=square'
  },
  {
    name: '王教授',
    title: '长江学者特聘教授、博士生导师',
    tags: ['国家杰青', '创新团队负责人'],
    research: '网络安全、密码学、信息安全',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20mid%20age%20asian%20male%20professor%20portrait%20academic%20style&image_size=square'
  },
  {
    name: '陈教授',
    title: '国家优秀青年基金获得者、博士生导师',
    tags: ['青年拔尖', '新世纪人才'],
    research: '计算机图形学、虚拟现实、人机交互',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20young%20asian%20female%20professor%20portrait%2 energetic%20academic%20style&image_size=square'
  },
  {
    name: '刘教授',
    title: '教育部新世纪优秀人才、博士生导师',
    tags: ['省级特聘', '学术带头人'],
    research: '软件工程、形式化方法、程序验证',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20mid%20career%20asian%20male%20professor%20portrait%20academic%20style&image_size=square'
  },
  {
    name: '赵教授',
    title: '国家自然科学基金重点项目负责人、博士生导师',
    tags: ['创新人才', '省级名师'],
    research: '分布式系统、边缘计算、物联网',
    avatar: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20mid%2 career%20asian%20female%20professor%20portrait%20accomplished%20academic%20style&image_size=square'
  }
])

const admissionDocs = ref([
  {
    title: 'XX大学2025年博士研究生招生简章',
    type: 'PDF',
    updateTime: '2024-07-20',
    size: '3.2 MB'
  },
  {
    title: '"申请-考核"制博士生招生工作细则',
    type: 'PDF',
    updateTime: '2024-07-20',
    size: '1.8 MB'
  },
  {
    title: '博士生导师信息一览表',
    type: 'PDF',
    updateTime: '2024-07-15',
    size: '2.5 MB'
  },
  {
    title: '申请材料模板及填写说明',
    type: 'DOC',
    updateTime: '2024-07-10',
    size: '680 KB'
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

/* 招生类型卡片 */
.type-card {
  height: 100%;
}

.type-icon {
  width: 5rem;
  height: 5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.type-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  text-align: center;
  margin-bottom: 0.5rem;
}

.type-desc {
  font-size: 0.875rem;
  color: #606266;
  text-align: center;
  line-height: 1.7;
  margin-bottom: 1rem;
}

.type-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
}

.info-label {
  color: #909399;
}

.info-value {
  color: #1a1a1a;
  font-weight: 500;
}

/* 导师卡片 */
.supervisor-card {
  text-align: center;
}

.supervisor-avatar {
  margin-bottom: 1rem;
}

.supervisor-avatar :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.supervisor-name {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.supervisor-title {
  font-size: 0.75rem;
  color: #409eff;
  margin-bottom: 0.5rem;
}

.supervisor-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.supervisor-major {
  font-size: 0.8125rem;
  color: #606266;
  margin-bottom: 0.75rem;
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
