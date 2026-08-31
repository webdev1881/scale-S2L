import { i18n } from './i18n'

export function formatKg(grams: number): string {
  return (grams / 1000).toFixed(3)
}

export function formatMoney(value: number): string {
  return value.toFixed(2)
}

/** BCP-47 тег для Intl по текущему языку интерфейса. */
export function localeTag(): string {
  return i18n.global.locale.value === 'ru' ? 'ru-RU' : 'uk-UA'
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleString(localeTag(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
