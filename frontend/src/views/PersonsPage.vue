<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ $t('persons.title') }}</h2>
      <button
        v-if="hiddenPersons.length"
        @click="showHidden = !showHidden"
        class="px-3 py-1.5 text-sm text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
      >{{ showHidden ? $t('persons.hideManage') : $t('persons.showHidden', { count: hiddenPersons.length }) }}</button>
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

    <!-- 已隐藏的人物 -->
    <div v-if="showHidden && hiddenPersons.length" class="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
      <h3 class="text-sm font-medium text-gray-500 mb-4">{{ $t('persons.hiddenTitle') }}</h3>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
        <div
          v-for="person in hiddenPersons"
          :key="person.person_id"
          class="flex flex-col items-center gap-2"
        >
          <div class="w-20 h-20 rounded-full overflow-hidden border-2 border-gray-300 dark:border-gray-500 opacity-60">
            <img
              :src="faceThumbUrl(person.representative_face_id)"
              class="w-full h-full object-cover"
            />
          </div>
          <div class="text-center">
            <p class="text-sm text-gray-500 line-clamp-1">{{ person.name || $t('persons.unnamed') }}</p>
            <div class="mt-1 flex items-center justify-center gap-2">
              <button
                @click="handleRestore(person.person_id)"
                class="text-xs text-primary-500 hover:text-primary-700"
              >{{ $t('persons.restore') }}</button>
              <button
                @click="handleHardDelete(person.person_id, person.name)"
                class="text-xs text-red-500 hover:text-red-700"
              >{{ $t('persons.deletePermanent') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchPersons, faceThumbUrl, hidePerson, deletePerson, type PersonInfo } from '../api'

const { t } = useI18n()
const persons = ref<PersonInfo[]>([])
const hiddenPersons = ref<PersonInfo[]>([])
const loading = ref(true)
const showHidden = ref(false)

async function loadAll() {
  const all = await fetchPersons(true)
  persons.value = all.filter(p => !p.hidden)
  hiddenPersons.value = all.filter(p => p.hidden)
}

async function handleRestore(personId: number) {
  await hidePerson(personId, false)
  await loadAll()
}

async function handleHardDelete(personId: number, name: string) {
  if (!window.confirm(t('persons.deletePermanentConfirm', { name: name || t('persons.unnamed') }))) return
  await deletePerson(personId)
  await loadAll()
}

onMounted(async () => {
  try {
    await loadAll()
  } finally {
    loading.value = false
  }
})
</script>
