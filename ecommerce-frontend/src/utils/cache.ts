interface CacheItem<T> {
  value: T
  timestamp: number
}

export function createCache<T>(maxSize: number = 100, maxAge: number = 5 * 60 * 1000) {
  const cache = new Map<string, CacheItem<T>>()

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
      const item = cache.get(key)
      if (!item) return false
      
      if (Date.now() - item.timestamp > maxAge) {
        cache.delete(key)
        return false
      }
      
      return true
    },
    
    delete(key: string): boolean {
      return cache.delete(key)
    },
    
    clear(): void {
      cache.clear()
    },
    
    size(): number {
      return cache.size
    },
    
    keys(): IterableIterator<string> {
      return cache.keys()
    }
  }
}

const productCache = createCache<any>(50, 10 * 60 * 1000)
const searchCache = createCache<any>(30, 5 * 60 * 1000)

export { productCache, searchCache }
