<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800">时间线</h2>
      <div class="flex items-center gap-2">
        <button
          @click="toggleSelectMode"
          class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
          :class="selectMode ? 'bg-primary-500 text-white border-primary-500' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
        >{{ selectMode ? `已选 ${selectedIds.size} 张` : '多选' }}</button>
        <button
          v-if="selectMode && selectedIds.size > 0"
          @click="handleBatchAddToAlbum"
          class="px-3 py-1.5 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >添加到相册</button>
        <button
          v-if="selectMode"
          @click="cancelSelect"
          class="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
        >取消</button>
      </div>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <div v-for="bucket in timeline" :key="bucket.month" class="mb-8">
        <div class="flex items-center gap-3 mb-3">
          <h3
            class="text-base font-medium text-gray-700 cursor-pointer hover:text-primary-600"
            @click="toggleMonth(bucket.month)"
          >{{ formatMonth(bucket.month) }}</h3>
          <span class="text-sm text-gray-400">{{ bucket.count }} 张</span>
          <router-link
            :to="{ path: '/explore', query: { month: bucket.month } }"
            class="text-xs text-primary-500 hover:text-primary-700"
          >查看全部</router-link>
        </div>
        <PhotoGrid
          v-if="expandedMonths.has(bucket.month)"
          :items="monthAssets[bucket.month] || []"
          :selectable="selectMode"
          :selected-ids="selectedIds"
          @toggle="handleToggle"
        />
        <!-- 收起状态显示代表图 -->
        <div v-else class="flex gap-1 overflow-hidden h-20">
          <img
            v-if="bucket.representative_id"
            :src="thumbnailUrl(bucket.representative_id, 'sm')"
            class="h-20 w-20 object-cover rounded"
          />
        </div>
      </div>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { fetchTimeline, fetchTimelineMonth, fetchAlbums, createAlbum, addAssetToAlbum, thumbnailUrl, type TimelineBucket, type AssetBrief, type Album } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const timeline = ref<TimelineBucket[]>([])
const loading = ref(true)
const expandedMonths = reactive(new Set<string>())
const monthAssets = reactive<Record<string, AssetBrief[]>>({})
const selectMode = ref(false)
const selectedIds = reactive(new Set<number>())

function formatMonth(m: string): string {
  const [year, month] = m.split('-')
  return `${year}年${parseInt(month)}月`
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

async function handleBatchAddToAlbum() {
  if (selectedIds.size === 0) return
  const albums = await fetchAlbums().catch(() => [])
  const options = albums.map(a => `${a.id}: ${a.name}`).join('\n')
  const input = prompt(`选择相册（输入编号）或输入新相册名称：\n${options}\n\n输入数字选择已有相册，或输入文字创建新相册：`)
  if (!input) return

  let albumId: number
  const num = parseInt(input)
  if (!isNaN(num) && albums.find(a => a.id === num)) {
    albumId = num
  } else {
    const newAlbum = await createAlbum(input)
    albumId = newAlbum.id
  }

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

async function toggleMonth(month: string) {
  if (expandedMonths.has(month)) {
    expandedMonths.delete(month)
    return
  }
  expandedMonths.add(month)
  if (!monthAssets[month]) {
    const res = await fetchTimelineMonth(month, { page_size: 100 })
    monthAssets[month] = res.items
  }
}

onMounted(async () => {
  try {
    timeline.value = await fetchTimeline()
  } finally {
    loading.value = false
  }
})
</script>
