<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800">我的相册</h2>
      <button
        @click="handleCreate"
        class="px-3 py-1.5 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600"
      >新建相册</button>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!albums.length" class="text-center py-12 text-gray-400">
      还没有相册，点击上方按钮创建一个
    </div>
    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <router-link
        v-for="album in albums"
        :key="album.id"
        :to="`/albums/${album.id}`"
        class="group bg-white rounded-xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
      >
        <div class="aspect-[4/3] bg-gray-100 overflow-hidden">
          <img
            v-if="album.cover_asset_id"
            :src="thumbnailUrl(album.cover_asset_id, 'md')"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
            <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
        </div>
        <div class="p-3">
          <h3 class="text-sm font-medium text-gray-800 line-clamp-1">{{ album.name }}</h3>
          <p class="text-xs text-gray-400 mt-1">{{ album.asset_count }} 张</p>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchAlbums, createAlbum, thumbnailUrl, type Album } from '../api'

const albums = ref<Album[]>([])
const loading = ref(true)

async function handleCreate() {
  const name = prompt('相册名称：')
  if (!name) return
  await createAlbum(name)
  albums.value = await fetchAlbums()
}

onMounted(async () => {
  try {
    albums.value = await fetchAlbums()
  } finally {
    loading.value = false
  }
})
</script>
