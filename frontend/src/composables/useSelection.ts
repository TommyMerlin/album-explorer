import { reactive, computed } from 'vue'

export function useSelection() {
  const selected = reactive(new Set<number | string>())

  function toggle(id: number | string) {
    if (selected.has(id)) {
      selected.delete(id)
    } else {
      selected.add(id)
    }
  }

  function select(id: number | string) {
    selected.add(id)
  }

  function deselect(id: number | string) {
    selected.delete(id)
  }

  function clear() {
    selected.clear()
  }

  const count = computed(() => selected.size)
  const hasSelection = computed(() => selected.size > 0)
  const isSelected = (id: number | string) => selected.has(id)

  return {
    selected,
    toggle,
    select,
    deselect,
    clear,
    count,
    hasSelection,
    isSelected,
  }
}
