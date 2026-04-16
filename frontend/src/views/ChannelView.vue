<template>
  <div class="channel-view-container">
    <header class="channel-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <div class="channel-title">
        <div class="channel-avatar">{{ getInitials(channel?.name) }}</div>
        <div>
          <h1>{{ channel?.name }}</h1>
          <p class="channel-desc">{{ channel?.description }}</p>
        </div>
      </div>
      <div v-if="channel?.is_creator" class="header-actions">
        <button @click="showAddAdminModal = true" class="action-btn">👥 Добавить админа</button>
        <button @click="deleteChannel" class="delete-btn">🗑️</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="channel-content">
      <!-- Форма создания поста (только для админов) -->
      <div v-if="channel?.is_admin" class="post-form">
        <textarea v-model="newPost" placeholder="Написать пост в канале..." class="input" rows="3"></textarea>
        <div class="post-form-actions">
          <button @click="createPost" :disabled="!newPost.trim()" class="btn-primary">Опубликовать</button>
        </div>
      </div>
      <div v-else class="no-post-permission">
        Только создатель и админы могут публиковать посты
      </div>

      <!-- Список постов -->
      <div class="posts-list">
        <div v-for="post in posts" :key="post.id" class="post-card">
          <div class="post-header">
            <div class="author-avatar">{{ getInitials(post.author) }}</div>
            <div class="author-info">
              <span class="author-name">{{ post.author?.full_name || 'Пользователь' }}</span>
              <span class="post-date">{{ formatDate(post.created_at) }}</span>
            </div>
            <button v-if="canDeletePost(post)" @click="deletePost(post.id)" class="delete-post-btn">🗑️</button>
          </div>
          <p class="post-content">{{ post.content }}</p>
          <div v-if="post.media_url" class="post-media">
            <img v-if="post.media_type === 'image'" :src="post.media_url" alt="Media" />
            <video v-else-if="post.media_type === 'video'" :src="post.media_url" controls />
          </div>
        </div>
        
        <div v-if="posts.length === 0" class="empty-state">
          В канале пока нет постов
        </div>
      </div>
    </div>

    <!-- Modal добавления админа -->
    <div v-if="showAddAdminModal" class="modal-overlay" @click.self="showAddAdminModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Добавить админа</h3>
          <button @click="showAddAdminModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Поиск пользователя</label>
            <input v-model="userSearch" @input="searchUsers" placeholder="Введите имя или email..." class="input" />
          </div>
          <div v-if="searchResults.length > 0" class="search-results">
            <div v-for="user in searchResults" :key="user.id" class="search-result-item" @click="addAdmin(user.id)">
              <div class="user-avatar">{{ getInitials(user) }}</div>
              <span>{{ user.full_name || user.email }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { channelsAPI, usersAPI, authAPI } from '../services/api'

export default {
  name: 'ChannelView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const channel = ref(null)
    const posts = ref([])
    const loading = ref(true)
    const newPost = ref('')
    const currentUserId = ref(null)
    const showAddAdminModal = ref(false)
    const userSearch = ref('')
    const searchResults = ref([])

    const loadChannel = async () => {
      try {
        const user = await authAPI.getCurrentUser()
        currentUserId.value = user.id
        
        const channelRes = await channelsAPI.getChannel(route.params.channelId)
        channel.value = channelRes
        
        const postsRes = await channelsAPI.getPosts(route.params.channelId)
        posts.value = postsRes.data || []
      } catch (e) {
        console.error('Error loading channel:', e)
      } finally {
        loading.value = false
      }
    }

    const createPost = async () => {
      if (!newPost.value.trim()) return
      try {
        const res = await channelsAPI.createPost(route.params.channelId, {
          content: newPost.value.trim()
        })
        posts.value.unshift(res)
        newPost.value = ''
      } catch (e) {
        console.error('Error creating post:', e)
        alert('Ошибка публикации поста')
      }
    }

    const deletePost = async (postId) => {
      if (!confirm('Удалить пост?')) return
      try {
        await channelsAPI.deletePost(postId)
        posts.value = posts.value.filter(p => p.id !== postId)
      } catch (e) {
        console.error('Error deleting post:', e)
      }
    }

    const canDeletePost = (post) => {
      if (!channel.value) return false
      if (post.author_id === currentUserId.value) return true
      if (channel.value.is_admin) return true
      return false
    }

    const deleteChannel = async () => {
      if (!confirm('Удалить канал?')) return
      try {
        await channelsAPI.deleteChannel(route.params.channelId)
        router.push('/channels')
      } catch (e) {
        console.error('Error deleting channel:', e)
      }
    }

    const searchUsers = async () => {
      if (userSearch.value.trim().length < 2) {
        searchResults.value = []
        return
      }
      try {
        const res = await usersAPI.search(userSearch.value)
        searchResults.value = (res.data || []).filter(u => u.id !== currentUserId.value)
      } catch (e) {
        console.error('Error searching users:', e)
      }
    }

    const addAdmin = async (userId) => {
      try {
        const res = await channelsAPI.addAdmin(route.params.channelId, userId)
        channel.value = res
        showAddAdminModal.value = false
        userSearch.value = ''
        searchResults.value = []
      } catch (e) {
        console.error('Error adding admin:', e)
        alert('Ошибка добавления админа')
      }
    }

    const goBack = () => {
      router.push('/channels')
    }

    const getInitials = (obj) => {
      if (!obj) return '?'
      const name = obj.full_name || obj.name || obj.email || ''
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    }

    onMounted(loadChannel)

    return {
      channel,
      posts,
      loading,
      newPost,
      showAddAdminModal,
      userSearch,
      searchResults,
      createPost,
      deletePost,
      canDeletePost,
      deleteChannel,
      searchUsers,
      addAdmin,
      goBack,
      getInitials,
      formatDate,
    }
  },
}
</script>

