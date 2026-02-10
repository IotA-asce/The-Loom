// API Client for The Loom UI
// Provides request/response interceptors, caching, retry logic, and circuit breaker

// ==================== TYPES ====================

export interface RequestConfig extends RequestInit {
  /** Request URL (used internally) */
  url?: string
  /** Custom timeout in milliseconds */
  timeout?: number
  /** Whether to skip the cache for this request */
  skipCache?: boolean
  /** Whether to deduplicate this request */
  deduplicate?: boolean
  /** Number of retry attempts (overrides default) */
  retries?: number
  /** Custom cache TTL in milliseconds */
  cacheTtl?: number
  /** Additional metadata for interceptors */
  meta?: Record<string, unknown>
}

export interface ApiResponse<T = unknown> {
  data: T
  status: number
  statusText: string
  headers: Headers
  config: RequestConfig
  cached?: boolean
  fromCache?: boolean
}

export interface CacheEntry<T = unknown> {
  data: T
  timestamp: number
  ttl: number
  key: string
}

export interface Interceptor {
  onRequest?: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>
  onRequestError?: (error: Error) => Error | Promise<Error>
  onResponse?: <T>(response: ApiResponse<T>) => ApiResponse<T> | Promise<ApiResponse<T>>
  onResponseError?: (error: ApiError) => ApiError | Promise<ApiError>
}

// ==================== CIRCUIT BREAKER ====================

type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN'

interface CircuitBreakerConfig {
  failureThreshold: number
  resetTimeout: number
  halfOpenMaxCalls: number
}

class CircuitBreaker {
  private state: CircuitState = 'CLOSED'
  private failureCount = 0
  private successCount = 0
  private nextAttempt = 0
  private halfOpenCalls = 0

  constructor(private config: CircuitBreakerConfig) {}

  canExecute(): boolean {
    if (this.state === 'CLOSED') return true

    if (this.state === 'OPEN') {
      if (Date.now() >= this.nextAttempt) {
        this.state = 'HALF_OPEN'
        this.halfOpenCalls = 0
        this.successCount = 0
        return true
      }
      return false
    }

    // HALF_OPEN state
    if (this.halfOpenCalls < this.config.halfOpenMaxCalls) {
      this.halfOpenCalls++
      return true
    }
    return false
  }

  recordSuccess(): void {
    this.failureCount = 0

    if (this.state === 'HALF_OPEN') {
      this.successCount++
      if (this.successCount >= this.config.halfOpenMaxCalls) {
        this.state = 'CLOSED'
        this.halfOpenCalls = 0
        this.successCount = 0
      }
    }
  }

  recordFailure(): void {
    this.failureCount++

    if (this.state === 'HALF_OPEN') {
      this.state = 'OPEN'
      this.nextAttempt = Date.now() + this.config.resetTimeout
      this.halfOpenCalls = 0
      this.successCount = 0
      return
    }

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = 'OPEN'
      this.nextAttempt = Date.now() + this.config.resetTimeout
    }
  }

  getState(): CircuitState {
    return this.state
  }
}

// ==================== CACHE MANAGER ====================

class CacheManager {
  private cache = new Map<string, CacheEntry>()

  get<T>(key: string): CacheEntry<T> | undefined {
    const entry = this.cache.get(key)
    if (!entry) return undefined

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return undefined
    }

    return entry as CacheEntry<T>
  }

  set<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
      key,
    })
  }

  invalidate(key: string): boolean {
    return this.cache.delete(key)
  }

  invalidatePattern(pattern: RegExp): number {
    let count = 0
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        this.cache.delete(key)
        count++
      }
    }
    return count
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }

  // Clean up expired entries periodically
  cleanup(): number {
    let count = 0
    const now = Date.now()
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key)
        count++
      }
    }
    return count
  }
}

// ==================== ERROR HANDLING ====================

export class ApiError extends Error {
  readonly status: number
  readonly statusText: string
  readonly url: string
  readonly config: RequestConfig
  readonly data?: unknown
  readonly isRetryable: boolean

  constructor(
    message: string,
    status: number,
    statusText: string,
    url: string,
    config: RequestConfig,
    data?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.statusText = statusText
    this.url = url
    this.config = config
    this.data = data
    // 5xx errors and network errors are retryable
    this.isRetryable = status >= 500 || status === 0
  }
}

// ==================== API CLIENT ====================

interface ApiClientConfig {
  baseUrl: string
  defaultTimeout: number
  defaultRetries: number
  defaultCacheTtl: number
  retryDelay: number
  circuitBreaker: CircuitBreakerConfig
}

const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: '/api',
  defaultTimeout: 30000,
  defaultRetries: 3,
  defaultCacheTtl: 5 * 60 * 1000, // 5 minutes
  retryDelay: 1000,
  circuitBreaker: {
    failureThreshold: 5,
    resetTimeout: 30000,
    halfOpenMaxCalls: 3,
  },
}

