<template>
  <div>
    <!-- 筛选栏 -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <input
        v-model="searchInput"
        @keydown.enter="onSearch"
        type="text"
        placeholder="搜索图片..."
        class="px-3 py-1.5 border border-gray-200 rounded-lg text-sm w-64 focus:outline-none focus:border-primary-400"
      />
      <button
        @click="onSearch"
        class="px-3 py-1.5 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600"
      >搜索</button>

      <!-- 活跃筛选标签 -->
      <span
        v-for="(value, key) in filterTags"
        :key="key"
        class="inline-flex items-center gap-1 px-2 py-1 bg-primary-50 border border-primary-200 rounded-full text-xs text-primary-700"
      >
        {{ value }}
        <button @click="removeFilter(key as string)" class="hover:text-primary-900">&times;</button>
      </span>
      <button
        v-if="filters.hasFilters"
        @click="clearAll"
        class="text-xs text-gray-400 hover:text-gray-600"
      >清除全部</button>
    </div>

    <!-- 结果信息 -->
    <div v-if="loaded && total > 0" class="flex items-center justify-between mb-4">
      <p class="text-sm text-gray-400">找到 {{ total.toLocaleString() }} 个结果</p>
      <div class="flex items-center gap-3">
        <button
          v-if="filters.hasFilters"
          @click="saveSearch"
          class="text-xs px-2 py-1 border border-gray-200 rounded hover:bg-gray-50"
        >保存搜索</button>
        <select v-model="sortOption" @change="onSortChange" class="text-sm border border-gray-200 rounded px-2 py-1">
          <option value="taken_at:desc">时间倒序</option>
          <option value="taken_at:asc">时间正序</option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="loaded && !items.length" class="text-center py-12 text-gray-400">
      没有找到匹配的图片
    </div>

    <!-- 结果网格 -->
    <template v-else>
      <PhotoGrid :items="items" />
      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-6">
        <button
          @click="goPage(page - 1)"
          :disabled="page <= 1"
          class="px-3 py-1.5 border border-gray-200 rounded text-sm disabled:opacity-30"
        >上一页</button>
        <span class="text-sm text-gray-500">{{ page }} / {{ totalPages }}</span>
        <button
          @click="goPage(page + 1)"
          :disabled="page >= totalPages"
          class="px-3 py-1.5 border border-gray-200 rounded text-sm disabled:opacity-30"
        >下一页</button>
      </div>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAssets, createSavedSearch, type AssetBrief } from '../api'
import { useFiltersStore } from '../stores/filters'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const router = useRouter()
const filters = useFiltersStore()

const items = ref<AssetBrief[]>([])
const loading = ref(false)
const loaded = ref(false)
const total = ref(0)
const totalPages = ref(1)
const page = ref(1)
const searchInput = ref('')
const sortOption = ref('taken_at:desc')

const filterTags = computed(() => {
  const tags: Record<string, string> = {}
  if (filters.q) tags.q = `搜索：${filters.q}`
  if (filters.selectedMonth) tags.month = `月份：${filters.selectedMonth}`
  if (filters.selectedCity) tags.city = `城市：${filters.selectedCity}`
  if (filters.selectedProvince) tags.province = `省份：${filters.selectedProvince}`
  if (filters.selectedClusterId !== null) tags.cluster_id = `聚类：#${filters.selectedClusterId}`
  if (filters.selectedTag) tags.tag = `标签：${filters.selectedTag}`
  if (filters.dateFrom) tags.date_from = `从：${filters.dateFrom}`
  if (filters.dateTo) tags.date_to = `到：${filters.dateTo}`
  if (filters.hasGps !== null) tags.has_gps = filters.hasGps ? '有GPS' : '无GPS'
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
  const name = prompt('为这个搜索命名：', Object.values(tags).join(' + '))
  if (!name) return
  const queryJson = { ...filters.toRouteQuery() }
  await createSavedSearch(name, queryJson)
  alert('已保存')
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

watch(() => route.query, (query) => {
  if (route.name !== 'explore') return
  filters.applyFromRoute(query as Record<string, any>)
  searchInput.value = filters.q
  sortOption.value = `${filters.sortBy}:${filters.order}`
  loadData()
}, { deep: true })

onMounted(() => {
  filters.applyFromRoute(route.query as Record<string, any>)
  searchInput.value = filters.q
  sortOption.value = `${filters.sortBy}:${filters.order}`
  loadData()
})
</script>
