import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchFavoriteIds, addFavorite, removeFavorite } from '@/api'

export const useFavoritesStore = defineStore('favorites', () => {
  const ids = ref<Set<number>>(new Set())
  const loaded = ref(false)

  async function load() {
    const list = await fetchFavoriteIds()
    ids.value = new Set(list)
    loaded.value = true
  }

  function isFavorite(assetId: number): boolean {
    return ids.value.has(assetId)
  }

  async function toggle(assetId: number) {
    if (ids.value.has(assetId)) {
      ids.value.delete(assetId)
      await removeFavorite(assetId)
    } else {
      ids.value.add(assetId)
      await addFavorite(assetId)
    }
  }

  return { ids, loaded, load, isFavorite, toggle }
})
