import { createRouter, createWebHistory } from 'vue-router'
import { authAPI } from '../services/api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:chatId',
    name: 'Chat',
    component: () => import('../views/Chat.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin.vue'),
    meta: { requiresAuth: true, requiresSuperuser: true },
  },
  {
    path: '/bots',
    name: 'Bots',
    component: () => import('../views/Bots.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/forum',
    name: 'Forum',
    component: () => import('../views/Forum.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/forum/post/:postId',
    name: 'ForumPost',
    component: () => import('../views/ForumPost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/channels',
    name: 'Channels',
    component: () => import('../views/Channels.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/channels/:channelId',
    name: 'ChannelView',
    component: () => import('../views/ChannelView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/ultra',
    name: 'Ultra',
    component: () => import('../views/Ultra.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/services',
    name: 'Services',
    component: () => import('../views/Services.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Проверка аутентификации
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
    } else {
      // Проверяем валидность токена
      try {
        const user = await authAPI.getCurrentUser()
        
        if (to.meta.requiresSuperuser && !user.is_superuser) {
          next('/')
          return
        }
        
        next()
      } catch (error) {
        localStorage.removeItem('access_token')
        next('/login')
      }
    }
  } else {
    // Если пользователь уже авторизован, перенаправляем на главную
    if (token && (to.path === '/login' || to.path === '/register')) {
      try {
        await authAPI.getCurrentUser()
        next('/')
      } catch (error) {
        localStorage.removeItem('access_token')
        next()
      }
    } else {
      next()
    }
  }
})

export default router

