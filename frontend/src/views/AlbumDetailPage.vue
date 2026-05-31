<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/albums" class="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ album?.name }}</h2>
      <span class="text-sm text-gray-400">{{ album?.asset_count }} 张</span>
      <div class="ml-auto flex items-center gap-2">
        <button
          v-if="album?.items.length"
          @click="toggleSelectMode"
          class="px-3 py-1.5 text-sm border rounded-lg transition-colors"
          :class="selectMode ? 'bg-primary-500 text-white border-primary-500' : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'"
        >{{ selectMode ? '选择中' : '多选' }}</button>
        <button
          v-if="selectMode"
          @click="cancelSelect"
          class="px-3 py-1.5 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >取消</button>
        <button
          @click="handleDelete"
          class="text-xs text-red-500 hover:text-red-700"
        >删除相册</button>
      </div>
    </div>
    <p v-if="album?.description" class="text-sm text-gray-500 dark:text-gray-400 mb-4">{{ album.description }}</p>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!album?.items.length" class="text-center py-12 text-gray-400">
      相册为空，在图片详情中可以添加图片到此相册
    </div>
    <PhotoGrid
      v-else
      :items="album.items"
      :selectable="selectMode"
      :selected-ids="selectedIds"
      @toggle="handleToggle"
    />
    <PhotoDetail @deleted="onAssetDeleted" />

    <!-- 底部操作栏 -->
    <div
      v-if="selectMode && selectedIds.size > 0"
      class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between z-[9999]"
    >
      <span class="text-sm text-gray-600 dark:text-gray-300">已选择 {{ selectedIds.size }} 张</span>
      <div class="flex items-center gap-3">
        <button
          @click="handleBatchRemove"
          class="px-4 py-2 text-sm text-orange-600 border border-orange-200 rounded-lg hover:bg-orange-50 dark:border-orange-700 dark:hover:bg-orange-900/30"
        >移出相册</button>
        <button
          @click="handleBatchDelete"
          class="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 dark:border-red-700 dark:hover:bg-red-900/30"
        >批量删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAlbumDetail, deleteAlbum, removeAssetFromAlbum, deleteAsset, type AlbumDetail } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const router = useRouter()
const album = ref<AlbumDetail | null>(null)
const loading = ref(true)
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
    selectedIds.add(assetId)
  }
}

async function handleBatchRemove() {
  if (!album.value || selectedIds.size === 0) return
  if (!window.confirm(`确定将选中的 ${selectedIds.size} 张图片移出相册？\n图片本身不会被删除。`)) return
  let removed = 0
  for (const assetId of selectedIds) {
    try {
      await removeAssetFromAlbum(album.value.id, assetId)
      album.value.items = album.value.items.filter(i => i.asset_id !== assetId)
      removed++
    } catch {}
  }
  album.value.asset_count = album.value.items.length
  selectMode.value = false
  selectedIds.clear()
}

async function handleBatchDelete() {
  if (!album.value || selectedIds.size === 0) return
  if (!window.confirm(`确定要删除选中的 ${selectedIds.size} 张图片吗？\n原图将移到回收站。`)) return
  let deleted = 0
  for (const assetId of selectedIds) {
    try {
      await deleteAsset(assetId)
      album.value.items = album.value.items.filter(i => i.asset_id !== assetId)
      deleted++
    } catch {}
  }
  album.value.asset_count = album.value.items.length
  selectMode.value = false
  selectedIds.clear()
}

async function handleDelete() {
  if (!album.value) return
  if (!window.confirm(`确定删除相册「${album.value.name}」？\n相册内的图片不会被删除。`)) return
  await deleteAlbum(album.value.id)
  router.push('/albums')
}

function onAssetDeleted(assetId: number) {
  if (album.value) {
    album.value.items = album.value.items.filter(i => i.asset_id !== assetId)
    album.value.asset_count = album.value.items.length
  }
}

onMounted(async () => {
  try {
    album.value = await fetchAlbumDetail(Number(route.params.id))
  } finally {
    loading.value = false
  }
})
</script>
