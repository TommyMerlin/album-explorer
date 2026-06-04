import { ref, computed } from 'vue'

export function usePagination(fetchFn: (page: number) => Promise<{ total_pages: number }>) {
  const page = ref(1)
  const totalPages = ref(1)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const result = await fetchFn(page.value)
      totalPages.value = result.total_pages
      return result
    } finally {
      loading.value = false
    }
  }

  async function next() {
    if (page.value < totalPages.value) {
      page.value++
      return load()
    }
  }

  async function prev() {
    if (page.value > 1) {
      page.value--
      return load()
    }
  }

  function reset() {
    page.value = 1
    totalPages.value = 1
  }

  const hasPrev = computed(() => page.value > 1)
  const hasNext = computed(() => page.value < totalPages.value)

  return { page, totalPages, loading, load, next, prev, reset, hasPrev, hasNext }
}
