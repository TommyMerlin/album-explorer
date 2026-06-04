<template>
  <div v-if="items.length" class="mt-1">
    <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">{{ title }}</h4>
    <div class="grid grid-cols-4 gap-1">
      <img
        v-for="item in items.slice(0, maxItems)"
        :key="item.asset_id"
        :src="thumbnailUrl(item.asset_id, 'sm')"
        class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80 transition-opacity"
        @click="$emit('open', item.asset_id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { thumbnailUrl, type AssetBrief } from '../../api'

interface Props {
  title: string
  items: AssetBrief[]
  maxItems?: number
}

withDefaults(defineProps<Props>(), {
  maxItems: 8,
})

defineEmits<{
  open: [assetId: number]
}>()
</script>
