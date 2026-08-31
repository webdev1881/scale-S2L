import elementRu from 'element-plus/es/locale/lang/ru'
import elementUk from 'element-plus/es/locale/lang/uk'
import { createI18n } from 'vue-i18n'

export const SUPPORTED_LOCALES = ['uk', 'ru'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export const LOCALE_NAMES: Record<Locale, string> = {
  uk: 'Українська',
  ru: 'Русский',
}

const messages = {
  uk: {
    title: {
      kiosk: 'Aurora S2L — самообслуговування',
      admin: 'Aurora S2L — адміністрування',
    },
    kiosk: {
      connected: 'Ваги підключено',
      disconnected: 'Немає зв’язку',
      searchPlaceholder: 'Пошук товару або PLU',
      allCategories: 'Усі',
      nothingFound: 'Нічого не знайдено',
      noProduct: 'Товар не обрано',
      total: 'До сплати',
      print: 'Надрукувати етикетку',
      printing: 'Друк…',
      takeLabel: 'Заберіть етикетку',
      sentToPrinter: 'Етикетку надіслано на принтер',
      done: 'Готово',
      pluNotFound: 'Товар з PLU {plu} не знайдено',
      printFailed: 'Помилка друку',
      perKg: 'кг',
      perPiece: 'шт',
      tare: 'тара',
    },
    weight: {
      tare: 'Тара',
      zero: 'Нуль',
      tareValue: 'Тара: {value} кг',
      putGoods: 'Покладіть товар на платформу',
      weighing: 'Зважування…',
      stable: 'Вага стабільна',
    },
    numpad: {
      find: 'Знайти за PLU',
    },
    blocked: {
      selectProduct: 'Оберіть товар',
      putGoods: 'Покладіть товар на платформу',
      waitStable: 'Дочекайтеся стабілізації',
    },
    errors: {
      scale_no_link: 'Немає зв’язку з вагами',
      scale_overload: 'Перевантаження',
      print_paper_out: 'Закінчився папір',
      print_cover_open: 'Відкрита кришка принтера',
      print_unavailable: 'Принтер недоступний',
      print_not_stable: 'Вага не стабілізувалася — зачекайте',
      print_no_goods: 'Покладіть товар на платформу',
      print_scale_error: 'Помилка ваг',
      unknown: 'Невідома помилка',
    },
    admin: {
      nav: {
        products: 'Товари',
        transactions: 'Журнал',
        simulator: 'Симулятор',
        settings: 'Налаштування',
      },
      status: {
        scaleOnline: 'Ваги: на зв’язку',
        scaleOffline: 'Ваги: немає зв’язку',
        printerOnline: 'Принтер: готовий',
        printerOffline: 'Принтер: помилка',
        openKiosk: 'Відкрити кіоск →',
      },
      products: {
        search: 'Пошук за назвою або PLU',
        add: 'Додати товар',
        name: 'Назва',
        category: 'Категорія',
        unit: 'Од.',
        price: 'Ціна',
        tare: 'Тара, г',
        shelfLife: 'Термін, дн',
        hidden: 'прихований',
        edit: 'Змінити',
        hide: 'Приховати',
        newTitle: 'Новий товар',
        editTitle: 'Зміна товару',
        unitWeight: 'Ваговий',
        unitPiece: 'Штучний',
        pricePerKg: 'Ціна за кг',
        pricePerPiece: 'Ціна за шт',
        emoji: 'Значок',
        composition: 'Склад',
        showInKiosk: 'Показувати в кіоску',
        cancel: 'Скасувати',
        save: 'Зберегти',
        created: 'Товар додано',
        updated: 'Товар збережено',
        removed: 'Товар прихований',
        saveFailed: 'Не вдалося зберегти',
        confirmHide: 'Приховати «{name}» з каталогу? Журнал операцій збережеться.',
        confirmTitle: 'Видалення товару',
        pluRule: 'PLU від 1 до 99999',
        nameRule: 'Вкажіть назву',
        priceRule: 'Ціна не може бути від’ємною',
      },
      transactions: {
        summary: 'Операцій: {count} · на суму {total}',
        refresh: 'Оновити',
        time: 'Час',
        product: 'Товар',
        mass: 'Маса',
        price: 'Ціна',
        total: 'Сума',
        barcode: 'Штрихкод',
        label: 'Етикетка',
        open: 'відкрити',
      },
      simulator: {
        realTitle: 'Підключено реальне обладнання',
        realText: 'Симулятор вимкнено: вага надходить із вагової плати, друк іде на принтер.',
        platform: 'Платформа ваг',
        stable: 'стабільна',
        unstable: 'коливається',
        printer: 'Принтер',
        paperOut: 'Закінчився папір',
        coverOpen: 'Відкрита кришка',
        printerHint:
          'Увімкніть відмову та спробуйте надрукувати етикетку в кіоску — так перевіряється, що інтерфейс переживає збій друку.',
        preview: 'Попередній перегляд етикетки',
        render: 'Відмалювати',
        product: 'Товар',
        tare: 'Тара',
        zero: 'Скидання в нуль',
        unavailable: 'Симулятор недоступний на реальному обладнанні',
      },
      settings: {
        device: 'Пристрій',
        language: 'Мова інтерфейсу',
        languageHint: 'Впливає на кіоск, адмінку та надруковану етикетку.',
        storeName: 'Назва магазину',
        currency: 'Валюта',
        labelSize: 'Розмір етикетки, мм',
        barcode: 'Штрихкод',
        template: 'Шаблон EAN-13',
        templateHint:
          'P — цифра PLU, W — цифра значення, решта символів копіюється як є. Наприклад {example}: префікс 22, п’ять цифр PLU, п’ять цифр значення.',
        encode: 'Що кодувати',
        encodeWeight: 'Маса, г',
        encodeTotal: 'Сума, коп',
        encodeHint: 'Залежить від того, як налаштовані каси в торговельній мережі.',
        kiosk: 'Поведінка кіоску',
        minWeight: 'Мінімальна маса, г',
        minWeightHint: 'Нижче цього значення друк не дозволяється.',
        requireStable: 'Друкувати лише за стабільною вагою',
        requireStableHint:
          'Вимикати лише для налагодження: етикетка з «тремтячою» вагою бреше покупцеві.',
        idleReset: 'Скидання екрана, с',
        save: 'Зберегти',
        reset: 'Скасувати зміни',
        saved: 'Налаштування збережено',
        saveFailed: 'Не вдалося зберегти',
      },
    },
  },

  ru: {
    title: {
      kiosk: 'Aurora S2L — самообслуживание',
      admin: 'Aurora S2L — администрирование',
    },
    kiosk: {
      connected: 'Весы подключены',
      disconnected: 'Нет связи',
      searchPlaceholder: 'Поиск товара или PLU',
      allCategories: 'Все',
      nothingFound: 'Ничего не найдено',
      noProduct: 'Товар не выбран',
      total: 'К оплате',
      print: 'Напечатать этикетку',
      printing: 'Печать…',
      takeLabel: 'Заберите этикетку',
      sentToPrinter: 'Этикетка отправлена на принтер',
      done: 'Готово',
      pluNotFound: 'Товар с PLU {plu} не найден',
      printFailed: 'Ошибка печати',
      perKg: 'кг',
      perPiece: 'шт',
      tare: 'тара',
    },
    weight: {
      tare: 'Тара',
      zero: 'Ноль',
      tareValue: 'Тара: {value} кг',
      putGoods: 'Положите товар на платформу',
      weighing: 'Взвешивание…',
      stable: 'Вес стабилен',
    },
    numpad: {
      find: 'Найти по PLU',
    },
    blocked: {
      selectProduct: 'Выберите товар',
      putGoods: 'Положите товар на платформу',
      waitStable: 'Дождитесь стабилизации',
    },
    errors: {
      scale_no_link: 'Нет связи с весами',
      scale_overload: 'Перегрузка',
      print_paper_out: 'Закончилась бумага',
      print_cover_open: 'Открыта крышка принтера',
      print_unavailable: 'Принтер недоступен',
      print_not_stable: 'Вес не стабилизировался — подождите',
      print_no_goods: 'Положите товар на платформу',
      print_scale_error: 'Ошибка весов',
      unknown: 'Неизвестная ошибка',
    },
    admin: {
      nav: {
        products: 'Товары',
        transactions: 'Журнал',
        simulator: 'Симулятор',
        settings: 'Настройки',
      },
      status: {
        scaleOnline: 'Весы: на связи',
        scaleOffline: 'Весы: нет связи',
        printerOnline: 'Принтер: готов',
        printerOffline: 'Принтер: ошибка',
        openKiosk: 'Открыть киоск →',
      },
      products: {
        search: 'Поиск по названию или PLU',
        add: 'Добавить товар',
        name: 'Название',
        category: 'Категория',
        unit: 'Ед.',
        price: 'Цена',
        tare: 'Тара, г',
        shelfLife: 'Срок, дн',
        hidden: 'скрыт',
        edit: 'Изменить',
        hide: 'Скрыть',
        newTitle: 'Новый товар',
        editTitle: 'Изменение товара',
        unitWeight: 'Весовой',
        unitPiece: 'Штучный',
        pricePerKg: 'Цена за кг',
        pricePerPiece: 'Цена за шт',
        emoji: 'Значок',
        composition: 'Состав',
        showInKiosk: 'Показывать в киоске',
        cancel: 'Отмена',
        save: 'Сохранить',
        created: 'Товар добавлен',
        updated: 'Товар сохранён',
        removed: 'Товар скрыт',
        saveFailed: 'Не удалось сохранить',
        confirmHide: 'Скрыть «{name}» из каталога? Журнал операций сохранится.',
        confirmTitle: 'Удаление товара',
        pluRule: 'PLU от 1 до 99999',
        nameRule: 'Укажите название',
        priceRule: 'Цена не может быть отрицательной',
      },
      transactions: {
        summary: 'Операций: {count} · на сумму {total}',
        refresh: 'Обновить',
        time: 'Время',
        product: 'Товар',
        mass: 'Масса',
        price: 'Цена',
        total: 'Сумма',
        barcode: 'Штрихкод',
        label: 'Этикетка',
        open: 'открыть',
      },
      simulator: {
        realTitle: 'Подключено реальное железо',
        realText: 'Симулятор отключён: вес приходит с весовой платы, печать идёт на принтер.',
        platform: 'Платформа весов',
        stable: 'стабилен',
        unstable: 'колеблется',
        printer: 'Принтер',
        paperOut: 'Закончилась бумага',
        coverOpen: 'Открыта крышка',
        printerHint:
          'Включите отказ и попробуйте напечатать этикетку в киоске — так проверяется, что интерфейс переживает сбой печати.',
        preview: 'Предпросмотр этикетки',
        render: 'Отрисовать',
        product: 'Товар',
        tare: 'Тара',
        zero: 'Сброс в ноль',
        unavailable: 'Симулятор недоступен на реальном железе',
      },
      settings: {
        device: 'Устройство',
        language: 'Язык интерфейса',
        languageHint: 'Влияет на киоск, админку и печатаемую этикетку.',
        storeName: 'Название магазина',
        currency: 'Валюта',
        labelSize: 'Размер этикетки, мм',
        barcode: 'Штрихкод',
        template: 'Шаблон EAN-13',
        templateHint:
          'P — цифра PLU, W — цифра значения, остальные символы копируются как есть. Например {example}: префикс 22, пять цифр PLU, пять цифр значения.',
        encode: 'Что кодировать',
        encodeWeight: 'Масса, г',
        encodeTotal: 'Сумма, коп',
        encodeHint: 'Зависит от того, как настроены кассы в торговой сети.',
        kiosk: 'Поведение киоска',
        minWeight: 'Минимальная масса, г',
        minWeightHint: 'Ниже этого значения печать не разрешается.',
        requireStable: 'Печатать только по стабильному весу',
        requireStableHint:
          'Отключать только для отладки: этикетка с «дрожащим» весом врёт покупателю.',
        idleReset: 'Сброс экрана, с',
        save: 'Сохранить',
        reset: 'Отменить изменения',
        saved: 'Настройки сохранены',
        saveFailed: 'Не удалось сохранить',
      },
    },
  },
}

export const i18n = createI18n({
  legacy: false,
  locale: 'uk',
  fallbackLocale: 'uk',
  messages,
})

const ELEMENT_LOCALES = { uk: elementUk, ru: elementRu }

export function isLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

/** Язык приходит из настроек устройства, поэтому меняется в рантайме, а не на сборке. */
export function setLocale(value: string) {
  const locale: Locale = isLocale(value) ? value : 'uk'
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  return locale
}

export function elementLocale(value: string) {
  return ELEMENT_LOCALES[isLocale(value) ? value : 'uk']
}

/** Код ошибки от бэкенда -> формулировка. Незнакомый код не должен ломать экран. */
export function translateError(code: string | null | undefined): string {
  if (!code) return ''
  // Код вида "print.paper_out" -> ключ "errors.print_paper_out":
  // точка в ключе интерпретировалась бы как путь во вложенном объекте.
  const key = `errors.${code.replace(/\./g, '_')}`
  const text = i18n.global.t(key)
  return text === key ? i18n.global.t('errors.unknown') : text
}
