import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useFiltersStore = defineStore('filters', () => {
  const searchQuery = ref('')
  const selectedMonth = ref<string | null>(null)
  const selectedCity = ref<string | null>(null)
  const selectedClusterId = ref<number | null>(null)
  const selectedTag = ref<string | null>(null)

  const activeParams = computed(() => {
    const params: Record<string, any> = {}
    if (selectedMonth.value) params.month = selectedMonth.value
    if (selectedCity.value) params.city = selectedCity.value
    if (selectedClusterId.value !== null) params.cluster_id = selectedClusterId.value
    if (selectedTag.value) params.tag = selectedTag.value
    return params
  })

  const hasFilters = computed(() => {
    return !!(selectedMonth.value || selectedCity.value || selectedClusterId.value !== null || selectedTag.value)
  })

  function clearAll() {
    searchQuery.value = ''
    selectedMonth.value = null
    selectedCity.value = null
    selectedClusterId.value = null
    selectedTag.value = null
  }

  return {
    searchQuery, selectedMonth, selectedCity, selectedClusterId, selectedTag,
    activeParams, hasFilters, clearAll,
  }
})
