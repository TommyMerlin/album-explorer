<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[10001] flex items-center justify-center bg-black/50"
      @click.self="emit('close')"
    >
      <div class="bg-white rounded-xl w-80 max-h-[60vh] overflow-hidden shadow-xl">
        <div class="p-4 border-b border-gray-100">
          <h3 class="text-base font-medium text-gray-800">添加到相册</h3>
          <p class="text-xs text-gray-400 mt-1">选择已有相册或创建新相册</p>
        </div>
        <div class="max-h-[40vh] overflow-y-auto">
          <button
            v-for="album in albums"
            :key="album.id"
            @click="selectAlbum(album.id)"
            class="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-50 flex items-center gap-3"
          >
            <img
              v-if="album.cover_asset_id"
              :src="thumbnailUrl(album.cover_asset_id, 'sm')"
              class="w-10 h-10 rounded object-cover"
            />
            <div v-else class="w-10 h-10 rounded bg-gray-100 flex items-center justify-center">
              <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </div>
            <div>
              <p class="text-sm text-gray-800">{{ album.name }}</p>
              <p class="text-xs text-gray-400">{{ album.asset_count }} 张</p>
            </div>
          </button>
          <div v-if="!albums.length" class="px-4 py-6 text-center text-sm text-gray-400">
            暂无相册
          </div>
        </div>
        <div class="p-3 border-t border-gray-100">
          <div class="flex gap-2">
            <input
              v-model="newName"
              @keydown.enter="createNew"
              placeholder="输入新相册名称..."
              class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
            <button
              @click="createNew"
              :disabled="!newName.trim()"
              class="px-3 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-40"
            >创建</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { fetchAlbums, createAlbum, thumbnailUrl, type Album } from '../api'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [], select: [albumId: number] }>()

const albums = ref<Album[]>([])
const newName = ref('')

watch(() => props.visible, async (v) => {
  if (v) {
    albums.value = await fetchAlbums().catch(() => [])
    newName.value = ''
  }
})

function selectAlbum(id: number) {
  emit('select', id)
}

async function createNew() {
  if (!newName.value.trim()) return
  const album = await createAlbum(newName.value.trim())
  emit('select', album.id)
}
</script>
