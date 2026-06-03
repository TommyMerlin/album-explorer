<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ $t('favorites.title') }}</h2>
      <span v-if="total > 0" class="text-sm text-gray-400">{{ $t('common.photos', { count: total }) }}</span>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!items.length" class="text-center py-12 text-gray-400">
      {{ $t('favorites.empty') }}
    </div>
    <template v-else>
      <PhotoGrid
        :items="items"
        @open="handleOpen"
      />
      <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-6">
        <button
          :disabled="page <= 1"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 disabled:opacity-40"
          @click="page--; loadPage()"
        >{{ $t('common.prevPage') }}</button>
        <span class="text-sm text-gray-500">{{ $t('common.pageInfo', { current: page, total: totalPages }) }}</span>
        <button
          :disabled="page >= totalPages"
          class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 disabled:opacity-40"
          @click="page++; loadPage()"
        >{{ $t('common.nextPage') }}</button>
      </div>
    </template>
    <PhotoDetail @deleted="handleDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUiStore } from '../stores/ui'
import { fetchFavorites, type AssetBrief } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const ui = useUiStore()
const items = ref<AssetBrief[]>([])
const loading = ref(true)
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)

async function loadPage() {
  loading.value = true
  try {
    const res = await fetchFavorites({ page: page.value, page_size: ui.computedPageSize })
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
  } finally {
    loading.value = false
  }
}

function handleOpen(assetId: number) {
  ui.openDetail(assetId, items.value.map(i => i.asset_id))
}

function handleDeleted(assetId: number) {
  items.value = items.value.filter(i => i.asset_id !== assetId)
  total.value--
}

onMounted(() => loadPage())
</script>
