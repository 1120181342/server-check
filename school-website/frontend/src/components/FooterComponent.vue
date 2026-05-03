<template>
  <footer class="footer-container">
    <div class="footer-content">
      <div class="footer-main">
        <div class="footer-section about-section">
          <div class="footer-logo">
            <el-icon :size="32"><School /></el-icon>
            <span class="footer-school-name">XX大学</span>
          </div>
          <p class="footer-desc">
            XX大学是一所历史悠久、学科齐全的综合性研究型大学，致力于培养具有创新精神和实践能力的高素质人才。
          </p>
          <div class="contact-info">
            <div class="contact-item">
              <el-icon><Location /></el-icon>
              <span>地址：XX市XX区XX路XX号</span>
            </div>
            <div class="contact-item">
              <el-icon><Phone /></el-icon>
              <span>电话：400-XXX-XXXX</span>
            </div>
            <div class="contact-item">
              <el-icon><Message /></el-icon>
              <span>邮箱：info@xxuniversity.edu.cn</span>
            </div>
          </div>
        </div>
        
        <div class="footer-section links-section">
          <h4 class="section-title">快速链接</h4>
          <ul class="link-list">
            <li><router-link to="/">首页</router-link></li>
            <li><router-link to="/graduate/admission">研究生招生</router-link></li>
            <li><router-link to="/undergraduate/admission">本科生招生</router-link></li>
            <li><router-link to="/doctoral/admission">博士生招生</router-link></li>
            <li><router-link to="/personal/login">个人中心</router-link></li>
          </ul>
        </div>
        
        <div class="footer-section sections">
          <h4 class="section-title">学院导航</h4>
          <ul class="link-list">
            <li><a href="javascript:;">计算机学院</a></li>
            <li><a href="javascript:;">电子工程学院</a></li>
            <li><a href="javascript:;">机械工程学院</a></li>
            <li><a href="javascript:;">经济管理学院</a></li>
            <li><a href="javascript:;">人文学院</a></li>
          </ul>
        </div>
        
        <div class="footer-section follow-section">
          <h4 class="section-title">关注我们</h4>
          <div class="qrcode-container">
            <div class="qrcode-item">
              <div class="qrcode">
                <el-icon :size="60"><QRCode /></el-icon>
              </div>
              <p class="qrcode-desc">微信公众号</p>
            </div>
            <div class="qrcode-item">
              <div class="qrcode">
                <el-icon :size="60"><Share /></el-icon>
              </div>
              <p class="qrcode-desc">官方微博</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="footer-bottom">
        <div class="bottom-content">
          <p>Copyright © 2024 XX大学 版权所有</p>
          <p>ICP备案号：京ICP备XXXXXXXX号-X</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
.footer-container {
  background: linear-gradient(135deg, #0a4b8e 0%, #083d77 100%);
  color: rgba(255, 255, 255, 0.9);
  margin-top: auto;
}

.footer-content {
  max-width: 75rem;
  margin: 0 auto;
}

.footer-main {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1fr 1.5fr;
  gap: 2.5rem;
  padding: 2.5rem 1.25rem;
  border-bottom: 0.0625rem solid rgba(255, 255, 255, 0.1);
}

.footer-section {
  display: flex;
  flex-direction: column;
}

.about-section {
  grid-column: span 1;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.footer-logo .el-icon {
  color: #fff;
}

.footer-school-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
}

.footer-desc {
  font-size: 0.875rem;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 1.25rem;
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
}

.contact-item .el-icon {
  color: #67c23a;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 1rem;
  position: relative;
  padding-bottom: 0.5rem;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 2.5rem;
  height: 0.125rem;
  background: #67c23a;
}

.link-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.link-list li {
  transition: transform 0.3s ease;
}

.link-list li:hover {
  transform: translateX(0.3125rem);
}

.link-list a,
.link-list .router-link-active {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.3s ease;
}

.link-list a:hover,
.link-list .router-link-active:hover {
  color: #67c23a;
}

.qrcode-container {
  display: flex;
  gap: 1.5rem;
}

.qrcode-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.qrcode {
  width: 6.25rem;
  height: 6.25rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qrcode .el-icon {
  color: rgba(255, 255, 255, 0.9);
}

.qrcode-desc {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.footer-bottom {
  background: rgba(0, 0, 0, 0.2);
  padding: 1.25rem;
}

.bottom-content {
  max-width: 75rem;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.bottom-content p {
  margin: 0;
}

@media (max-width: 768px) {
  .footer-main {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .about-section {
    grid-column: span 1;
  }
  
  .bottom-content {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
