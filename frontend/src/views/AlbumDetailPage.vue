<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/albums" class="text-gray-400 hover:text-gray-600">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <h2 class="text-lg font-semibold text-gray-800">{{ album?.name }}</h2>
      <span class="text-sm text-gray-400">{{ album?.asset_count }} 张</span>
      <button
        @click="handleDelete"
        class="ml-auto text-xs text-red-500 hover:text-red-700"
      >删除相册</button>
    </div>
    <p v-if="album?.description" class="text-sm text-gray-500 mb-4">{{ album.description }}</p>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!album?.items.length" class="text-center py-12 text-gray-400">
      相册为空，在图片详情中可以添加图片到此相册
    </div>
    <PhotoGrid v-else :items="album.items" />
    <PhotoDetail @deleted="onAssetDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAlbumDetail, deleteAlbum, type AlbumDetail } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const router = useRouter()
const album = ref<AlbumDetail | null>(null)
const loading = ref(true)

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
