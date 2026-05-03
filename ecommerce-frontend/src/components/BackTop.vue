<template>
  <el-backtop :bottom="60" :right="30">
    <div class="back-top-btn">
      <el-icon :size="20"><ArrowUp /></el-icon>
    </div>
  </el-backtop>
</template>

<script setup>
</script>

<style scoped>
.back-top-btn {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
  transition: all 0.3s ease;
}

.back-top-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 107, 107, 0.4);
}
</style>
