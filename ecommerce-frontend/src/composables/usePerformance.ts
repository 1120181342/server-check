const ENABLE_PERFORMANCE_MONITOR = false

const globalConfig = {
  enabled: false,
  sampleInterval: 2000,
  logToConsole: false,
  measureTimeEnabled: false
}

let globalFPSMonitor: {
  fps: number
  start: () => void
  stop: () => void
} | null = null

let monitorRefCount = 0

function createFPSMonitor() {
  let fps = 60
  let frameCount = 0
  let lastUpdateTime = performance.now()
  let animationId: number | null = null
  let isRunning = false

  const measureFPS = () => {
    if (!isRunning) return
    
    frameCount++
    const now = performance.now()
    
    if (now - lastUpdateTime >= globalConfig.sampleInterval) {
      fps = Math.round((frameCount * 1000) / (now - lastUpdateTime))
      frameCount = 0
      lastUpdateTime = now
      
      if (globalConfig.logToConsole) {
        console.log(`[Performance] FPS: ${fps}`)
      }
    }
    
    animationId = requestAnimationFrame(measureFPS)
  }

  return {
    get fps() { return fps },
    start() {
      if (!isRunning && globalConfig.enabled) {
        isRunning = true
        frameCount = 0
        lastUpdateTime = performance.now()
        measureFPS()
      }
    },
    stop() {
      if (animationId !== null) {
        cancelAnimationFrame(animationId)
        animationId = null
      }
      isRunning = false
    }
  }
}

export function enablePerformanceMonitor(options?: {
  sampleInterval?: number
  logToConsole?: boolean
  measureTimeEnabled?: boolean
}) {
  if (options?.sampleInterval !== undefined) {
    globalConfig.sampleInterval = options.sampleInterval
  }
  if (options?.logToConsole !== undefined) {
    globalConfig.logToConsole = options.logToConsole
  }
  if (options?.measureTimeEnabled !== undefined) {
    globalConfig.measureTimeEnabled = options.measureTimeEnabled
  }
  
  globalConfig.enabled = true
}

export function disablePerformanceMonitor() {
  globalConfig.enabled = false
  if (globalFPSMonitor) {
    globalFPSMonitor.stop()
  }
}

export function usePerformance() {
  const isEnabled = ENABLE_PERFORMANCE_MONITOR && globalConfig.enabled

  const metrics = {
    get fps() {
      return isEnabled && globalFPSMonitor ? globalFPSMonitor.fps : 60
    },
    get memory() {
      if (!isEnabled) return 0
      if ('memory' in performance) {
        return Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024)
      }
      return 0
    },
    get loadTime() {
      return performance.now()
    }
  }

  const startFPSMonitor = () => {
    if (!isEnabled) return
    
    monitorRefCount++
    if (!globalFPSMonitor) {
      globalFPSMonitor = createFPSMonitor()
    }
    globalFPSMonitor.start()
  }

  const stopFPSMonitor = () => {
    if (!isEnabled) return
    
    monitorRefCount--
    if (monitorRefCount <= 0 && globalFPSMonitor) {
      globalFPSMonitor.stop()
      monitorRefCount = 0
    }
  }

  const measureTime = <T>(label: string, fn: () => T): T => {
    if (!isEnabled || !globalConfig.measureTimeEnabled) {
      return fn()
    }
    
    const start = performance.now()
    try {
      return fn()
    } finally {
      const duration = performance.now() - start
      console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`)
    }
  }

  const measureTimeAsync = async <T>(label: string, fn: () => Promise<T>): Promise<T> => {
    if (!isEnabled || !globalConfig.measureTimeEnabled) {
      return fn()
    }
    
    const start = performance.now()
    try {
      return await fn()
    } finally {
      const duration = performance.now() - start
      console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`)
    }
  }

  return {
    metrics,
    isEnabled,
    measureTime,
    measureTimeAsync,
    startFPSMonitor,
    stopFPSMonitor,
    enablePerformanceMonitor,
    disablePerformanceMonitor
  }
}
