<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <!-- 设置栏 -->
      <div class="flex items-center justify-end gap-3 mb-4">
        <label class="text-sm text-gray-500 dark:text-gray-400">每行显示：</label>
        <input
          type="range"
          :min="4"
          :max="12"
          :value="ui.gridColumns"
          @input="ui.setGridColumns(Number(($event.target as HTMLInputElement).value))"
          class="w-28"
        />
        <span class="text-sm text-gray-600 dark:text-gray-300 w-6">{{ ui.gridColumns }}</span>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100">{{ stats?.total.toLocaleString() }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">总图片数</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100">{{ stats?.with_time.toLocaleString() }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">有时间信息</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100">{{ stats?.with_gps.toLocaleString() }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">有位置信息</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100">{{ stats?.cluster_count }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">聚类数</p>
        </div>
      </div>

      <!-- 最近图片 -->
      <section class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">最近拍摄</h2>
          <router-link to="/timeline" class="text-sm text-primary-600 hover:text-primary-700">查看全部</router-link>
        </div>
        <PhotoGrid :items="recentAssets" />
      </section>

      <!-- 随机精选 -->
      <section v-if="randomPicks.length" class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">随机精选</h2>
            <button @click="refreshRandom" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="换一批">
              <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
        </div>
        <PhotoGrid :items="randomPicks" />
      </section>

      <!-- 热门主题 -->
      <section v-if="clusterPick && clusterPick.items.length" class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">主题推荐：{{ clusterPick.name }}</h2>
            <button @click="refreshCluster" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="换一批">
              <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
          <router-link
            :to="{ path: '/explore', query: { cluster_id: String(clusterPick.cluster_id) } }"
            class="text-sm text-primary-600 hover:text-primary-700"
          >查看全部</router-link>
        </div>
        <PhotoGrid :items="clusterPick.items" />
      </section>

      <!-- 已保存搜索 -->
      <section v-if="savedSearches.length" class="mb-8">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">已保存搜索</h2>
        <div class="flex flex-wrap gap-2">
          <router-link
            v-for="s in savedSearches"
            :key="s.id"
            :to="{ path: '/explore', query: s.query_json }"
            class="px-3 py-1.5 bg-white dark:bg-gray-800 border border-primary-200 dark:border-primary-700 rounded-full text-sm text-primary-700 dark:text-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/30 transition-colors"
          >
            {{ s.name }}
          </router-link>
        </div>
      </section>

      <!-- 热门城市 -->
      <section v-if="stats && stats.top_cities.length">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">热门地点</h2>
        <div class="flex flex-wrap gap-2">
          <router-link
            v-for="city in stats.top_cities"
            :key="city.city"
            :to="{ path: '/explore', query: { city: city.city } }"
            class="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full text-sm text-gray-700 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:border-primary-200 cursor-pointer transition-colors"
          >
            {{ city.city }}（{{ city.count }}）
          </router-link>
        </div>
      </section>
    </template>
    <PhotoDetail @deleted="onAssetDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { fetchStats, fetchAssets, fetchSavedSearches, fetchRandomPicks, fetchClusterPick, type StatsOverview, type AssetBrief, type SavedSearch, type ClusterPick } from '../api'
import { useUiStore } from '../stores/ui'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const ui = useUiStore()

const stats = ref<StatsOverview | null>(null)
const recentAssets = ref<AssetBrief[]>([])
const savedSearches = ref<SavedSearch[]>([])
const randomPicks = ref<AssetBrief[]>([])
const clusterPick = ref<ClusterPick | null>(null)
const loading = ref(true)

const twoRows = () => ui.gridColumns * 2

async function refreshRandom() {
  randomPicks.value = await fetchRandomPicks(twoRows())
}

async function refreshCluster() {
  clusterPick.value = await fetchClusterPick(twoRows())
}

function onAssetDeleted(assetId: number) {
  recentAssets.value = recentAssets.value.filter(a => a.asset_id !== assetId)
  randomPicks.value = randomPicks.value.filter(a => a.asset_id !== assetId)
  if (clusterPick.value) {
    clusterPick.value.items = clusterPick.value.items.filter(a => a.asset_id !== assetId)
  }
}

async function loadHomeData() {
  const size = twoRows()
  const [s, a, ss, rnd, cls] = await Promise.all([
    fetchStats(),
    fetchAssets({ page: 1, page_size: size, sort_by: 'taken_at', order: 'desc' }),
    fetchSavedSearches().catch(() => []),
    fetchRandomPicks(size).catch(() => []),
    fetchClusterPick(size).catch(() => null),
  ])
  stats.value = s
  recentAssets.value = a.items
  savedSearches.value = ss
  randomPicks.value = rnd
  clusterPick.value = cls
}

watch(() => ui.gridColumns, async () => {
  const size = twoRows()
  const [a, rnd, cls] = await Promise.all([
    fetchAssets({ page: 1, page_size: size, sort_by: 'taken_at', order: 'desc' }),
    fetchRandomPicks(size).catch(() => []),
    fetchClusterPick(size).catch(() => null),
  ])
  recentAssets.value = a.items
  randomPicks.value = rnd
  clusterPick.value = cls
})

onMounted(async () => {
  try {
    await loadHomeData()
  } finally {
    loading.value = false
  }
})
</script>
