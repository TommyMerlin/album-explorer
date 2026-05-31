<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
    <div
      v-for="asset in items"
      :key="asset.asset_id"
      class="group relative aspect-square rounded-lg overflow-hidden cursor-pointer bg-gray-100 hover:ring-2 hover:ring-primary-400 transition-all"
      @click="ui.openDetail(asset.asset_id)"
    >
      <img
        :src="thumbnailUrl(asset.asset_id, 'sm')"
        :alt="asset.caption_short || ''"
        loading="lazy"
        decoding="async"
        class="w-full h-full object-cover transition-opacity duration-300"
        :class="loadedSet.has(asset.asset_id) ? 'opacity-100' : 'opacity-0'"
        @load="loadedSet.add(asset.asset_id)"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
        <div class="absolute bottom-0 left-0 right-0 p-2">
          <p class="text-white text-xs line-clamp-2">{{ asset.caption_short }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { AssetBrief } from '../../api'
import { thumbnailUrl } from '../../api'
import { useUiStore } from '../../stores/ui'

defineProps<{
  items: AssetBrief[]
}>()

const ui = useUiStore()
const loadedSet = reactive(new Set<number>())
</script>
