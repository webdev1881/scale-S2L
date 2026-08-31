import type {
  DeviceSettings,
  PrintResult,
  Product,
  Status,
  Transaction,
  WeightReading,
} from './types'

/** Ошибка с человекочитаемым текстом из detail — киоск показывает её как подсказку. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    let detail = `Ошибка ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* тело не JSON — оставляем общий текст */
    }
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  products: (params: { search?: string; category?: string; only_active?: boolean } = {}) => {
    const query = new URLSearchParams()
    if (params.search) query.set('search', params.search)
    if (params.category) query.set('category', params.category)
    if (params.only_active === false) query.set('only_active', 'false')
    return request<Product[]>(`/api/products?${query.toString()}`)
  },
  categories: () => request<string[]>('/api/products/categories'),
  createProduct: (payload: Omit<Product, 'id'>) =>
    request<Product>('/api/products', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: Omit<Product, 'id'>) =>
    request<Product>(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProduct: (id: number) => request<void>(`/api/products/${id}`, { method: 'DELETE' }),

  weight: () => request<WeightReading>('/api/scale/weight'),
  tare: () => request<WeightReading>('/api/scale/tare', { method: 'POST' }),
  zero: () => request<WeightReading>('/api/scale/zero', { method: 'POST' }),
  status: () => request<Status>('/api/status'),

  print: (product_id: number, weight_g?: number, copies = 1) =>
    request<PrintResult>('/api/print', {
      method: 'POST',
      body: JSON.stringify({ product_id, weight_g, copies }),
    }),
  transactions: (limit = 100) => request<Transaction[]>(`/api/transactions?limit=${limit}`),

  settings: () => request<DeviceSettings>('/api/settings'),
  saveSettings: (payload: DeviceSettings) =>
    request<DeviceSettings>('/api/settings', { method: 'PUT', body: JSON.stringify(payload) }),

  simWeight: (grams: number) =>
    request<WeightReading>('/api/sim/weight', {
      method: 'POST',
      body: JSON.stringify({ grams }),
    }),
  simPrinter: (payload: { paper_out?: boolean; cover_open?: boolean }) =>
    request<Record<string, unknown>>('/api/sim/printer', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  labelPreviewUrl: '/api/label/preview',
}
