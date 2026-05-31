import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AssetBrief, AssetDetail } from '../api'
import { fetchAssets, fetchAssetDetail } from '../api'

export const useAssetsStore = defineStore('assets', () => {
  const items = ref<AssetBrief[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(50)
  const totalPages = ref(1)
  const loading = ref(false)
  const currentDetail = ref<AssetDetail | null>(null)

  async function load(params: Record<string, any> = {}) {
    loading.value = true
    try {
      const res = await fetchAssets({ page: page.value, page_size: pageSize.value, ...params })
      items.value = res.items
      total.value = res.total
      totalPages.value = res.total_pages
    } finally {
      loading.value = false
    }
  }

  async function loadMore(params: Record<string, any> = {}) {
    if (page.value >= totalPages.value) return
    loading.value = true
    try {
      page.value++
      const res = await fetchAssets({ page: page.value, page_size: pageSize.value, ...params })
      items.value.push(...res.items)
    } finally {
      loading.value = false
    }
  }

  async function loadDetail(id: number) {
    currentDetail.value = await fetchAssetDetail(id)
  }

  function reset() {
    items.value = []
    total.value = 0
    page.value = 1
    totalPages.value = 1
  }

  return { items, total, page, pageSize, totalPages, loading, currentDetail, load, loadMore, loadDetail, reset }
})
