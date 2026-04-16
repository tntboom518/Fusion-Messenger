<template>
  <div class="post-view-container">
    <header class="post-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <button v-if="isAuthor" @click="deletePost" class="delete-btn">🗑️ Удалить</button>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="post" class="post-content">
      <div class="post-author">
        <div class="author-avatar">{{ getInitials(post.author) }}</div>
        <div class="author-info">
          <span class="author-name">{{ post.author?.full_name || 'Пользователь' }}</span>
          <span class="post-date">{{ formatDate(post.created_at) }}</span>
        </div>
      </div>
      
      <h1 class="post-title">{{ post.title }}</h1>
      <p class="post-text">{{ post.content }}</p>
      
      <div v-if="post.media_url" class="post-media">
        <img v-if="post.media_type === 'image'" :src="post.media_url" alt="Media" />
        <video v-else-if="post.media_type === 'video'" :src="post.media_url" controls />
      </div>
      
      <div class="post-actions">
        <button @click="likePost" class="action-btn">❤️ {{ post.likes_count }}</button>
      </div>

      <!-- Comments section -->
      <div class="comments-section">
        <h3>Комментарии ({{ comments.length }})</h3>
        
        <div class="comment-form">
          <textarea v-model="newComment" placeholder="Написать комментарий..." class="input" rows="3"></textarea>
          <button @click="addComment" :disabled="!newComment.trim()" class="btn-primary">Отправить</button>
        </div>

        <div class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment">
            <div class="comment-author">
              <div class="author-avatar small">{{ getInitials(comment.author) }}</div>
              <span class="author-name">{{ comment.author?.full_name || 'Пользователь' }}</span>
              <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
            </div>
            <p class="comment-text">{{ comment.content }}</p>
            <button v-if="comment.author_id === currentUserId" @click="deleteComment(comment.id)" class="delete-comment-btn">×</button>
          </div>
          
          <div v-if="comments.length === 0" class="empty-comments">
            Пока нет комментариев. Будь первым!
          </div>
        </div>
      </div>
    </div>
    <div v-else class="error">Пост не найден</div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumAPI, authAPI } from '../services/api'

export default {
  name: 'ForumPost',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const post = ref(null)
    const comments = ref([])
    const loading = ref(true)
    const newComment = ref('')
    const currentUserId = ref(null)

    const isAuthor = computed(() => post.value && currentUserId.value && post.value.author_id === currentUserId.value)

    const loadPost = async () => {
      try {
        const user = await authAPI.getCurrentUser()
        currentUserId.value = user.id
        
        const postRes = await forumAPI.getPost(route.params.postId)
        post.value = postRes
        
        const commentsRes = await forumAPI.getComments(route.params.postId)
        comments.value = commentsRes.data || []
      } catch (e) {
        console.error('Error loading post:', e)
      } finally {
        loading.value = false
      }
    }

    const likePost = async () => {
      try {
        const res = await forumAPI.likePost(post.value.id)
        post.value.likes_count = res.likes_count
      } catch (e) {
        console.error('Error liking post:', e)
      }
    }

    const addComment = async () => {
      if (!newComment.value.trim()) return
      try {
        const res = await forumAPI.createComment(post.value.id, newComment.value.trim())
        comments.value.push(res)
        post.value.comments_count++
        newComment.value = ''
      } catch (e) {
        console.error('Error adding comment:', e)
        alert('Ошибка добавления комментария')
      }
    }

    const deleteComment = async (commentId) => {
      if (!confirm('Удалить комментарий?')) return
      try {
        await forumAPI.deleteComment(commentId)
        comments.value = comments.value.filter(c => c.id !== commentId)
        post.value.comments_count--
      } catch (e) {
        console.error('Error deleting comment:', e)
      }
    }

    const deletePost = async () => {
      if (!confirm('Удалить пост?')) return
      try {
        await forumAPI.deletePost(post.value.id)
        router.push('/forum')
      } catch (e) {
        console.error('Error deleting post:', e)
      }
    }

    const goBack = () => {
      router.push('/forum')
    }

    const getInitials = (user) => {
      if (!user?.full_name) return '?'
      return user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    }

    onMounted(loadPost)

    return {
      post,
      comments,
      loading,
      newComment,
      currentUserId,
      isAuthor,
      likePost,
      addComment,
      deleteComment,
      deletePost,
      goBack,
      getInitials,
      formatDate,
    }
  },
}
</script>

<style scoped>
.post-view-container {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-dark, #1a1a2e);
  color: var(--text-primary, #eee);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--bg-card, #16213e);
  border-bottom: 1px solid var(--border-color, #333);
}

.back-btn, .delete-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
}

.delete-btn {
  background: #dc2626;
  border-color: #dc2626;
}

.post-content {
  padding: 1.5rem;
}

.post-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-purple, #9333ea), var(--primary-purple-light, #a855f7));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.author-avatar.small {
  width: 32px;
  height: 32px;
  font-size: 0.8rem;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
}

.post-date {
  font-size: 0.8rem;
  color: var(--text-secondary, #999);
}

.post-title {
  font-size: 2rem;
  margin: 0 0 1rem;
  color: var(--text-primary, #eee);
}

.post-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: var(--text-secondary, #bbb);
  white-space: pre-wrap;
}

.post-media {
  margin: 1.5rem 0;
  border-radius: 12px;
  overflow: hidden;
}

.post-media img, .post-media video {
  max-width: 100%;
  display: block;
}

.post-actions {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color, #333);
  margin-bottom: 2rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
  font-size: 1rem;
}

.action-btn:hover {
  border-color: var(--primary-purple, #9333ea);
}

.comments-section h3 {
  margin-bottom: 1rem;
  color: var(--primary-purple-light, #a855f7);
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.input {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-card, #16213e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  font-size: 1rem;
  resize: vertical;
}

.input:focus {
  outline: none;
  border-color: var(--primary-purple, #9333ea);
}

.btn-primary {
  align-self: flex-end;
  padding: 0.75rem 1.5rem;
  background: var(--primary-purple, #9333ea);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.comment {
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  padding: 1rem;
  position: relative;
  border: 1px solid var(--border-color, #333);
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.comment-date {
  font-size: 0.75rem;
  color: var(--text-secondary, #999);
  margin-left: auto;
}

.comment-text {
  margin: 0;
  color: var(--text-secondary, #bbb);
}

.delete-comment-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: var(--text-secondary, #999);
  font-size: 1.25rem;
  cursor: pointer;
}

.delete-comment-btn:hover {
  color: #dc2626;
}

.empty-comments {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary, #999);
}

.loading, .error {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary, #999);
}
</style>