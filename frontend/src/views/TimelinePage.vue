<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">时间线</h2>
      <div class="flex items-center gap-2">
        <button
          @click="toggleSelectMode"
          class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
          :class="selectMode ? 'bg-primary-500 text-white border-primary-500' : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'"
        >{{ selectMode ? '选择中' : '多选' }}</button>
        <button
          v-if="selectMode"
          @click="cancelSelect"
          class="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >取消</button>
      </div>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <div v-for="bucket in timeline" :key="bucket.month" class="mb-8" :ref="(el) => setMonthRef(el, bucket.month)" :data-month="bucket.month">
        <div class="flex items-center gap-3 mb-3">
          <h3
            class="text-base font-medium text-gray-700 dark:text-gray-200 cursor-pointer hover:text-primary-600"
            @click="loadMonth(bucket.month)"
          >{{ formatMonth(bucket.month) }}</h3>
          <span class="text-sm text-gray-400">{{ bucket.count }} 张</span>
          <router-link
            :to="{ path: '/explore', query: { month: bucket.month } }"
            class="text-xs text-primary-500 hover:text-primary-700"
          >在探索页查看</router-link>
        </div>
        <!-- 已加载的月份显示图片 -->
        <template v-if="monthAssets[bucket.month]">
          <PhotoGrid
            :items="displayItems(bucket.month)"
            :selectable="selectMode"
            :selected-ids="selectedIds"
            @toggle="handleToggle"
          />
          <div class="mt-2 flex items-center gap-3">
            <button
              v-if="!expandedMonths.has(bucket.month) && monthAssets[bucket.month].length > previewCount"
              @click="expandedMonths.add(bucket.month)"
              class="text-sm text-primary-500 hover:text-primary-700"
            >展开全部（{{ monthAssets[bucket.month].length }} 张）</button>
            <button
              v-if="expandedMonths.has(bucket.month) && monthAssets[bucket.month].length > previewCount"
              @click="expandedMonths.delete(bucket.month)"
              class="text-sm text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >收起</button>
            <button
              @click="collapseMonth(bucket.month)"
              class="text-sm text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >折叠</button>
          </div>
        </template>
        <!-- 未加载的月份显示代表图 + 加载按钮 -->
        <div v-else class="flex items-center gap-2">
          <img
            v-if="bucket.representative_id"
            :src="thumbnailUrl(bucket.representative_id, 'sm')"
            class="h-20 w-20 object-cover rounded cursor-pointer"
            @click="loadMonth(bucket.month)"
          />
          <button
            @click="loadMonth(bucket.month)"
            class="text-sm text-primary-500 hover:text-primary-700"
          >加载图片</button>
        </div>
      </div>
    </template>
    <PhotoDetail @deleted="onAssetDeleted" />

    <!-- 底部操作栏 -->
    <div
      v-if="selectMode && selectedIds.size > 0"
      class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between z-[9999]"
    >
      <span class="text-sm text-gray-600 dark:text-gray-300">已选择 {{ selectedIds.size }} 张</span>
      <div class="flex items-center gap-3">
        <button
          @click="showAlbumPicker = true"
          class="px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >添加到相册</button>
        <button
          @click="handleBatchDelete"
          class="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
        >批量删除</button>
      </div>
    </div>

    <AlbumPicker
      :visible="showAlbumPicker"
      @close="showAlbumPicker = false"
      @select="handleAlbumSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { fetchTimeline, fetchTimelineMonth, fetchAlbums, createAlbum, addAssetToAlbum, deleteAsset, thumbnailUrl, type TimelineBucket, type AssetBrief, type Album } from '../api'
import { useUiStore } from '../stores/ui'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'
import AlbumPicker from '../components/AlbumPicker.vue'

const ui = useUiStore()

const timeline = ref<TimelineBucket[]>([])
const loading = ref(true)
const expandedMonths = reactive(new Set<string>())
const monthAssets = reactive<Record<string, AssetBrief[]>>({})
const selectMode = ref(false)
const selectedIds = reactive(new Set<number>())
const showAlbumPicker = ref(false)
const previewCount = computed(() => ui.gridColumns * 2)
const monthRefs = ref<Record<string, HTMLElement>>({})

function formatMonth(m: string): string {
  const [year, month] = m.split('-')
  return `${year}年${parseInt(month)}月`
}

function displayItems(month: string) {
  const items = monthAssets[month] || []
  if (expandedMonths.has(month)) return items
  return items.slice(0, previewCount.value)
}

async function loadMonth(month: string) {
  if (!monthAssets[month]) {
    const res = await fetchTimelineMonth(month, { page_size: 200 })
    monthAssets[month] = res.items
  }
}

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
    selectedIds.add(assetId)
  }
}

function collapseMonth(month: string) {
  delete monthAssets[month]
  expandedMonths.delete(month)
}

function onAssetDeleted(assetId: number) {
  for (const month in monthAssets) {
    monthAssets[month] = monthAssets[month].filter(a => a.asset_id !== assetId)
  }
}

async function handleAlbumSelected(albumId: number) {
  showAlbumPicker.value = false
  if (selectedIds.size === 0) return

  let added = 0
  for (const assetId of selectedIds) {
    try {
      await addAssetToAlbum(albumId, assetId)
      added++
    } catch {}
  }
  alert(`已添加 ${added} 张图片到相册`)
  selectMode.value = false
  selectedIds.clear()
}

async function handleBatchDelete() {
  if (selectedIds.size === 0) return
  if (!window.confirm(`确定要删除选中的 ${selectedIds.size} 张图片吗？\n原图将移到回收站。`)) return
  let deleted = 0
  for (const assetId of selectedIds) {
    try {
      await deleteAsset(assetId)
      deleted++
      for (const month in monthAssets) {
        monthAssets[month] = monthAssets[month].filter(a => a.asset_id !== assetId)
      }
    } catch {}
  }
  alert(`已删除 ${deleted} 张图片`)
  selectMode.value = false
  selectedIds.clear()
}

// 懒加载：前3个月立即加载两行，其余月份滚动到视口时加载
let observer: IntersectionObserver | null = null

function setMonthRef(el: any, month: string) {
  if (el) monthRefs.value[month] = el
}

function setupObserver() {
  observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        const month = (entry.target as HTMLElement).dataset.month
        if (month && !monthAssets[month]) {
          loadMonth(month)
        }
      }
    }
  }, { rootMargin: '200px' })

  nextTick(() => {
    // 只观察前3个月之后的月份
    const laterMonths = timeline.value.slice(3)
    for (const bucket of laterMonths) {
      const el = monthRefs.value[bucket.month]
      if (el) observer!.observe(el)
    }
  })
}

onMounted(async () => {
  try {
    timeline.value = await fetchTimeline()
    // 前3个月立即加载两行图片
    const first3 = timeline.value.slice(0, 3)
    await Promise.all(first3.map(b => loadMonth(b.month)))
    await nextTick()
    setupObserver()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})
</script>
