/**
 * Шрифты, которые оператор может выбрать для экранной клавиатуры.
 *
 * Список короткий и с запасными вариантами в каждой строке: на приборе стоит
 * Ubuntu без Segoe UI, на машине разработчика — Windows без Ubuntu, и один
 * ключ должен давать похожий результат и там и там. Ключ хранится в настройках,
 * стек — здесь, чтобы не тащить CSS в JSON прибора.
 */
export const KIOSK_FONTS = {
  system: "'Segoe UI', Ubuntu, Roboto, 'Helvetica Neue', Arial, sans-serif",
  arial: "Arial, 'Liberation Sans', Helvetica, sans-serif",
  dejavu: "'DejaVu Sans', Verdana, Geneva, sans-serif",
  ubuntu: "Ubuntu, 'Noto Sans', 'Segoe UI', sans-serif",
  mono: "'DejaVu Sans Mono', Consolas, 'Liberation Mono', monospace",
  serif: "Georgia, 'DejaVu Serif', 'Times New Roman', serif",
} as const

export type KioskFont = keyof typeof KIOSK_FONTS

export const KIOSK_FONT_KEYS = Object.keys(KIOSK_FONTS) as KioskFont[]
