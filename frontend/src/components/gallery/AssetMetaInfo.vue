<template>
  <div class="space-y-3 text-sm">
    <div v-if="takenAt" class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
      </svg>
      <router-link
        :to="{ path: '/explore', query: { month: monthBucket } }"
        class="hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        @click="$emit('navigate')"
      >{{ takenAt }}</router-link>
    </div>
    <div v-if="cityName" class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
      </svg>
      <router-link
        :to="{ path: '/explore', query: { city: cityName } }"
        class="hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        @click="$emit('navigate')"
      >{{ provinceName }} {{ cityName }}</router-link>
    </div>
    <div v-if="clusterName" class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
      </svg>
      <router-link
        :to="{ path: '/explore', query: { cluster_id: String(clusterId) } }"
        class="hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        @click="$emit('navigate')"
      >{{ clusterName }}</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  takenAt?: string | null
  monthBucket?: string | null
  cityName?: string | null
  provinceName?: string | null
  clusterName?: string | null
  clusterId?: number | null
}

defineProps<Props>()
defineEmits<{ navigate: [] }>()
</script>
