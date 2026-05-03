<template>
  <footer class="footer-container">
    <div class="footer-service">
      <div class="container">
        <div class="service-list">
          <div class="service-item">
            <el-icon :size="40"><Trophy /></el-icon>
            <div class="service-info">
              <h4>正品保障</h4>
              <p>100%正品行货</p>
            </div>
          </div>
          <div class="service-item">
            <el-icon :size="40"><Van /></el-icon>
            <div class="service-info">
              <h4>极速配送</h4>
              <p>当日达/次日达</p>
            </div>
          </div>
          <div class="service-item">
            <el-icon :size="40"><Back /></el-icon>
            <div class="service-info">
              <h4>7天无理由</h4>
              <p>退换货无忧</p>
            </div>
          </div>
          <div class="service-item">
            <el-icon :size="40"><Headset /></el-icon>
            <div class="service-info">
              <h4>专业客服</h4>
              <p>7x24小时服务</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="footer-links">
      <div class="container">
        <div class="links-content">
          <div class="links-section">
            <h4>购物指南</h4>
            <ul>
              <li><a href="javascript:void(0)">购物流程</a></li>
              <li><a href="javascript:void(0)">会员介绍</a></li>
              <li><a href="javascript:void(0)">生活旅行</a></li>
              <li><a href="javascript:void(0)">常见问题</a></li>
              <li><a href="javascript:void(0)">联系客服</a></li>
            </ul>
          </div>
          <div class="links-section">
            <h4>配送方式</h4>
            <ul>
              <li><a href="javascript:void(0)">上门自提</a></li>
              <li><a href="javascript:void(0)">211限时达</a></li>
              <li><a href="javascript:void(0)">配送服务查询</a></li>
              <li><a href="javascript:void(0)">配送费收取标准</a></li>
              <li><a href="javascript:void(0)">海外配送</a></li>
            </ul>
          </div>
          <div class="links-section">
            <h4>支付方式</h4>
            <ul>
              <li><a href="javascript:void(0)">货到付款</a></li>
              <li><a href="javascript:void(0)">在线支付</a></li>
              <li><a href="javascript:void(0)">分期付款</a></li>
              <li><a href="javascript:void(0)">优惠券说明</a></li>
              <li><a href="javascript:void(0)">活动说明</a></li>
            </ul>
          </div>
          <div class="links-section">
            <h4>售后服务</h4>
            <ul>
              <li><a href="javascript:void(0)">售后政策</a></li>
              <li><a href="javascript:void(0)">价格保护</a></li>
              <li><a href="javascript:void(0)">退款说明</a></li>
              <li><a href="javascript:void(0)">取消订单</a></li>
              <li><a href="javascript:void(0)">售后服务</a></li>
            </ul>
          </div>
          <div class="links-section contact-section">
            <h4>联系我们</h4>
            <div class="contact-item">
              <el-icon><Phone /></el-icon>
              <span>客服热线：400-123-4567</span>
            </div>
            <div class="contact-item">
              <el-icon><ChatDotRound /></el-icon>
              <span>在线客服</span>
            </div>
            <div class="qr-code">
              <div class="qr-item">
                <div class="qr-placeholder">
                  <el-icon :size="60"><QRCode /></el-icon>
                </div>
                <p>扫码关注</p>
              </div>
              <div class="qr-item">
                <div class="qr-placeholder">
                  <el-icon :size="60"><Promotion /></el-icon>
                </div>
                <p>APP下载</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="footer-copyright">
      <div class="container">
        <div class="copyright-content">
          <div class="copyright-text">
            <p>© 2024 优选商城 版权所有 | 京ICP备XXXXXXXX号</p>
            <p class="links">
              <a href="javascript:void(0)">关于我们</a>
              <span>|</span>
              <a href="javascript:void(0)">联系我们</a>
              <span>|</span>
              <a href="javascript:void(0)">招贤纳士</a>
              <span>|</span>
              <a href="javascript:void(0)">用户协议</a>
              <span>|</span>
              <a href="javascript:void(0)">隐私政策</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
.footer-container {
  background: #f5f5f5;
  border-top: 1px solid #eee;
}

.footer-service {
  padding: 30px 0;
  border-bottom: 1px solid #eee;
}

.service-list {
  display: flex;
  justify-content: space-between;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 40px;
}

.service-item:not(:last-child) {
  border-right: 1px solid #eee;
}

.service-item > .el-icon {
  color: #ff6b6b;
}

.service-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
}

.service-info p {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.footer-links {
  padding: 40px 0;
}

.links-content {
  display: flex;
  gap: 60px;
}

.links-section {
  flex: 1;
}

.links-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
}

.links-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.links-section li {
  margin-bottom: 10px;
}

.links-section a {
  color: #666;
  font-size: 12px;
  text-decoration: none;
  transition: color 0.2s;
}

.links-section a:hover {
  color: #ff6b6b;
}

.contact-section {
  flex: 0 0 280px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

.contact-item .el-icon {
  color: #ff6b6b;
}

.qr-code {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.qr-item {
  text-align: center;
}

.qr-placeholder {
  width: 80px;
  height: 80px;
  background: #fff;
  border: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  color: #ccc;
}

.qr-item p {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.footer-copyright {
  background: #333;
  padding: 20px 0;
}

.copyright-content {
  text-align: center;
}

.copyright-text p {
  font-size: 12px;
  color: #999;
  margin: 0 0 8px 0;
}

.copyright-text .links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.copyright-text .links a {
  color: #999;
  text-decoration: none;
  transition: color 0.2s;
}

.copyright-text .links a:hover {
  color: #fff;
}

.copyright-text .links span {
  color: #555;
}
</style>
