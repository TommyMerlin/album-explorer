<template>
  <div>
    <!-- 筛选栏 -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <input
        v-model="searchInput"
        @keydown.enter="onSearch"
        type="text"
        :placeholder="$t('explore.searchPlaceholder')"
        class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 rounded-lg text-sm w-64 focus:outline-none focus:border-primary-400"
      />
      <button
        @click="onSearch"
        class="px-3 py-1.5 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600"
      >{{ $t('explore.search') }}</button>
      <button
        @click="showCalendar = !showCalendar"
        class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
      >
        <span class="flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          {{ $t('explore.byTime') }}
        </span>
      </button>
      <select
        v-model="mediaTypeOption"
        @change="onMediaTypeChange"
        class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 rounded-lg text-sm"
      >
        <option value="">{{ $t('explore.mediaTypeAll') }}</option>
        <option value="screenshot">{{ $t('explore.mediaTypeScreenshot') }}</option>
        <option value="long_image">{{ $t('explore.mediaTypeLongImage') }}</option>
        <option value="gif">{{ $t('explore.mediaTypeGif') }}</option>
      </select>
      <button
        @click="toggleFavoriteFilter"
        class="px-3 py-1.5 border rounded-lg text-sm transition-colors"
        :class="filters.isFavorite ? 'border-red-300 bg-red-50 dark:bg-red-900/20 text-red-600' : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
      >
        <span class="flex items-center gap-1">
          <svg class="w-4 h-4" :fill="filters.isFavorite ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
          </svg>
          {{ $t('explore.filterFavorite') }}
        </span>
      </button>

      <!-- 活跃筛选标签 -->
      <span
        v-for="(value, key) in filterTags"
        :key="key"
        class="inline-flex items-center gap-1 px-2 py-1 bg-primary-50 dark:bg-primary-900/30 border border-primary-200 dark:border-primary-700 rounded-full text-xs text-primary-700 dark:text-primary-300"
      >
        {{ value }}
        <button @click="removeFilter(key as string)" class="hover:text-primary-900">&times;</button>
      </span>
      <button
        v-if="filters.hasFilters"
        @click="clearAll"
        class="text-xs text-gray-400 hover:text-gray-600"
      >{{ $t('explore.clearAll') }}</button>
    </div>

    <!-- 日历选择器 -->
    <div v-if="showCalendar" class="mb-4 max-w-xs">
      <DateRangePicker @confirm="onDateRangeConfirm" />
    </div>

    <!-- 结果信息 -->
    <div v-if="loaded && total > 0" class="flex items-center justify-between mb-4">
      <p class="text-sm text-gray-400">{{ $t('explore.results', { count: total.toLocaleString() }) }}</p>
      <div class="flex items-center gap-3">
        <button
          v-if="filters.hasFilters"
          @click="saveSearch"
          class="text-xs px-2 py-1 border border-gray-200 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300"
        >{{ $t('explore.saveSearch') }}</button>
        <select v-model="sortOption" @change="onSortChange" class="text-sm border border-gray-200 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 rounded px-2 py-1">
          <option value="taken_at:desc">{{ $t('explore.sortDesc') }}</option>
          <option value="taken_at:asc">{{ $t('explore.sortAsc') }}</option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="loaded && !items.length" class="text-center py-12 text-gray-400">
      {{ $t('explore.noResults') }}
    </div>

    <!-- 结果网格 -->
    <template v-else>
      <PhotoGrid :items="items" />
      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-6">
        <button
          @click="goPage(page - 1)"
          :disabled="page <= 1"
          class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 dark:text-gray-300 rounded text-sm disabled:opacity-30"
        >{{ $t('common.prevPage') }}</button>
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ $t('common.pageInfo', { current: page, total: totalPages }) }}</span>
        <button
          @click="goPage(page + 1)"
          :disabled="page >= totalPages"
          class="px-3 py-1.5 border border-gray-200 dark:border-gray-600 dark:text-gray-300 rounded text-sm disabled:opacity-30"
        >{{ $t('common.nextPage') }}</button>
      </div>
    </template>
    <PhotoDetail @deleted="onAssetDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { fetchAssets, createSavedSearch, type AssetBrief } from '../api'
import { useFiltersStore } from '../stores/filters'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'
import DateRangePicker from '../components/DateRangePicker.vue'

