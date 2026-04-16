<template>
  <div class="forum-container">
    <header class="forum-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h1>Форум</h1>
      <button @click="showCreateModal = true" class="create-btn">+ Новый пост</button>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="posts-list">
      <div v-for="post in posts" :key="post.id" class="post-card" @click="openPost(post.id)">
        <div class="post-author">
          <div class="author-avatar">
            {{ getInitials(post.author) }}
          </div>
          <div class="author-info">
            <span class="author-name">{{ post.author?.full_name || 'Пользователь' }}</span>
            <span class="post-date">{{ formatDate(post.created_at) }}</span>
          </div>
        </div>
        <h2 class="post-title">{{ post.title }}</h2>
        <p class="post-content">{{ truncate(post.content, 150) }}</p>
        <div v-if="post.media_url" class="post-media">
          <img v-if="post.media_type === 'image'" :src="post.media_url" alt="Media" />
          <video v-else-if="post.media_type === 'video'" :src="post.media_url" controls />
        </div>
        <div class="post-stats">
          <span>❤️ {{ post.likes_count }}</span>
          <span>💬 {{ post.comments_count }}</span>
        </div>
      </div>
      
      <div v-if="posts.length === 0" class="empty-state">
        Постов пока нет. Будь первым!
      </div>
    </div>

    <!-- Modal создания поста -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Новый пост</h3>
          <button @click="showCreateModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Заголовок</label>
            <input v-model="newPost.title" placeholder="Заголовок поста" class="input" />
          </div>
          <div class="form-group">
            <label>Содержание</label>
            <textarea v-model="newPost.content" placeholder="Текст поста" class="input" rows="6"></textarea>
          </div>
          <div class="form-group">
            <label>Медиа (URL)</label>
            <input v-model="newPost.media_url" placeholder="Ссылка на изображение или видео" class="input" />
            <select v-model="newPost.media_type" class="input" style="margin-top: 8px">
              <option value="">Без медиа</option>
              <option value="image">Изображение</option>
              <option value="video">Видео</option>
            </select>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showCreateModal = false" class="btn-secondary">Отмена</button>
          <button @click="createPost" :disabled="!newPost.title.trim() || !newPost.content.trim()" class="btn-primary">
            Опубликовать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { forumAPI } from '../services/api'

export default {
  name: 'Forum',
  setup() {
    const router = useRouter()
    const posts = ref([])
    const loading = ref(true)
    const showCreateModal = ref(false)
    const newPost = ref({
      title: '',
      content: '',
      media_url: '',
      media_type: '',
    })

    const loadPosts = async () => {
      try {
        const res = await forumAPI.getPosts()
        posts.value = res.data || []
      } catch (e) {
        console.error('Error loading posts:', e)
      } finally {
        loading.value = false
      }
    }

    const createPost = async () => {
      if (!newPost.value.title.trim() || !newPost.value.content.trim()) return
      try {
        await forumAPI.createPost(newPost.value)
        showCreateModal.value = false
        newPost.value = { title: '', content: '', media_url: '', media_type: '' }
        loadPosts()
      } catch (e) {
        console.error('Error creating post:', e)
        alert('Ошибка создания поста')
      }
    }

    const openPost = (postId) => {
      router.push(`/forum/post/${postId}`)
    }

    const goBack = () => {
      router.push('/')
    }

    const getInitials = (user) => {
      if (!user?.full_name) return '?'
      return user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
    }

    const truncate = (text, length) => {
      if (!text) return ''
      return text.length > length ? text.slice(0, length) + '...' : text
    }

    onMounted(loadPosts)

    return {
      posts,
      loading,
      showCreateModal,
      newPost,
      createPost,
      openPost,
      goBack,
      getInitials,
      formatDate,
      truncate,
    }
  },
}
</script>

<style scoped>
.forum-container {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-dark, #1a1a2e);
  color: var(--text-primary, #eee);
}

.forum-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--bg-card, #16213e);
  border-bottom: 1px solid var(--border-color, #333);
}

.forum-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--primary-purple-light, #a855f7);
}

.back-btn, .create-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
  transition: all 0.3s ease;
}

.create-btn {
  background: var(--primary-purple, #9333ea);
  border-color: var(--primary-purple, #9333ea);
}

.back-btn:hover, .create-btn:hover {
  background: var(--bg-card-hover, #1f2937);
}

.posts-list {
  padding: 1rem;
}

.post-card {
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  cursor: pointer;
  border: 1px solid var(--border-color, #333);
  transition: all 0.3s ease;
}

.post-card:hover {
  border-color: var(--primary-purple, #9333ea);
  transform: translateY(-2px);
}

.post-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-purple, #9333ea), var(--primary-purple-light, #a855f7));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary, #eee);
}

.post-date {
  font-size: 0.8rem;
  color: var(--text-secondary, #999);
}

.post-title {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  color: var(--text-primary, #eee);
}

.post-content {
  margin: 0 0 1rem;
  color: var(--text-secondary, #999);
  line-height: 1.5;
}

.post-media {
  margin-bottom: 1rem;
  border-radius: 8px;
  overflow: hidden;
}

.post-media img, .post-media video {
  max-width: 100%;
  max-height: 300px;
  display: block;
}

.post-stats {
  display: flex;
  gap: 1rem;
  color: var(--text-secondary, #999);
  font-size: 0.9rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary, #999);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary, #999);
}

/* Modal styles */
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
  padding: 1rem;
}

.modal-content {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
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
  color: var(--text-primary, #eee);
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

.input {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-dark, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  font-size: 1rem;
}

.input:focus {
  outline: none;
  border-color: var(--primary-purple, #9333ea);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color, #333);
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: var(--primary-purple, #9333ea);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #7c3aed;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: transparent;
  color: var(--text-secondary, #999);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary:hover {
  border-color: var(--primary-purple, #9333ea);
  color: var(--text-primary, #eee);
}
</style>