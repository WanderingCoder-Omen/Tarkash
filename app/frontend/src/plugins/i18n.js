import Vue from 'vue'
import VueI18n from 'vue-i18n'

Vue.use(VueI18n)

export const i18n = new VueI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    'en': require('@/locales/en.json'),
    'fr': require('@/locales/fr.json'),
    'es': require('@/locales/es.json'),
    'cat': require('@/locales/cat.json'),
    'ru': require('@/locales/ru.json'),
    'pt': require('@/locales/pt.json'),
    'it': require('@/locales/it.json'),
    'de': require('@/locales/de.json')
  }
})