class ApiClient {
  private config: ApiClientConfig
  private interceptors: Interceptor[] = []
  private cache: CacheManager
  private circuitBreaker: CircuitBreaker
  private inFlightRequests = new Map<string, Promise<unknown>>()

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.cache = new CacheManager()
    this.circuitBreaker = new CircuitBreaker(this.config.circuitBreaker)

    // Set up periodic cache cleanup
    setInterval(() => this.cache.cleanup(), 60000)
  }

  // ==================== INTERCEPTORS ====================

  addInterceptor(interceptor: Interceptor): () => void {
    this.interceptors.push(interceptor)
    return () => {
      const index = this.interceptors.indexOf(interceptor)
      if (index > -1) {
        this.interceptors.splice(index, 1)
      }
    }
  }

  private async applyRequestInterceptors(config: RequestConfig): Promise<RequestConfig> {
    let currentConfig = config
    for (const interceptor of this.interceptors) {
      if (interceptor.onRequest) {
        currentConfig = await interceptor.onRequest(currentConfig)
      }
    }
    return currentConfig
  }

  private async applyResponseInterceptors<T>(response: ApiResponse<T>): Promise<ApiResponse<T>> {
    let currentResponse = response
    for (const interceptor of this.interceptors) {
      if (interceptor.onResponse) {
        currentResponse = await interceptor.onResponse(currentResponse)
      }
    }
    return currentResponse
  }

  private async applyResponseErrorInterceptors(error: ApiError): Promise<ApiError> {
    let currentError = error
    for (const interceptor of this.interceptors) {
      if (interceptor.onResponseError) {
        currentError = await interceptor.onResponseError(currentError)
      }
    }
    return currentError
  }

  // ==================== REQUEST DEDUPLICATION ====================

  private getRequestKey(url: string, config: RequestConfig): string {
    const method = config.method || 'GET'
    const body = config.body ? JSON.stringify(config.body) : ''
    return `${method}:${url}:${body}`
  }

  private deduplicateRequest<T>(key: string, request: () => Promise<T>): Promise<T> {
    const existing = this.inFlightRequests.get(key)
    if (existing) {
      return existing as Promise<T>
    }

    const promise = request().finally(() => {
      this.inFlightRequests.delete(key)
    })

    this.inFlightRequests.set(key, promise)
    return promise
  }

  // ==================== CORE REQUEST METHOD ====================

  private async executeRequest<T>(url: string, config: RequestConfig): Promise<ApiResponse<T>> {
    const fullUrl = url.startsWith('http') ? url : `${this.config.baseUrl}${url}`
    const cacheKey = this.getRequestKey(fullUrl, config)

    // Check cache for GET requests
    if (config.method === undefined || config.method === 'GET') {
      if (!config.skipCache) {
        const cached = this.cache.get<T>(cacheKey)
        if (cached) {
          return {
            data: cached.data,
            status: 200,
            statusText: 'OK (from cache)',
            headers: new Headers(),
            config,
            cached: true,
            fromCache: true,
          }
        }
      }
    }

    // Check circuit breaker
    if (!this.circuitBreaker.canExecute()) {
      throw new ApiError(
        'Circuit breaker is open - service temporarily unavailable',
        503,
        'Service Unavailable',
        fullUrl,
        config
      )
    }

    // Apply request interceptors
    const processedConfig = await this.applyRequestInterceptors(config)

    // Set up timeout
    const timeout = processedConfig.timeout || this.config.defaultTimeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const fetchConfig: RequestInit = {
        ...processedConfig,
        signal: controller.signal,
      }

      const response = await fetch(fullUrl, fetchConfig)
      clearTimeout(timeoutId)

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await this.parseErrorResponse(response)
        throw new ApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response.statusText,
          fullUrl,
          processedConfig,
          errorData
        )
      }

      // Parse response data
      const data = await this.parseResponse<T>(response)

      // Record success for circuit breaker
      this.circuitBreaker.recordSuccess()

      const apiResponse: ApiResponse<T> = {
        data,
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        config: processedConfig,
        cached: false,
        fromCache: false,
      }

      // Cache successful GET responses
      if (config.method === undefined || config.method === 'GET') {
        const ttl = config.cacheTtl || this.config.defaultCacheTtl
        this.cache.set(cacheKey, data, ttl)
      }

      return this.applyResponseInterceptors(apiResponse)
    } catch (error) {
      clearTimeout(timeoutId)

      // Record failure for circuit breaker (only for network errors and 5xx)
      if (error instanceof ApiError && error.isRetryable) {
        this.circuitBreaker.recordFailure()
      }

      if (error instanceof ApiError) {
        throw await this.applyResponseErrorInterceptors(error)
      }

      // Handle network errors and timeouts
      const isTimeout = error instanceof Error && error.name === 'AbortError'
      const networkError = new ApiError(
        isTimeout ? 'Request timeout' : (error as Error).message || 'Network error',
        isTimeout ? 408 : 0,
        isTimeout ? 'Request Timeout' : 'Network Error',
        fullUrl,
        processedConfig
      )

      // Record network failures for circuit breaker
      this.circuitBreaker.recordFailure()

      throw await this.applyResponseErrorInterceptors(networkError)
    }
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type') || ''

    if (contentType.includes('application/json')) {
      return response.json() as Promise<T>
    }

    if (contentType.includes('text/')) {
      return response.text() as Promise<T>
    }

    // For binary data, return blob
    if (contentType.includes('application/octet-stream') ||
        contentType.includes('image/') ||
        contentType.includes('audio/') ||
        contentType.includes('video/')) {
      return response.blob() as Promise<T>
    }

    // Default to text
    return response.text() as Promise<T>
  }

  private async parseErrorResponse(response: Response): Promise<{ message?: string }> {
    try {
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        return await response.json()
      }
      const text = await response.text()
      return { message: text }
    } catch {
      return {}
    }
  }

  // ==================== RETRY LOGIC ====================

  private async requestWithRetry<T>(url: string, config: RequestConfig): Promise<ApiResponse<T>> {
    const maxRetries = config.retries ?? this.config.defaultRetries
    let lastError: ApiError | undefined

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.executeRequest<T>(url, config)
      } catch (error) {
        lastError = error as ApiError

        // Don't retry if it's not a retryable error
        if (!lastError.isRetryable) {
          throw lastError
        }

        // Don't retry on the last attempt
        if (attempt === maxRetries) {
          break
        }

        // Calculate exponential backoff delay
        const delay = this.config.retryDelay * Math.pow(2, attempt)
        await this.sleep(delay)
      }
    }

    throw lastError!
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // ==================== PUBLIC API METHODS ====================

  async request<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    // Apply deduplication if enabled (default for GET requests)
    const shouldDeduplicate = config.deduplicate ?? (config.method === undefined || config.method === 'GET')

    if (shouldDeduplicate) {
      const key = this.getRequestKey(url, config)
      return this.deduplicateRequest(key, () => this.requestWithRetry<T>(url, config))
    }

    return this.requestWithRetry<T>(url, config)
  }

  async get<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, { ...config, method: 'GET' })
  }

  async post<T>(url: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...config,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(url: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...config,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async patch<T>(url: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...config,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, { ...config, method: 'DELETE' })
  }

  // Form data upload
  async upload<T>(url: string, formData: FormData, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...config,
      method: 'POST',
      body: formData,
    })
  }

  // ==================== CONFIGURATION ====================

  setBaseUrl(baseUrl: string): void {
    this.config.baseUrl = baseUrl
  }

  setDefaultTimeout(timeout: number): void {
    this.config.defaultTimeout = timeout
  }

  setDefaultRetries(retries: number): void {
    this.config.defaultRetries = retries
  }

  // ==================== CACHE ACCESS ====================

  getCache(): CacheManager {
    return this.cache
  }

  // ==================== CIRCUIT BREAKER STATUS ====================

  getCircuitBreakerState(): CircuitState {
    return this.circuitBreaker.getState()
  }

  // ==================== DEBUGGING ====================

  getInFlightRequests(): number {
    return this.inFlightRequests.size
  }

  getCacheSize(): number {
    return this.cache.size()
  }
}

