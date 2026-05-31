<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/clusters" class="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ clusterName }}</h2>
      <span class="text-sm text-gray-400">{{ total }} 张</span>
      <div class="ml-auto flex items-center gap-2">
        <button
          v-if="items.length"
          @click="toggleSelectMode"
          class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
          :class="selectMode ? 'bg-primary-500 text-white border-primary-500' : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'"
        >{{ selectMode ? '选择中' : '选择封面' }}</button>
        <button
          v-if="selectMode"
          @click="cancelSelect"
          class="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >取消</button>
        <button
          v-if="currentCoverId"
          @click="handleClearCover"
          class="px-3 py-1.5 text-sm text-orange-600 border border-orange-200 rounded-lg hover:bg-orange-50 dark:border-orange-700 dark:hover:bg-orange-900/30"
        >取消封面</button>
      </div>
    </div>

    <!-- 当前封面提示 -->
    <div v-if="currentCoverId && !selectMode" class="mb-4 flex items-center gap-3 px-3 py-2 bg-primary-50 dark:bg-primary-900/20 border border-primary-100 dark:border-primary-800 rounded-lg">
      <img :src="thumbnailUrl(currentCoverId, 'sm')" class="w-10 h-10 rounded object-cover" />
      <span class="text-sm text-primary-700 dark:text-primary-300">当前封面</span>
    </div>

    <!-- 聚类增强信息 -->
    <div v-if="clusterInfo" class="mb-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
      <p v-if="clusterInfo.summary_text" class="text-sm text-gray-600 dark:text-gray-400 mb-3">{{ clusterInfo.summary_text }}</p>
      <div v-if="clusterInfo.cover_asset_ids.length" class="flex gap-2 mb-3">
        <img
          v-for="aid in clusterInfo.cover_asset_ids"
          :key="aid"
          :src="thumbnailUrl(aid, 'sm')"
          class="w-20 h-20 object-cover rounded-lg"
        />
      </div>
      <div v-if="clusterInfo.distinct_tags.length" class="flex flex-wrap gap-1.5">
        <router-link
          v-for="tag in clusterInfo.distinct_tags"
          :key="tag"
          :to="{ path: '/explore', query: { tag } }"
          class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full text-xs hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:text-primary-700 dark:hover:text-primary-300"
        >{{ tag }}</router-link>
      </div>
    </div>

    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <PhotoGrid
      :items="items"
      :selectable="selectMode"
      :selected-ids="selectedIds"
      @toggle="handleToggle"
    />
    <div v-if="page < totalPages" class="flex justify-center mt-6">
      <button
        @click="loadMore"
        :disabled="loading"
        class="px-6 py-2 bg-primary-500 text-white rounded-full text-sm hover:bg-primary-600 disabled:opacity-50"
      >
        {{ loading ? '加载中...' : '加载更多' }}
      </button>
    </div>
    <PhotoDetail @deleted="onAssetDeleted" />

    <!-- 底部操作栏 -->
    <div
      v-if="selectMode && selectedIds.size > 0"
      class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between z-[9999]"
    >
      <span class="text-sm text-gray-600 dark:text-gray-300">已选择 {{ selectedIds.size }} 张</span>
      <div class="flex items-center gap-3">
        <button
          v-if="selectedIds.size === 1"
          @click="handleSetCover"
          class="px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >设为封面</button>
        <span v-else class="text-xs text-gray-400">请只选择 1 张图片来设为封面</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchClusterAssets, fetchClusterDetail, setClusterCover, thumbnailUrl, type AssetBrief, type ClusterDetail } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const items = ref<AssetBrief[]>([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const clusterName = ref('')
const clusterInfo = ref<ClusterDetail | null>(null)
const currentCoverId = ref<number | null>(null)
const selectMode = ref(false)
const selectedIds = reactive(new Set<number>())

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  if (!selectMode.value) selectedIds.clear()
}

function cancelSelect() {
  selectMode.value = false
  selectedIds.clear()
}

function handleToggle(assetId: number) {
  if (selectedIds.has(assetId)) {
    selectedIds.delete(assetId)
  } else {
    selectedIds.clear()
    selectedIds.add(assetId)
  }
}

async function handleSetCover() {
  const assetId = [...selectedIds][0]
  if (!assetId) return
  const clusterId = Number(route.params.id)
  try {
    await setClusterCover(clusterId, assetId)
    currentCoverId.value = assetId
    selectMode.value = false
    selectedIds.clear()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '设置失败')
  }
}

async function handleClearCover() {
  const clusterId = Number(route.params.id)
  try {
    await setClusterCover(clusterId, null)
    currentCoverId.value = null
  } catch (e: any) {
    alert(e?.response?.data?.detail || '操作失败')
  }
}

async function loadMore() {
  loading.value = true
  try {
    page.value++
    const res = await fetchClusterAssets(Number(route.params.id), { page: page.value })
    items.value.push(...res.items)
  } finally {
    loading.value = false
  }
}

function onAssetDeleted(assetId: number) {
  items.value = items.value.filter(a => a.asset_id !== assetId)
  total.value = Math.max(0, total.value - 1)
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const [res, detail] = await Promise.all([
      fetchClusterAssets(id, { page: 1, page_size: 100 }),
      fetchClusterDetail(id).catch(() => null),
    ])
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
    clusterInfo.value = detail
    currentCoverId.value = detail?.representative_asset_id ?? null
    clusterName.value = detail?.cluster_name || (res.items.length > 0 ? res.items[0].cluster_name || '未分类' : '未分类')
  } finally {
    loading.value = false
  }
})
</script>
