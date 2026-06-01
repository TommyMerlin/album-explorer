<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-800 mb-4">
      {{ $t('search.title') }}<span v-if="query" class="text-gray-400 font-normal">{{ $t('search.query', { q: query }) }}</span>
    </h2>
    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="searched && !items.length" class="text-center py-12 text-gray-400">
      {{ $t('search.noResults') }}
    </div>
    <template v-else>
      <p class="text-sm text-gray-400 mb-4">{{ $t('search.results', { count: total }) }}</p>
      <PhotoGrid :items="items" />
      <div v-if="page < totalPages" class="flex justify-center mt-6">
        <button
          @click="loadMore"
          :disabled="loading"
          class="px-6 py-2 bg-primary-500 text-white rounded-full text-sm hover:bg-primary-600 disabled:opacity-50"
        >
          {{ loading ? $t('common.loading') : $t('common.loadMore') }}
        </button>
      </div>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { searchAssets, type AssetBrief } from '../api'
import { useUiStore } from '../stores/ui'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const ui = useUiStore()
const items = ref<AssetBrief[]>([])
const loading = ref(false)
const searched = ref(false)
const query = ref('')
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
let searchController: AbortController | null = null

async function doSearch(q: string) {
  if (!q.trim()) return
  if (searchController) searchController.abort()
  searchController = new AbortController()
  const signal = searchController.signal

  query.value = q
  loading.value = true
  searched.value = true
  page.value = 1
  try {
    const res = await searchAssets(q, { page: 1, page_size: ui.computedPageSize }, signal)
    if (signal.aborted) return
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
  } catch (e: any) {
    if (e?.name === 'AbortError' || e?.name === 'CanceledError' || signal.aborted) return
    throw e
  } finally {
    if (!signal.aborted) loading.value = false
  }
}

async function loadMore() {
  loading.value = true
  try {
    page.value++
    const res = await searchAssets(query.value, { page: page.value, page_size: ui.computedPageSize })
    items.value.push(...res.items)
  } finally {
    loading.value = false
  }
}

watch(() => route.query.q, (q) => {
  if (q) doSearch(q as string)
}, { immediate: true })
</script>
