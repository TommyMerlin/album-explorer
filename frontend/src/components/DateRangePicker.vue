<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
    <div class="flex items-center justify-between mb-3">
      <button @click="prevMonth" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
        <svg class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <span class="text-sm font-medium text-gray-700 dark:text-gray-200">{{ displayYear }}年{{ displayMonth }}月</span>
      <button @click="nextMonth" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
        <svg class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>
    <div class="grid grid-cols-7 gap-0.5 text-center mb-1">
      <span v-for="d in weekDays" :key="d" class="text-xs text-gray-400 py-1">{{ d }}</span>
    </div>
    <div class="grid grid-cols-7 gap-0.5 text-center">
      <button
        v-for="(day, i) in calendarDays"
        :key="i"
        @click="day.date && selectDay(day.date)"
        :disabled="!day.date"
        class="py-1.5 text-xs rounded transition-colors"
        :class="dayClass(day)"
      >{{ day.label }}</button>
    </div>
    <div class="mt-3 flex items-center justify-between">
      <div class="text-xs text-gray-500 dark:text-gray-400">
        <template v-if="startDate && endDate">{{ startDate }} ~ {{ endDate }}</template>
        <template v-else-if="startDate">{{ startDate }} ~ 选择结束</template>
        <template v-else>点击选择起始日期</template>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="startDate"
          @click="clearSelection"
          class="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >清除</button>
        <button
          v-if="startDate && endDate"
          @click="confirm"
          class="px-3 py-1 text-xs bg-primary-500 text-white rounded hover:bg-primary-600"
        >查看</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{ confirm: [dateFrom: string, dateTo: string] }>()

const weekDays = ['一', '二', '三', '四', '五', '六', '日']

const now = new Date()
const viewYear = ref(now.getFullYear())
const viewMonth = ref(now.getMonth() + 1)

const startDate = ref<string | null>(null)
const endDate = ref<string | null>(null)

const displayYear = computed(() => viewYear.value)
const displayMonth = computed(() => viewMonth.value)

interface CalendarDay {
  label: string
  date: string | null
  isStart: boolean
  isEnd: boolean
  inRange: boolean
  isCurrentMonth: boolean
}

const calendarDays = computed<CalendarDay[]>(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()

  let startWeekday = firstDay.getDay()
  if (startWeekday === 0) startWeekday = 7

  const days: CalendarDay[] = []

  for (let i = 1; i < startWeekday; i++) {
    days.push({ label: '', date: null, isStart: false, isEnd: false, inRange: false, isCurrentMonth: false })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const isStart = dateStr === startDate.value
    const isEnd = dateStr === endDate.value
    const inRange = !!(startDate.value && endDate.value && dateStr > startDate.value && dateStr < endDate.value)
    days.push({ label: String(d), date: dateStr, isStart, isEnd, inRange, isCurrentMonth: true })
  }

  return days
})

function dayClass(day: CalendarDay) {
  if (!day.date) return 'text-transparent cursor-default'
  if (day.isStart || day.isEnd) return 'bg-primary-500 text-white'
  if (day.inRange) return 'bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300'
  return 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
}

function selectDay(date: string) {
  if (!startDate.value || endDate.value) {
    startDate.value = date
    endDate.value = null
  } else {
    if (date < startDate.value) {
      endDate.value = startDate.value
      startDate.value = date
    } else if (date === startDate.value) {
      endDate.value = date
    } else {
      endDate.value = date
    }
  }
}

function clearSelection() {
  startDate.value = null
  endDate.value = null
}

function confirm() {
  if (startDate.value && endDate.value) {
    emit('confirm', startDate.value, endDate.value)
  }
}

function prevMonth() {
  if (viewMonth.value === 1) {
    viewMonth.value = 12
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 12) {
    viewMonth.value = 1
    viewYear.value++
  } else {
    viewMonth.value++
  }
}
</script>