const route = useRoute()
const router = useRouter()
const filters = useFiltersStore()
const { t } = useI18n()

const items = ref<AssetBrief[]>([])
const loading = ref(false)
const loaded = ref(false)
const total = ref(0)
const totalPages = ref(1)
const page = ref(1)
const searchInput = ref('')
const sortOption = ref('taken_at:desc')
const showCalendar = ref(false)
const mediaTypeOption = ref('')

const filterTags = computed(() => {
  const tags: Record<string, string> = {}
  if (filters.q) tags.q = t('explore.filterSearch', { q: filters.q })
  if (filters.selectedMonth) tags.month = t('explore.filterMonth', { month: filters.selectedMonth })
  if (filters.selectedCity) tags.city = t('explore.filterCity', { city: filters.selectedCity })
  if (filters.selectedProvince) tags.province = t('explore.filterProvince', { province: filters.selectedProvince })
  if (filters.selectedClusterId !== null) tags.cluster_id = t('explore.filterCluster', { id: filters.selectedClusterId })
  if (filters.selectedTag) tags.tag = t('explore.filterTag', { tag: filters.selectedTag })
  if (filters.dateFrom) tags.date_from = t('explore.filterDateFrom', { date: filters.dateFrom })
  if (filters.dateTo) tags.date_to = t('explore.filterDateTo', { date: filters.dateTo })
  if (filters.hasGps !== null) tags.has_gps = filters.hasGps ? t('explore.filterHasGps') : t('explore.filterNoGps')
  if (filters.isFavorite !== null) tags.is_favorite = t('explore.filterFavorite')
  if (filters.selectedMediaType) tags.media_type = t('explore.filterMediaType', { type: t(`explore.mediaType_${filters.selectedMediaType}`) })
  return tags
})

function removeFilter(key: string) {
  filters.setFilter({ [key]: undefined } as any)
  syncToUrl()
}

function clearAll() {
  filters.clearAll()
  searchInput.value = ''
  syncToUrl()
}

function onSearch() {
  filters.setFilter({ q: searchInput.value || undefined })
  syncToUrl()
}

function onSortChange() {
  const [sb, ord] = sortOption.value.split(':')
  filters.setFilter({ sort_by: sb, order: ord })
  syncToUrl()
}

function onMediaTypeChange() {
  filters.setFilter({ media_type: mediaTypeOption.value || undefined })
  syncToUrl()
}

function toggleFavoriteFilter() {
  filters.setFilter({ is_favorite: filters.isFavorite ? undefined : true })
  syncToUrl()
}

function goPage(p: number) {
  filters.setFilter({ page: p })
  page.value = p
  syncToUrl()
}

function syncToUrl() {
  router.replace({ path: '/explore', query: filters.toRouteQuery() })
}

async function saveSearch() {
  const tags = filterTags.value
  const name = prompt(t('explore.saveSearchPrompt'), Object.values(tags).join(' + '))
  if (!name) return
  const queryJson = { ...filters.toRouteQuery() }
  await createSavedSearch(name, queryJson)
  alert(t('explore.saved'))
}

async function loadData() {
  loading.value = true
  try {
    const res = await fetchAssets(filters.activeParams)
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
    page.value = filters.page
    loaded.value = true
  } finally {
    loading.value = false
  }
}

function onAssetDeleted(assetId: number) {
  items.value = items.value.filter(a => a.asset_id !== assetId)
  total.value = Math.max(0, total.value - 1)
}

function onDateRangeConfirm(dateFrom: string, dateTo: string) {
  showCalendar.value = false
  filters.setFilter({ date_from: dateFrom, date_to: dateTo })
  syncToUrl()
}

watch(() => route.query, (query) => {
  if (route.name !== 'explore') return
  filters.applyFromRoute(query as Record<string, any>)
  searchInput.value = filters.q
  sortOption.value = `${filters.sortBy}:${filters.order}`
  mediaTypeOption.value = filters.selectedMediaType || ''
  loadData()
}, { deep: true })

onMounted(() => {
  filters.applyFromRoute(route.query as Record<string, any>)
  searchInput.value = filters.q
  sortOption.value = `${filters.sortBy}:${filters.order}`
  mediaTypeOption.value = filters.selectedMediaType || ''
  loadData()
})
</script>