<style scoped>
.channel-view-container {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-dark, #1a1a2e);
  color: var(--text-primary, #eee);
}

.channel-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--bg-card, #16213e);
  border-bottom: 1px solid var(--border-color, #333);
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
}

.channel-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.channel-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary-purple, #9333ea), var(--primary-purple-light, #a855f7));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
}

.channel-title h1 {
  margin: 0;
  font-size: 1.25rem;
}

.channel-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary, #999);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn, .delete-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
  font-size: 0.9rem;
}

.delete-btn {
  background: #dc2626;
  border-color: #dc2626;
}

.channel-content {
  padding: 1rem;
}

.post-form {
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border-color, #333);
}

.input {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-dark, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  resize: vertical;
}

.input:focus {
  outline: none;
  border-color: var(--primary-purple, #9333ea);
}

.post-form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.btn-primary {
  padding: 0.5rem 1.5rem;
  background: var(--primary-purple, #9333ea);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:disabled {
  opacity: 0.5;
}

.no-post-permission {
  text-align: center;
  padding: 1rem;
  color: var(--text-secondary, #999);
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  margin-bottom: 1rem;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-card {
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid var(--border-color, #333);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.author-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-purple, #9333ea), var(--primary-purple-light, #a855f7));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.8rem;
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.post-date {
  font-size: 0.75rem;
  color: var(--text-secondary, #999);
}

.delete-post-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  opacity: 0.5;
}

.delete-post-btn:hover {
  opacity: 1;
}

.post-content {
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.post-media {
  margin-top: 1rem;
  border-radius: 8px;
  overflow: hidden;
}

.post-media img, .post-media video {
  max-width: 100%;
  display: block;
}

.empty-state, .loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary, #999);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border-color, #333);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color, #333);
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary, #999);
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary, #999);
}

.search-results {
  max-height: 200px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.search-result-item:hover {
  background: var(--bg-dark, #1a1a2e);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary-purple, #9333ea);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>