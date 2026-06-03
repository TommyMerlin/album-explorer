<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ $t('persons.title') }}</h2>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!persons.length" class="text-center py-12 text-gray-400">
      {{ $t('persons.empty') }}
    </div>
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
      <router-link
        v-for="person in persons"
        :key="person.person_id"
        :to="`/persons/${person.person_id}`"
        class="group flex flex-col items-center gap-2"
      >
        <div class="w-20 h-20 rounded-full overflow-hidden border-2 border-gray-200 dark:border-gray-600 group-hover:border-primary-400 transition-colors">
          <img
            :src="faceThumbUrl(person.representative_face_id)"
            class="w-full h-full object-cover"
          />
        </div>
        <div class="text-center">
          <p class="text-sm text-gray-700 dark:text-gray-200 line-clamp-1">
            {{ person.name || $t('persons.unnamed') }}
          </p>
          <p class="text-xs text-gray-400">{{ $t('common.photos', { count: person.face_count }) }}</p>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchPersons, faceThumbUrl, type PersonInfo } from '../api'

const persons = ref<PersonInfo[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    persons.value = await fetchPersons()
  } finally {
    loading.value = false
  }
})
</script>
