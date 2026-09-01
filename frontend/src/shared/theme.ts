export const THEMES = ['dark', 'light'] as const
export type Theme = (typeof THEMES)[number]

export const DEFAULT_THEME: Theme = 'dark'

const STORAGE_KEY = 's2l-theme'

export function isTheme(value: string): value is Theme {
  return (THEMES as readonly string[]).includes(value)
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
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* приватный режим или запрет на хранилище — не повод падать */
  }
  return theme
}

/**
 * Тема прошлого запуска. Нужна ровно для одного: применить её до того, как
 * придут настройки с сервера, иначе заставка успевает мигнуть чужим фоном.
 */
export function storedTheme(): Theme {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && isTheme(saved)) return saved
  } catch {
    /* см. выше */
  }
  return DEFAULT_THEME
}
