export type Unit = 'weight' | 'piece'

export interface Product {
  id: number
  plu: number
  name: string
  unit: Unit
  price: number
  category: string
  tare_g: number
  shelf_life_days: number
  composition: string
  emoji: string
  active: number
}

export interface WeightReading {
  gross_g: number
  net_g: number
  tare_g: number
  stable: boolean
  error: string | null
}

export interface DeviceStatus {
  online: boolean
  kind: string
  detail: Record<string, unknown>
}

export interface Status {
  backend: string
  scale: DeviceStatus
  printer: DeviceStatus
}

export interface PrintResult {
  transaction_id: number
  barcode: string
  weight_g: number
  total: number
  label_url: string | null
}

export interface Transaction {
  id: number
  created_at: string
  product_id: number
  product_name: string
  weight_g: number
  price: number
  total: number
  barcode: string
  label_file: string
}

export interface DeviceSettings {
  language: 'uk' | 'ru'
  store_name: string
  currency: string
  label_width_mm: number
  label_height_mm: number
  barcode_template: string
  barcode_value: 'weight' | 'total'
  min_print_weight_g: number
  require_stable: boolean
  kiosk_idle_reset_s: number
}
