import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import en from './locales/en'

export type MessageSchema = typeof zhCN

declare module 'vue-i18n' {
  export interface DefineLocaleMessage extends MessageSchema {}
}

const savedLocale = localStorage.getItem('locale') || 'zh-CN'

const i18n = createI18n<[MessageSchema], 'zh-CN' | 'en'>({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    en,
  },
})

export default i18n
