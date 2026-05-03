const __DEV__ = import.meta.env.DEV

export function perfTime(label: string): void {
  if (__DEV__) {
    console.time(label)
  }
}

export function perfTimeEnd(label: string): void {
  if (__DEV__) {
    console.timeEnd(label)
  }
}

export function perfMeasure<T>(label: string, fn: () => T): T {
  if (!__DEV__) {
    return fn()
  }
  console.time(label)
  try {
    return fn()
  } finally {
    console.timeEnd(label)
  }
}

export async function perfMeasureAsync<T>(label: string, fn: () => Promise<T>): Promise<T> {
  if (!__DEV__) {
    return fn()
  }
  console.time(label)
  try {
    return await fn()
  } finally {
    console.timeEnd(label)
  }
}

export function perfLog(...args: any[]): void {
  if (__DEV__) {
    console.log(...args)
  }
}

export function perfWarn(...args: any[]): void {
  if (__DEV__) {
    console.warn(...args)
  }
}

export function perfError(...args: any[]): void {
  if (__DEV__) {
    console.error(...args)
  }
}
