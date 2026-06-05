<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ $t('timeline.title') }}</h2>
      <div class="flex items-center gap-2">
        <button
          @click="toggleSelectMode"
          class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
          :class="selectMode ? 'bg-primary-500 text-white border-primary-500' : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'"
        >{{ selectMode ? $t('common.selecting') : $t('common.multiSelect') }}</button>
        <button
          v-if="selectMode"
          @click="cancelSelect"
          class="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >{{ $t('common.cancel') }}</button>
      </div>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <div v-for="bucket in timeline" :key="bucket.month" class="mb-8" :data-month="bucket.month">
        <div class="flex items-center gap-3 mb-3">
          <h3
            class="text-base font-medium text-gray-700 dark:text-gray-200 cursor-pointer hover:text-primary-600"
            @click="loadMonth(bucket.month)"
          >{{ formatMonth(bucket.month) }}</h3>
          <span class="text-sm text-gray-400">{{ $t('common.photos', { count: bucket.count }) }}</span>
          <router-link
            :to="{ path: '/explore', query: { month: bucket.month } }"
            class="text-xs text-primary-500 hover:text-primary-700"
          >{{ $t('timeline.viewInExplore') }}</router-link>
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
            >{{ $t('common.expandAll', { count: monthAssets[bucket.month].length }) }}</button>
            <button
              v-if="expandedMonths.has(bucket.month) && monthAssets[bucket.month].length > previewCount"
              @click="expandedMonths.delete(bucket.month)"
              class="text-sm text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >{{ $t('common.collapse') }}</button>
            <button
              @click="collapseMonth(bucket.month)"
              class="text-sm text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >{{ $t('common.fold') }}</button>
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
          >{{ $t('timeline.loadPhotos') }}</button>
        </div>
      </div>
    </template>
    <PhotoDetail @deleted="onAssetDeleted" />

    <!-- 底部操作栏 -->
    <div
      v-if="selectMode && selectedIds.size > 0"
      class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between z-[9999]"
    >
      <span class="text-sm text-gray-600 dark:text-gray-300">{{ $t('common.selected', { count: selectedIds.size }) }}</span>
      <div class="flex items-center gap-3">
        <button
          @click="showAlbumPicker = true"
          class="px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >{{ $t('timeline.addToAlbum') }}</button>
        <button
          @click="handleBatchDelete"
          class="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
        >{{ $t('timeline.batchDelete') }}</button>
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
import { useI18n } from 'vue-i18n'
import { fetchTimeline, fetchTimelineMonth, addAssetToAlbum, deleteAsset, thumbnailUrl, type TimelineBucket, type AssetBrief } from '../api'
import { useUiStore } from '../stores/ui'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'
import AlbumPicker from '../components/AlbumPicker.vue'

const ui = useUiStore()
const { t } = useI18n()

const timeline = ref<TimelineBucket[]>([])
const loading = ref(true)
const expandedMonths = reactive(new Set<string>())
const monthAssets = reactive<Record<string, AssetBrief[]>>({})
const selectMode = ref(false)
const selectedIds = reactive(new Set<number>())
const showAlbumPicker = ref(false)
const previewCount = computed(() => ui.gridColumns * 2)

function formatMonth(m: string): string {
  const [year, month] = m.split('-')
  return t('timeline.month', { year, month: parseInt(month) })
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
    const before = monthAssets[month].length
    monthAssets[month] = monthAssets[month].filter(a => a.asset_id !== assetId)
    if (monthAssets[month].length < before) {
      updateBucketCount(month, -1)
    }
  }
}

function updateBucketCount(month: string, delta: number) {
  const bucket = timeline.value.find(b => b.month === month)
  if (bucket) {
    bucket.count += delta
    if (bucket.count <= 0) {
      timeline.value = timeline.value.filter(b => b.month !== month)
      delete monthAssets[month]
      expandedMonths.delete(month)
    }
  }
}

async function handleAlbumSelected(albumId: number) {
  showAlbumPicker.value = false
  if (selectedIds.size === 0) return

  const results = await Promise.allSettled(
    [...selectedIds].map(assetId => addAssetToAlbum(albumId, assetId))
  )
  const added = results.filter(r => r.status === 'fulfilled').length
  const failed = results.filter(r => r.status === 'rejected').length
  if (failed > 0) {
    alert(t('timeline.addedWithFail', { added, failed }))
  } else {
    alert(t('timeline.addedToAlbum', { added }))
  }
  selectMode.value = false
  selectedIds.clear()
}

async function handleBatchDelete() {
  if (selectedIds.size === 0) return
  if (!window.confirm(t('timeline.deleteConfirm', { count: selectedIds.size }))) return

  const ids = [...selectedIds]
  const results = await Promise.allSettled(
    ids.map(assetId => deleteAsset(assetId))
  )
  let deleted = 0
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      deleted++
      for (const month in monthAssets) {
        const before = monthAssets[month].length
        monthAssets[month] = monthAssets[month].filter(a => a.asset_id !== ids[i])
        if (monthAssets[month].length < before) {
          updateBucketCount(month, -1)
        }
      }
    }
  })
  const failed = ids.length - deleted
  if (failed > 0) {
    alert(t('timeline.deletedWithFail', { deleted, failed }))
  } else {
    alert(t('timeline.deleted', { count: deleted }))
  }
  selectMode.value = false
  selectedIds.clear()
}

// 懒加载：前3个月立即加载两行，其余月份滚动到视口时加载
let observer: IntersectionObserver | null = null

function setupObserver() {
  observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        const month = (entry.target as HTMLElement).dataset.month
        if (month && !monthAssets[month]) {
          loadMonth(month)
          observer!.unobserve(entry.target)
        }
      }
    }
  }, { rootMargin: '300px' })

  const els = document.querySelectorAll<HTMLElement>('[data-month]')
  const skip = new Set(timeline.value.slice(0, 3).map(b => b.month))
  els.forEach(el => {
    const month = el.dataset.month
    if (month && !skip.has(month)) {
      observer!.observe(el)
    }
  })
}

onMounted(async () => {
  try {
    timeline.value = await fetchTimeline()
    // 前3个月立即加载两行图片
    const first3 = timeline.value.slice(0, 3)
    await Promise.all(first3.map(b => loadMonth(b.month)))
  } finally {
    loading.value = false
  }
  // loading 变为 false 后 DOM 才渲染月份列表，需要等渲染完成
  await nextTick()
  await nextTick()
  setupObserver()
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})
</script>
