import { reactive, onMounted, onUnmounted } from 'vue'

export type KeyBinding = {
  key: string
  ctrl?: boolean
  shift?: boolean
  handler: () => void
}

export function useKeyboard(bindings: KeyBinding[]) {
  const activeKeys = reactive(new Set<string>())

  function handleKeydown(e: KeyboardEvent) {
    activeKeys.add(e.key)
    for (const binding of bindings) {
      if (binding.key !== e.key) continue
      if (binding.ctrl && !e.ctrlKey) continue
      if (binding.shift && !e.shiftKey) continue
      e.preventDefault()
      binding.handler()
      break
    }
  }

  function handleKeyup(e: KeyboardEvent) {
    activeKeys.delete(e.key)
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
    window.addEventListener('keyup', handleKeyup)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
    window.removeEventListener('keyup', handleKeyup)
  })

  return { activeKeys }
}
