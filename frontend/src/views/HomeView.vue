<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
          <p class="text-2xl font-bold text-gray-800">{{ stats?.total.toLocaleString() }}</p>
          <p class="text-sm text-gray-500">总图片数</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
          <p class="text-2xl font-bold text-gray-800">{{ stats?.with_time.toLocaleString() }}</p>
          <p class="text-sm text-gray-500">有时间信息</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
          <p class="text-2xl font-bold text-gray-800">{{ stats?.with_gps.toLocaleString() }}</p>
          <p class="text-sm text-gray-500">有位置信息</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
          <p class="text-2xl font-bold text-gray-800">{{ stats?.cluster_count }}</p>
          <p class="text-sm text-gray-500">聚类数</p>
        </div>
      </div>

      <!-- 最近图片 -->
      <section class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800">最近拍摄</h2>
          <router-link to="/timeline" class="text-sm text-primary-600 hover:text-primary-700">查看全部</router-link>
        </div>
        <PhotoGrid :items="recentAssets" />
      </section>

      <!-- 已保存搜索 -->
      <section v-if="savedSearches.length" class="mb-8">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">已保存搜索</h2>
        <div class="flex flex-wrap gap-2">
          <router-link
            v-for="s in savedSearches"
            :key="s.id"
            :to="{ path: '/explore', query: s.query_json }"
            class="px-3 py-1.5 bg-white border border-primary-200 rounded-full text-sm text-primary-700 hover:bg-primary-50 transition-colors"
          >
            {{ s.name }}
          </router-link>
        </div>
      </section>

      <!-- 热门城市 -->
      <section v-if="stats && stats.top_cities.length">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">热门地点</h2>
        <div class="flex flex-wrap gap-2">
          <router-link
            v-for="city in stats.top_cities"
            :key="city.city"
            :to="{ path: '/explore', query: { city: city.city } }"
            class="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:bg-primary-50 hover:border-primary-200 cursor-pointer transition-colors"
          >
            {{ city.city }}（{{ city.count }}）
          </router-link>
        </div>
      </section>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchStats, fetchAssets, fetchSavedSearches, type StatsOverview, type AssetBrief, type SavedSearch } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const stats = ref<StatsOverview | null>(null)
const recentAssets = ref<AssetBrief[]>([])
const savedSearches = ref<SavedSearch[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [s, a, ss] = await Promise.all([
      fetchStats(),
      fetchAssets({ page: 1, page_size: 24, sort_by: 'taken_at', order: 'desc' }),
      fetchSavedSearches().catch(() => []),
    ])
    stats.value = s
    recentAssets.value = a.items
    savedSearches.value = ss
  } finally {
    loading.value = false
  }
})
</script>
