/**
 * Настройки, нужные киоску до того, как ответит сервер: тема и длительность
 * заставки. И то и другое влияет на самый первый кадр, а настройки приезжают
 * запросом, поэтому запоминаем последние известные значения в localStorage —
 * иначе экран успевает мигнуть чужим фоном или показать заставку не той длины.
 */
export const THEMES = ['dark', 'light'] as const
export type Theme = (typeof THEMES)[number]

export const DEFAULT_THEME: Theme = 'light'
export const DEFAULT_SPLASH_MS = 3000

const THEME_KEY = 's2l-theme'
const SPLASH_KEY = 's2l-splash-ms'

export function isTheme(value: string): value is Theme {
  return (THEMES as readonly string[]).includes(value)
}

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    // приватный режим или запрет на хранилище — не повод падать
    return null
  }
}

function write(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* см. выше */
  }
}

/**
 * Тема применяется к <html>: data-theme переключает наши токены, класс dark —
 * переменные Element Plus, иначе диалоги и всплывающие сообщения останутся белыми.
 */
export function applyTheme(value: string): Theme {
  const theme: Theme = isTheme(value) ? value : DEFAULT_THEME
  const root = document.documentElement
  root.dataset.theme = theme
  root.classList.toggle('dark', theme === 'dark')
  write(THEME_KEY, theme)
  return theme
}

export function storedTheme(): Theme {
  const saved = read(THEME_KEY)
  return saved && isTheme(saved) ? saved : DEFAULT_THEME
}

export function storedSplashMs(): number {
  const saved = Number(read(SPLASH_KEY))
  return Number.isFinite(saved) && saved >= 0 ? saved : DEFAULT_SPLASH_MS
}

export function rememberSplash(seconds: number | undefined | null): number {
  // Значение может не прийти вовсе — например, бэкенд старее фронта и поля ещё
  // не знает. Без этой проверки в хранилище уезжает NaN, а киоск остаётся
  // без заставки: NaN > 0 ложно.
  const ms = Number.isFinite(seconds) ? Math.max(0, Math.round(Number(seconds) * 1000)) : DEFAULT_SPLASH_MS
  write(SPLASH_KEY, String(ms))
  return ms
}
