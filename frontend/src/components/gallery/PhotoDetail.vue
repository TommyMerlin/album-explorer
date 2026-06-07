<template>
  <Teleport to="body">
    <div
      v-if="ui.detailModalOpen"
      class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70"
      @click.self="ui.closeDetail()"
    >
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl max-w-[calc(85vh+20rem)] w-full mx-4 max-h-[90vh] min-h-0 overflow-hidden flex">
        <!-- 图片区域 -->
        <div class="flex-1 min-w-0 min-h-[400px] flex flex-col">
          <div class="relative flex-1 min-h-0 bg-gray-900 flex items-center justify-center p-3">
            <!-- 左箭头 -->
            <button
              v-if="ui.hasPrev"
              @click="ui.navigatePrev()"
              class="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/40 hover:bg-black/60 rounded-full text-white z-10 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            <div
              ref="previewViewport"
              class="relative h-full aspect-square max-h-full max-w-full overflow-hidden rounded-xl touch-none select-none"
              @pointerdown="startPan"
              @pointermove="handlePan"
              @pointerup="endPan"
              @pointercancel="endPan"
              @lostpointercapture="cancelPan"
            >
              <img
                v-if="detail"
                ref="previewImage"
                :src="fullImageUrl(detail.asset_id)"
                :alt="detail.caption_short || ''"
                :style="previewImageStyle"
                class="select-none"
                draggable="false"
                @load="handleImageLoad"
              />
              <div v-else class="text-white">{{ $t('detail.loading') }}</div>
            </div>
            <!-- 右箭头 -->
            <button
              v-if="ui.hasNext"
              @click="ui.navigateNext()"
              class="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/40 hover:bg-black/60 rounded-full text-white z-10 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
          <!-- 操作按钮栏 -->
          <div v-if="detail" class="shrink-0 flex flex-wrap items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
            <a :href="fullImageUrl(detail.asset_id)" target="_blank" class="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">{{ $t('detail.viewOriginal') }}</a>
            <a :href="originalImageUrl(detail.asset_id)" :download="detail.rel_path.split('/').pop()" class="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">{{ $t('detail.downloadOriginal') }}</a>
            <button @click="toggleFavorite" class="px-3 py-1.5 text-xs border rounded-lg transition-colors" :class="isFav ? 'text-red-500 border-red-300 dark:border-red-700 hover:bg-red-50 dark:hover:bg-red-900/30' : 'text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'">{{ isFav ? $t('detail.unfavorite') : $t('detail.favorite') }}</button>
            <button @click="showAlbumPicker = true" class="px-3 py-1.5 text-xs text-primary-600 dark:text-primary-400 border border-primary-200 dark:border-primary-700 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/30 transition-colors">{{ $t('detail.addToAlbum') }}</button>
            <button @click="handleDelete" class="px-3 py-1.5 text-xs text-red-600 dark:text-red-400 border border-red-200 dark:border-red-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors">{{ $t('detail.deletePhoto') }}</button>
          </div>
        </div>
        <!-- 信息面板 -->
        <div v-if="detail" class="w-80 p-5 overflow-y-auto border-l border-gray-200 dark:border-gray-700">
          <button @click="ui.closeDetail()" class="absolute top-3 right-3 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-600 dark:text-gray-200 z-10">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h3 class="text-base font-medium text-gray-800 dark:text-gray-100 mb-3">{{ detail.caption_short }}</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">{{ detail.caption_long }}</p>

          <div class="space-y-3 text-sm">
            <div v-if="detail.taken_at" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              <router-link
                :to="{ path: '/explore', query: { month: detail.month_bucket } }"
                class="hover:text-primary-600"
                @click="ui.closeDetail()"
              >{{ detail.taken_at }}</router-link>
            </div>
            <div v-if="detail.city_name" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
              <router-link
                :to="{ path: '/explore', query: { city: detail.city_name } }"
                class="hover:text-primary-600"
                @click="ui.closeDetail()"
              >{{ detail.province_name }} {{ detail.city_name }}</router-link>
            </div>
            <div v-if="detail.cluster_name" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
              <router-link
                :to="{ path: '/explore', query: { cluster_id: String(detail.cluster_id) } }"
                class="hover:text-primary-600"
                @click="ui.closeDetail()"
              >{{ detail.cluster_name }}</router-link>
            </div>
          </div>

          <div v-if="detail.tags.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.tags') }}</h4>
            <div class="flex flex-wrap gap-1.5">
              <router-link
                v-for="tag in detail.tags"
                :key="tag"
                :to="{ path: '/explore', query: { tag } }"
                class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full text-xs hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:text-primary-700 dark:hover:text-primary-300"
                @click="ui.closeDetail()"
              >{{ tag }}</router-link>
            </div>
          </div>

          <div v-if="detail.activities.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.activities') }}</h4>
            <p class="text-sm text-gray-600">{{ detail.activities.join('、') }}</p>
          </div>

          <div v-if="detail.main_subjects.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.subjects') }}</h4>
            <p class="text-sm text-gray-600">{{ detail.main_subjects.join('、') }}</p>
          </div>

          <!-- 上下文探索区块 -->
          <div v-if="context || similar.length" class="mt-4 pt-3 border-t border-gray-100 space-y-4">
            <div v-if="similar.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.similar') }}</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in similar.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                  @error="($event.target as HTMLElement).style.display = 'none'"
                />
              </div>
            </div>
            <div v-if="context && context.same_day.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.sameDay', { date: context.same_day_date }) }}</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in context.same_day.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                  @error="($event.target as HTMLElement).style.display = 'none'"
                />
              </div>
            </div>
            <div v-if="context && context.shared_tags.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ $t('detail.related') }}</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in context.shared_tags.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                  @error="($event.target as HTMLElement).style.display = 'none'"
                />
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-100">
            <p class="text-xs text-gray-400 break-all">{{ detail.rel_path }}</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
  <AlbumPicker
    :visible="showAlbumPicker"
    @close="showAlbumPicker = false"
    @select="handleAlbumSelected"
  />
