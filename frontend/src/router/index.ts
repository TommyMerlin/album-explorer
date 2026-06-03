import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/explore',
      name: 'explore',
      component: () => import('../views/ExplorePage.vue'),
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: () => import('../views/TimelinePage.vue'),
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('../views/MapPage.vue'),
    },
    {
      path: '/clusters',
      name: 'clusters',
      component: () => import('../views/ClustersPage.vue'),
    },
    {
      path: '/clusters/:id',
      name: 'cluster-detail',
      component: () => import('../views/ClusterDetailPage.vue'),
    },
    {
      path: '/tags',
      name: 'tags',
      component: () => import('../views/TagsPage.vue'),
    },
    {
      path: '/albums',
      name: 'albums',
      component: () => import('../views/AlbumsPage.vue'),
    },
    {
      path: '/albums/:id',
      name: 'album-detail',
      component: () => import('../views/AlbumDetailPage.vue'),
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('../views/FavoritesPage.vue'),
    },
    {
      path: '/persons',
      name: 'persons',
      component: () => import('../views/PersonsPage.vue'),
    },
    {
      path: '/persons/:id',
      name: 'person-detail',
      component: () => import('../views/PersonDetailPage.vue'),
    },
    {
      path: '/search',
      redirect: to => ({ path: '/explore', query: to.query }),
    },
  ],
})

export default router
