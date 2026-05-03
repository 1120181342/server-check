import { ref, onMounted, onUnmounted } from 'vue'

export function usePerformance() {
  const isDev = ref(import.meta.env.DEV)
  const metrics = ref({
    fps: 60,
    memory: 0,
    loadTime: 0
  })

  let frameCount = 0
  let lastTime = performance.now()
  let animationId: number | null = null

  const startFPSMonitor = () => {
    if (!isDev.value) return

    const measureFPS = () => {
      frameCount++
      const now = performance.now()
      
      if (now >= lastTime + 1000) {
        metrics.value.fps = Math.round((frameCount * 1000) / (now - lastTime))
        frameCount = 0
        lastTime = now
      }
      
      animationId = requestAnimationFrame(measureFPS)
    }
    
    animationId = requestAnimationFrame(measureFPS)
  }

  const stopFPSMonitor = () => {
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
  }

  const measureTime = (label: string, fn: () => void) => {
    console.time(label)
    const result = fn()
    console.timeEnd(label)
    return result
  }

  const measureTimeAsync = async (label: string, fn: () => Promise<any>) => {
    console.time(label)
    const result = await fn()
    console.timeEnd(label)
    return result
  }

  const getMemoryUsage = () => {
    if ('memory' in performance) {
      const mem = (performance as any).memory
      metrics.value.memory = Math.round(mem.usedJSHeapSize / 1024 / 1024)
    }
    return metrics.value.memory
  }

  onMounted(() => {
    if (isDev.value) {
      metrics.value.loadTime = performance.now()
      startFPSMonitor()
      
      console.log('%c[Performance Monitor] Started', 'color: #4CAF50; font-weight: bold;')
    }
  })

  onUnmounted(() => {
    stopFPSMonitor()
  })

  return {
    metrics,
    isDev,
    measureTime,
    measureTimeAsync,
    getMemoryUsage,
    startFPSMonitor,
    stopFPSMonitor
  }
}

export function createCache<T>(maxSize: number = 100) {
  const cache = new Map<string, { value: T; timestamp: number }>()
  const maxAge = 5 * 60 * 1000

  return {
    get(key: string): T | undefined {
      const item = cache.get(key)
      if (!item) return undefined
      
      if (Date.now() - item.timestamp > maxAge) {
        cache.delete(key)
        return undefined
      }
      
      return item.value
    },
    
    set(key: string, value: T): void {
      if (cache.size >= maxSize) {
        const firstKey = cache.keys().next().value
        if (firstKey !== undefined) {
          cache.delete(firstKey)
        }
      }
      
      cache.set(key, {
        value,
        timestamp: Date.now()
      })
    },
    
    has(key: string): boolean {
      return this.get(key) !== undefined
    },
    
    delete(key: string): boolean {
      return cache.delete(key)
    },
    
    clear(): void {
      cache.clear()
    },
    
    size(): number {
      return cache.size
    }
  }
}