</template>

<script setup lang="ts">
import { watch, ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '../../stores/ui'
import { useFavoritesStore } from '../../stores/favorites'
import { fetchAssetDetail, fetchAssetContext, fetchSimilarAssets, deleteAsset, addAssetToAlbum, fullImageUrl, originalImageUrl, thumbnailUrl, type AssetDetail, type AssetContext, type AssetBrief } from '../../api'
import AlbumPicker from '../AlbumPicker.vue'

const emit = defineEmits<{ deleted: [assetId: number] }>()

const ui = useUiStore()
const favoritesStore = useFavoritesStore()
const { t } = useI18n()
const detail = ref<AssetDetail | null>(null)
const context = ref<AssetContext | null>(null)
const similar = ref<AssetBrief[]>([])
const showAlbumPicker = ref(false)
const previewViewport = ref<HTMLElement | null>(null)
const previewImage = ref<HTMLImageElement | null>(null)
const naturalSize = reactive({ width: 0, height: 0 })
const renderedSize = reactive({ width: 0, height: 0 })
const viewportSize = reactive({ width: 0, height: 0 })
const imageOffset = reactive({ x: 0, y: 0 })
const dragState = reactive({
  active: false,
  pointerId: -1,
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0,
})

const isFav = computed(() => detail.value ? favoritesStore.isFavorite(detail.value.asset_id) : false)
const aspectRatio = computed(() => naturalSize.height ? naturalSize.width / naturalSize.height : 1)
const useCoverFit = computed(() => aspectRatio.value >= 1.8 || aspectRatio.value <= 0.65)
const canPan = computed(() =>
  renderedSize.width - viewportSize.width > 1 || renderedSize.height - viewportSize.height > 1
)
const previewImageStyle = computed(() => ({
  width: renderedSize.width ? `${renderedSize.width}px` : 'auto',
  height: renderedSize.height ? `${renderedSize.height}px` : 'auto',
  maxWidth: 'none',
  maxHeight: 'none',
  transform: `translate(${imageOffset.x}px, ${imageOffset.y}px)`,
  cursor: canPan.value ? (dragState.active ? 'grabbing' : 'grab') : 'default',
}))

async function toggleFavorite() {
  if (!detail.value) return
  await favoritesStore.toggle(detail.value.asset_id)
}

function resetPreviewState() {
  naturalSize.width = 0
  naturalSize.height = 0
  renderedSize.width = 0
  renderedSize.height = 0
  viewportSize.width = 0
  viewportSize.height = 0
  imageOffset.x = 0
  imageOffset.y = 0
  cancelPan()
}

function clampOffset(x: number, y: number) {
  const maxX = Math.max(0, (renderedSize.width - viewportSize.width) / 2)
  const maxY = Math.max(0, (renderedSize.height - viewportSize.height) / 2)
  return {
    x: Math.min(maxX, Math.max(-maxX, x)),
    y: Math.min(maxY, Math.max(-maxY, y)),
  }
}

function applyOffset(x: number, y: number) {
  const clamped = clampOffset(x, y)
  imageOffset.x = clamped.x
  imageOffset.y = clamped.y
}

function updatePreviewLayout() {
  const viewport = previewViewport.value
  if (!viewport || !naturalSize.width || !naturalSize.height) return
  const width = viewport.clientWidth
  const height = viewport.clientHeight
  if (!width || !height) return
  viewportSize.width = width
  viewportSize.height = height
  const fit = useCoverFit.value
    ? Math.max(width / naturalSize.width, height / naturalSize.height)
    : Math.min(width / naturalSize.width, height / naturalSize.height)
  renderedSize.width = naturalSize.width * fit
  renderedSize.height = naturalSize.height * fit
  applyOffset(imageOffset.x, imageOffset.y)
}

function syncPreviewFromImage() {
  const img = previewImage.value
  if (!img || !img.complete || !img.naturalWidth || !img.naturalHeight) return
  naturalSize.width = img.naturalWidth
  naturalSize.height = img.naturalHeight
  updatePreviewLayout()
}

function handleImageLoad() {
  syncPreviewFromImage()
}

function startPan(event: PointerEvent) {
  if (!canPan.value) return
  if (event.pointerType === 'mouse' && event.button !== 0) return
  dragState.active = true
  dragState.pointerId = event.pointerId
  dragState.startX = event.clientX
  dragState.startY = event.clientY
  dragState.originX = imageOffset.x
  dragState.originY = imageOffset.y
  previewViewport.value?.setPointerCapture(event.pointerId)
}

function handlePan(event: PointerEvent) {
  if (!dragState.active || dragState.pointerId !== event.pointerId) return
  applyOffset(
    dragState.originX + event.clientX - dragState.startX,
    dragState.originY + event.clientY - dragState.startY
  )
}

function cancelPan() {
  dragState.active = false
  dragState.pointerId = -1
}

function endPan(event: PointerEvent) {
  if (dragState.pointerId !== event.pointerId) return
  if (previewViewport.value?.hasPointerCapture(event.pointerId)) {
    previewViewport.value.releasePointerCapture(event.pointerId)
  }
  cancelPan()
}

function handleKeydown(e: KeyboardEvent) {
  if (!ui.detailModalOpen) return
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    ui.navigatePrev()
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    ui.navigateNext()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    ui.closeDetail()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', updatePreviewLayout)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', updatePreviewLayout)
})