// ==================== EXPORTED INSTANCES ====================

export const apiClient = new ApiClient({
  baseUrl: '/api',
})

// Export cache utilities
export const cache = {
  get: <T>(key: string): CacheEntry<T> | undefined => apiClient.getCache().get<T>(key),
  set: <T>(key: string, data: T, ttl?: number): void => {
    const defaultTtl = 5 * 60 * 1000 // 5 minutes
    apiClient.getCache().set(key, data, ttl ?? defaultTtl)
  },
  invalidate: (key: string): boolean => apiClient.getCache().invalidate(key),
  invalidatePattern: (pattern: RegExp): number => apiClient.getCache().invalidatePattern(pattern),
  clear: (): void => apiClient.getCache().clear(),
  size: (): number => apiClient.getCache().size(),
}

// ==================== UTILITY INTERCEPTORS ====================

export const loggingInterceptor: Interceptor = {
  onRequest: (config) => {
    const url = config.url || '[unknown]'
    console.log(`[API] ${config.method || 'GET'} ${url}`)
    return config
  },
  onResponse: (response) => {
    console.log(`[API] Response: ${response.status} ${response.statusText}`)
    return response
  },
  onResponseError: (error) => {
    console.error(`[API] Error: ${error.status} ${error.message}`)
    return error
  },
}

export const authInterceptor = (getToken: () => string | null): Interceptor => ({
  onRequest: (config) => {
    const token = getToken()
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }
    return config
  },
})

export default apiClient
