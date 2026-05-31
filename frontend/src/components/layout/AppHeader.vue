<template>
  <header class="sticky top-0 z-50 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <button @click="ui.toggleSidebar()" class="p-2 hover:bg-gray-100 rounded-lg">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <h1 class="text-lg font-semibold text-gray-800">Album Explorer</h1>
    </div>
    <div class="flex items-center gap-3">
      <div class="relative">
        <input
          v-model="searchInput"
          @keyup.enter="doSearch"
          type="search"
          placeholder="搜索描述、标签、场景..."
          class="w-80 pl-10 pr-4 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white"
        />
        <svg class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '../../stores/ui'

const ui = useUiStore()
const router = useRouter()
const searchInput = ref('')

function doSearch() {
  const q = searchInput.value.trim()
  if (q) {
    router.push({ path: '/explore', query: { q } })
  }
}
</script>