async function handleAlbumSelected(albumId: number) {
  if (!detail.value) return
  try {
    await addAssetToAlbum(albumId, detail.value.asset_id)
    showAlbumPicker.value = false
    alert(t('detail.addedToAlbum'))
  } catch (e: any) {
    alert(e?.response?.data?.detail || t('detail.addFailed'))
  }
}

async function handleDelete() {
  if (!detail.value) return
  const confirmed = window.confirm(t('detail.deleteConfirm', { caption: detail.value.caption_short || detail.value.rel_path }))
  if (!confirmed) return
  try {
    await deleteAsset(detail.value.asset_id)
    const deletedId = detail.value.asset_id
    ui.removeFromList(deletedId)
    ui.closeDetail()
    emit('deleted', deletedId)
  } catch (e: any) {
    alert(t('detail.deleteFailed', { error: e?.response?.data?.detail || e.message }))
  }
}

watch(() => ui.detailAssetId, async (id) => {
  if (id !== null) {
    resetPreviewState()
    detail.value = null
    context.value = null
    similar.value = []
    showAlbumPicker.value = false
    const [d, c, s] = await Promise.all([
      fetchAssetDetail(id),
      fetchAssetContext(id),
      fetchSimilarAssets(id, 8).catch(() => []),
    ])
    detail.value = d
    context.value = c
    similar.value = s
    await nextTick()
    syncPreviewFromImage()
    preloadAdjacent()
  }
})

watch(() => ui.detailModalOpen, (open) => {
  if (!open) resetPreviewState()
})

function preloadAdjacent() {
  const list = ui.detailList
  const idx = ui.detailAssetId !== null ? list.indexOf(ui.detailAssetId) : -1
  if (idx < 0) return
  const toPreload: number[] = []
  if (idx > 0) toPreload.push(list[idx - 1])
  if (idx < list.length - 1) toPreload.push(list[idx + 1])
  for (const aid of toPreload) {
    const img = new Image()
    img.src = fullImageUrl(aid)
  }
}
</script>
