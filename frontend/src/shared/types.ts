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
  /** Имя файла в /products; пусто — карточка покажет значок */
  image: string
  active: number
}

export interface Category {
  name: string
  image: string
  count: number
  /** Обложку выбрал оператор, а не подставил первый товар группы. */
  custom_image: boolean
  /** Место группы, заданное перетаскиванием в админке; null — не задано. */
  sort_order: number | null
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

export interface LabelBlock {
  kind:
    | 'store'
    | 'name'
    | 'weight'
    | 'price'
    | 'total'
    | 'barcode'
    | 'packed'
    | 'best_before'
    | 'composition'
    | 'thanks'
    | 'text'
    | 'line'
  /** Левый верхний угол и размеры в миллиметрах; нулевая ширина — до правого края. */
  x: number
  y: number
  width: number
  height: number
  /** Кегль в точках растра принтера. */
  size: number
  bold: boolean
  align: 'left' | 'center' | 'right'
  caption: boolean
  /** Подпись в одной строке со значением, а не над ним. */
  caption_inline: boolean
  lines: number
  box: boolean
  text: string
  visible: boolean
}

export interface LabelLayout {
  blocks: LabelBlock[]
}

export interface PurgeResult {
  products: number
  transactions: number
  photos: number
  labels: number
}

/** Даты последних обновлений прибора — их всегда показывает шапка админки. */
export interface UpdatedAt {
  catalog_at: string | null
  catalog_products: number | null
  settings_at: string | null
  build_at: string | null
  build_sha: string | null
}

export interface DeviceSettings {
  language: 'uk' | 'ru'
  theme: 'dark' | 'light'
  store_name: string
  currency: string
  label_width_mm: number
  label_height_mm: number
  label_layout: LabelLayout
  barcode_template: string
  barcode_value: 'weight' | 'total'
  min_print_weight_g: number
  require_stable: boolean
  kiosk_scale_buttons: boolean
  kiosk_use_groups: boolean
  kiosk_show_code: boolean
  kiosk_show_unit: boolean
  kiosk_code_button: boolean
  kiosk_header_on_contact: boolean
  kiosk_only_with_photo: boolean
  kiosk_photo_first: boolean
  kiosk_search_button: boolean
  kiosk_back_button: boolean
  kiosk_search_width: number
  kiosk_actions_full_width: boolean
  kiosk_keyboard_width: number
  kiosk_keyboard_height: number
  kiosk_keyboard_font: 'system' | 'arial' | 'dejavu' | 'ubuntu' | 'mono' | 'serif'
  kiosk_keyboard_font_size: number
  kiosk_keyboard_bold: boolean
  kiosk_peek_percent: number
  kiosk_idle_reset_s: number
  kiosk_clear_hold_s: number
  kiosk_unselect_s: number
  kiosk_after_print: 'home' | 'catalog' | 'search'
  kiosk_piece_needs_load: boolean
  kiosk_label_max_s: number
  splash_seconds: number
  kiosk_force_updating: boolean
  kiosk_updating_photo_scale: number
  kiosk_updating_text_position: number
  kiosk_toast_font_size: number
  kiosk_toast_duration_s: number
  kiosk_toast_color: string
  kiosk_toast_pulse: boolean
  ui_scale_weight: number
  ui_scale_group_title: number
  ui_scale_product_name: number
  ui_scale_product_price: number
  ui_scale_product_code: number
  ui_scale_footer: number
  ui_photo_group: number
  ui_photo_product: number
  ui_photo_scale: number
  ui_photo_scale_group: number
  ui_plate_height: number
  ui_primary_color: string
  ui_secondary_color: string
  grid_cols: number
  grid_rows: number
  product_grid_cols: number
  product_grid_rows: number
}
