<template>
  <header class="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <button @click="ui.toggleSidebar()" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
        <svg class="w-5 h-5 text-gray-700 dark:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <h1 class="text-lg font-semibold text-gray-800 dark:text-gray-100">Album Explorer</h1>
    </div>
    <div class="flex items-center gap-3">
      <div class="relative">
        <input
          v-model="searchInput"
          @keyup.enter="doSearch"
          type="search"
          :placeholder="$t('header.searchPlaceholder')"
          class="w-80 pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-800 dark:text-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white dark:focus:bg-gray-700"
        />
        <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <button @click="toggleLocale" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300" :title="$t('header.switchLang')">
        {{ locale === 'zh-CN' ? 'EN' : '中' }}
      </button>
      <button @click="ui.toggleTheme()" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg" :title="$t('header.toggleTheme')">
        <svg v-if="ui.dark" class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
        </svg>
        <svg v-else class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '../../stores/ui'

const ui = useUiStore()
const router = useRouter()
const { locale } = useI18n()
const searchInput = ref('')

function doSearch() {
  const q = searchInput.value.trim()
  if (q) {
    router.push({ path: '/explore', query: { q } })
  }
}

function toggleLocale() {
  const next = locale.value === 'zh-CN' ? 'en' : 'zh-CN'
  locale.value = next
  localStorage.setItem('locale', next)
  document.documentElement.lang = next === 'zh-CN' ? 'zh' : 'en'
}
</script>
