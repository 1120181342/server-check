<template>
  <div 
    ref="containerRef" 
    class="virtual-list"
    :style="{ height: height + 'px' }"
  >
    <div 
      class="virtual-list-padding"
      :style="{ height: totalHeight + 'px' }"
    />
    <div 
      class="virtual-list-items"
      :style="{ transform: `translateY(${offsetY}px)` }"
    >
      <div 
        v-for="item in visibleItems" 
        :key="itemKey(item.data, item.index)"
        class="virtual-list-item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot :item="item.data" :index="item.index" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface VirtualListItem<T> {
  data: T
  index: number
}

const props = defineProps<{
  items: any[]
  itemHeight: number
  height: number
  itemKey?: (item: any, index: number) => string | number
}>()

const containerRef = ref<HTMLElement | null>(null)
const scrollTop = ref(0)

const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - bufferCount.value)
})

const endIndex = computed(() => {
  const visibleCount = Math.ceil(props.height / props.itemHeight)
  return Math.min(
    props.items.length,
    Math.floor((scrollTop.value + props.height) / props.itemHeight) + bufferCount.value + 1
  )
})

const bufferCount = computed(() => Math.ceil(props.height / props.itemHeight / 2))

const totalHeight = computed(() => props.items.length * props.itemHeight)

const offsetY = computed(() => startIndex.value * props.itemHeight)

const visibleItems = computed<VirtualListItem<any>[]>(() => {
  return props.items.slice(startIndex.value, endIndex.value).map((item, i) => ({
    data: item,
    index: startIndex.value + i
  }))
})

const defaultItemKey = (item: any, index: number) => index

let rafId: number | null = null
let isScrolling = false

const handleScroll = () => {
  if (rafId) {
    cancelAnimationFrame(rafId)
  }
  
  rafId = requestAnimationFrame(() => {
    if (containerRef.value) {
      scrollTop.value = containerRef.value.scrollTop
    }
    rafId = null
  })
}

onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll, { passive: true })
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll)
  }
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
})

watch(() => props.items, () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
  }
  scrollTop.value = 0
}, { deep: true })
</script>

<style scoped>
.virtual-list {
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

.virtual-list-padding {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
}

.virtual-list-items {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
}

.virtual-list-item {
  box-sizing: border-box;
}
</style>
