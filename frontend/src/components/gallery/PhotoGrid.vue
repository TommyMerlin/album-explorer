<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
    <div
      v-for="asset in items"
      :key="asset.asset_id"
      class="group relative aspect-square rounded-lg overflow-hidden cursor-pointer bg-gray-100 transition-all"
      :class="[
        selectedSet.has(asset.asset_id) ? 'ring-2 ring-primary-500' : 'hover:ring-2 hover:ring-primary-400',
      ]"
      @click="handleClick(asset)"
    >
      <img
        :src="thumbnailUrl(asset.asset_id, 'sm')"
        :alt="asset.caption_short || ''"
        loading="lazy"
        decoding="async"
        class="w-full h-full object-cover transition-opacity duration-300"
        :class="loadedSet.has(asset.asset_id) ? 'opacity-100' : 'opacity-0'"
        @load="loadedSet.add(asset.asset_id)"
        @error="errorSet.add(asset.asset_id)"
      />
      <!-- 选择圆圈 -->
      <div
        v-if="selectable"
        class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors z-10"
        :class="selectedSet.has(asset.asset_id) ? 'bg-primary-500 border-primary-500' : 'border-white bg-black/20'"
        @click.stop="emit('toggle', asset.asset_id)"
      >
        <svg v-if="selectedSet.has(asset.asset_id)" class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
      <!-- 加载失败占位 -->
      <div v-if="errorSet.has(asset.asset_id)" class="absolute inset-0 flex items-center justify-center bg-gray-100">
        <div class="text-center text-gray-400">
          <svg class="w-8 h-8 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="text-[10px]">文件缺失</p>
        </div>
      </div>
      <div v-if="!selectable" class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
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

const props = withDefaults(defineProps<{
  items: AssetBrief[]
  selectable?: boolean
  selectedIds?: Set<number>
}>(), {
  selectable: false,
})

const emit = defineEmits<{ toggle: [assetId: number] }>()

const ui = useUiStore()
const loadedSet = reactive(new Set<number>())
const errorSet = reactive(new Set<number>())

const selectedSet = props.selectedIds || reactive(new Set<number>())

function handleClick(asset: AssetBrief) {
  if (props.selectable) {
    emit('toggle', asset.asset_id)
  } else {
    ui.openDetail(asset.asset_id)
  }
}
</script>
