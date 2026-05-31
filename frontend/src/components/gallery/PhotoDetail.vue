<template>
  <Teleport to="body">
    <div
      v-if="ui.detailModalOpen"
      class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70"
      @click.self="ui.closeDetail()"
    >
      <div class="relative bg-white rounded-2xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-hidden flex">
        <!-- 图片区域 -->
        <div class="flex-1 bg-gray-900 flex items-center justify-center min-h-[400px]">
          <img
            v-if="detail"
            :src="fullImageUrl(detail.asset_id)"
            :alt="detail.caption_short || ''"
            class="max-w-full max-h-[85vh] object-contain"
          />
          <div v-else class="text-white">加载中...</div>
        </div>
        <!-- 信息面板 -->
        <div v-if="detail" class="w-80 p-5 overflow-y-auto border-l border-gray-200">
          <button @click="ui.closeDetail()" class="absolute top-3 right-3 p-1 hover:bg-gray-100 rounded-full">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h3 class="text-base font-medium mb-3">{{ detail.caption_short }}</h3>
          <p class="text-sm text-gray-600 mb-4">{{ detail.caption_long }}</p>

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
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">标签</h4>
            <div class="flex flex-wrap gap-1.5">
              <router-link
                v-for="tag in detail.tags"
                :key="tag"
                :to="{ path: '/explore', query: { tag } }"
                class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-primary-50 hover:text-primary-700"
                @click="ui.closeDetail()"
              >{{ tag }}</router-link>
            </div>
          </div>

          <div v-if="detail.activities.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">活动</h4>
            <p class="text-sm text-gray-600">{{ detail.activities.join('、') }}</p>
          </div>

          <div v-if="detail.main_subjects.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">主体</h4>
            <p class="text-sm text-gray-600">{{ detail.main_subjects.join('、') }}</p>
          </div>

          <!-- 上下文探索区块 -->
          <div v-if="context || similar.length" class="mt-4 pt-3 border-t border-gray-100 space-y-4">
            <div v-if="similar.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">相似图片</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in similar.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                />
              </div>
            </div>
            <div v-if="context && context.same_cluster.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">同主题「{{ context.cluster_name }}」</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in context.same_cluster.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                />
              </div>
            </div>
            <div v-if="context && context.shared_tags.length">
              <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">相关图片</h4>
              <div class="grid grid-cols-4 gap-1">
                <img
                  v-for="item in context.shared_tags.slice(0, 8)"
                  :key="item.asset_id"
                  :src="thumbnailUrl(item.asset_id, 'sm')"
                  class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
                  @click="ui.openDetail(item.asset_id)"
                />
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-100">
            <p class="text-xs text-gray-400 break-all mb-3">{{ detail.rel_path }}</p>
            <div class="space-y-2">
              <button
                @click="showAlbumPicker = !showAlbumPicker"
                class="w-full px-3 py-1.5 text-sm text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors"
              >添加到相册</button>
              <div v-if="showAlbumPicker" class="border border-gray-200 rounded-lg p-2 space-y-1">
                <div v-if="!albumList.length" class="text-xs text-gray-400 text-center py-2">暂无相册</div>
                <button
                  v-for="a in albumList"
                  :key="a.id"
                  @click="handleAddToAlbum(a.id)"
                  class="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                >{{ a.name }}</button>
                <button
                  @click="handleCreateAndAdd"
                  class="w-full text-left px-2 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded"
                >+ 新建相册</button>
              </div>
              <button
                @click="handleDelete"
                class="w-full px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >删除图片</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'
import { useUiStore } from '../../stores/ui'
import { fetchAssetDetail, fetchAssetContext, fetchSimilarAssets, deleteAsset, fetchAlbums, createAlbum, addAssetToAlbum, fullImageUrl, thumbnailUrl, type AssetDetail, type AssetContext, type AssetBrief, type Album } from '../../api'

const emit = defineEmits<{ deleted: [assetId: number] }>()

const ui = useUiStore()
const detail = ref<AssetDetail | null>(null)
const context = ref<AssetContext | null>(null)
const similar = ref<AssetBrief[]>([])
const showAlbumPicker = ref(false)
const albumList = ref<Album[]>([])

async function handleAddToAlbum(albumId: number) {
  if (!detail.value) return
  try {
    await addAssetToAlbum(albumId, detail.value.asset_id)
    showAlbumPicker.value = false
    alert('已添加到相册')
  } catch (e: any) {
    alert(e?.response?.data?.detail || '添加失败')
  }
}

async function handleCreateAndAdd() {
  const name = prompt('新相册名称：')
  if (!name || !detail.value) return
  const album = await createAlbum(name)
  await addAssetToAlbum(album.id, detail.value.asset_id)
  showAlbumPicker.value = false
  albumList.value = await fetchAlbums()
  alert('已创建相册并添加')
}

async function handleDelete() {
  if (!detail.value) return
  const confirmed = window.confirm(`确定要删除这张图片吗？\n${detail.value.caption_short || detail.value.rel_path}\n\n原图将移到回收站。`)
  if (!confirmed) return
  try {
    await deleteAsset(detail.value.asset_id)
    const deletedId = detail.value.asset_id
    ui.closeDetail()
    emit('deleted', deletedId)
  } catch (e: any) {
    alert('删除失败：' + (e?.response?.data?.detail || e.message))
  }
}

watch(() => ui.detailAssetId, async (id) => {
  if (id !== null) {
    detail.value = null
    context.value = null
    similar.value = []
    showAlbumPicker.value = false
    const [d, c, s, albums] = await Promise.all([
      fetchAssetDetail(id),
      fetchAssetContext(id),
      fetchSimilarAssets(id, 8).catch(() => []),
      fetchAlbums().catch(() => []),
    ])
    detail.value = d
    context.value = c
    similar.value = s
    albumList.value = albums
  }
})
</script>
