export function formatKg(grams: number): string {
  return (grams / 1000).toFixed(3)
}

export function formatMoney(value: number): string {
  return value.toFixed(2)
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
