<template>
  <div class="home-container">
    <header class="header">
      <h1>Fusion</h1>
      <div class="header-actions">
        <button v-if="activeSeason" @click="showSeasonModal = true" class="season-btn">
          🏆 {{ activeSeason.name }}
        </button>
        <router-link v-if="currentUser && currentUser.is_superuser" to="/admin" class="admin-link">⚙️</router-link>
        <router-link to="/forum" class="forum-link">📋</router-link>
        <router-link to="/channels" class="channels-link">📢</router-link>
        <router-link to="/bots" class="bots-link">🤖</router-link>
        <router-link to="/profile" class="profile-link">👤</router-link>
        <button @click="handleLogout" class="logout-btn">Выйти</button>
      </div>
    </header>

    <!-- Сезон модальное окно -->
    <div v-if="showSeasonModal" class="modal-overlay" @click.self="showSeasonModal = false">
      <div class="season-modal">
        <h2>🏆 {{ activeSeason?.name }}</h2>
        <div class="season-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: (seasonProgress.progress * 10) + '%' }"></div>
          </div>
          <span>Прогресс: {{ seasonProgress.progress }}/10 заданий</span>
          <span>Заработано: {{ seasonProgress.total_reward_earned }} шекелей</span>
        </div>
        <div class="season-tasks">
          <h3>Задания сезона</h3>
          <div v-for="task in seasonTasks" :key="task.id" class="task-item">
            <div class="task-info">
              <strong>{{ task.name }}</strong>
              <p>{{ task.description || 'Выполните это задание' }}</p>
              <span class="task-target">Прогресс: {{ task.current_progress }}/{{ task.target_count }}</span>
            </div>
            <div class="task-reward">
              <span>Награда: {{ task.base_reward }}+ шекелей</span>
              <button 
                v-if="!task.is_completed"
                @click="claimTask(task.id)"
                class="claim-btn"
                :disabled="task.current_progress < task.target_count"
              >
                {{ task.current_progress >= task.target_count ? 'Получить' : 'В процессе' }}
              </button>
              <span v-else class="completed-badge">Выполнено</span>
            </div>
          </div>
        </div>
        <button @click="showSeasonModal = false" class="close-btn">Закрыть</button>
      </div>
    </div>

    <div class="content">
      <div class="search-section">
        <div class="section-header">
          <h2>Поиск пользователей</h2>
          <button @click="showCreateGroup = true" class="create-group-btn" title="Создать групповой чат">
            <span>+</span> Группа
          </button>
        </div>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Введите email или имя..."
            @input="handleSearch"
          />
          <div v-if="searching" class="loading">Поиск...</div>
          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="item in searchResults"
              :key="item.id"
              class="user-item"
              @click="item.type === 'bot' ? startChatWithBot(item) : startChat(item)"
            >
              <div class="user-info">
                <span v-if="item.type === 'bot'" class="type-badge">🤖</span>
                <strong>{{ item.name || item.full_name || item.email }}</strong>
                <span v-if="item.type === 'bot'" class="bot-badge">Бот</span>
                <span v-else class="user-email">{{ item.email }}</span>
              </div>
              <button class="chat-btn">{{ item.type === 'bot' ? 'Чат' : 'Написать' }}</button>
            </div>
          </div>
          <div v-if="searchQuery && !searching && searchResults.length === 0" class="no-results">
            Пользователи и боты не найдены
          </div>
        </div>
      </div>

      <div class="chats-section">
        <h2>Мои чаты</h2>
        <div v-if="loadingChats" class="loading">Загрузка чатов...</div>
        <div v-else-if="chats.length === 0" class="no-chats">
          У вас пока нет чатов. Найдите пользователя и начните переписку!
        </div>
        <div v-else class="chats-list">
          <div
            v-for="chat in chats.filter(c => c.chat_type !== 'bot')"
            :key="chat.id"
            class="chat-item"
            :class="{ 'group-chat': chat.chat_type === 'group' }"
            @click="openChat(chat.id)"
          >
            <div class="avatar-wrapper">
              <img 
                v-if="getChatAvatar(chat)" 
                :src="getChatAvatar(chat)" 
                class="chat-avatar" 
              />
              <div v-else class="chat-avatar-placeholder">
                {{ getChatInitials(chat) }}
              </div>
              <span v-if="chat.chat_type === 'private' && getOtherMemberUserId(chat) && isUserOnline(getOtherMemberUserId(chat))" class="online-indicator"></span>
            </div>
            <div class="chat-info">
              <div class="chat-name-row">
                <strong>{{ getChatName(chat) }}</strong>
                <span v-if="chat.chat_type === 'group'" class="group-badge">Группа</span>
                <span v-if="chat.chat_type === 'bot'" class="bot-badge">Бот</span>
                <span v-if="isOtherMemberUltra(chat)" class="ultra-badge">⚡</span>
              </div>
              <span v-if="chat.last_message" class="last-message">
                {{ chat.last_message.content }}
              </span>
            </div>
            <span v-if="chat.last_message" class="chat-time">
              {{ formatTime(chat.last_message.created_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания группового чата -->
    <div v-if="showCreateGroup" class="modal-overlay" @click.self="showCreateGroup = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Создать групповой чат</h3>
          <button @click="showCreateGroup = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Название группы:</label>
            <input
              v-model="newGroupName"
              type="text"
              placeholder="Введите название группы"
              maxlength="50"
            />
          </div>
          <div class="form-group">
            <label>Поиск участников:</label>
            <input
              v-model="groupMemberSearch"
              type="text"
              placeholder="Начните вводить имя или email..."
              @input="handleGroupMemberSearch"
            />
            <div v-if="groupSearchResults.length > 0" class="member-search-results">
              <div
                v-for="user in groupSearchResults"
                :key="user.id"
                class="member-item"
                @click="toggleGroupMember(user)"
              >
                <div class="member-info">
                  <strong>{{ user.full_name || user.email }}</strong>
                  <span class="member-email">{{ user.email }}</span>
                </div>
                <div class="checkbox" :class="{ checked: isMemberSelected(user.id) }">
                  {{ isMemberSelected(user.id) ? '✓' : '' }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="selectedMembers.length > 0" class="selected-members">
            <div class="selected-label">Выбранные участники ({{ selectedMembers.length }}):</div>
            <div class="selected-tags">
              <span
                v-for="member in selectedMembers"
                :key="member.id"
                class="member-tag"
              >
                {{ member.full_name || member.email }}
                <button @click="removeMember(member.id)" class="remove-member">×</button>
              </span>
            </div>
          </div>
          <div v-if="groupError" class="error">{{ groupError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateGroup = false" class="cancel-btn">Отмена</button>
          <button
            @click="createGroupChat"
            :disabled="!newGroupName.trim() || selectedMembers.length === 0 || creatingGroup"
            class="create-btn"
          >
            {{ creatingGroup ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, chatsAPI, botsAPI } from '../services/api'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const searchQuery = ref('')
    const searchResults = ref([])
    const searching = ref(false)
    let searchTimeout = null
    const chats = ref([])
    const loadingChats = ref(false)
    const currentUser = ref(null)
    const showCreateGroup = ref(false)
    const newGroupName = ref('')
    const groupMemberSearch = ref('')
    const groupSearchResults = ref([])
    const selectedMembers = ref([])
    const creatingGroup = ref(false)
    const groupError = ref('')
    const activeSeason = ref(null)
    const seasonProgress = ref({ progress: 0, completed_tasks: [], total_reward_earned: 0 })
    const seasonTasks = ref([])
    const showSeasonModal = ref(false)
    const onlineUsers = ref(new Set())

    const initWebSocket = () => {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? `${protocol}//localhost:8000/api/v1/ws/0?token=${token}`
        : `${protocol}//${window.location.host}/api/v1/ws/0?token=${token}`

      try {
        ws.value = new WebSocket(wsUrl)

        ws.value.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'online_users' && data.users) {
              onlineUsers.value = new Set(data.users)
            } else if (data.type === 'user_online') {
              onlineUsers.value.add(data.user_id)
            } else if (data.type === 'user_offline') {
              onlineUsers.value.delete(data.user_id)
            }
          } catch (e) {}
        }

        ws.value.onerror = () => {}
        ws.value.onclose = () => {}
        ws.value.onopen = () => {}
      } catch (e) {
        console.log('WS error:', e)
      }
    }

    const isUserOnline = (userId) => onlineUsers.value.has(userId)

    const handleSearch = async () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }

      // Clear previous timeout
      if (searchTimeout) clearTimeout(searchTimeout)
      
      searchTimeout = setTimeout(async () => {
        searching.value = true
        searchResults.value = []
        
        try {
          console.log('=== SEARCH START ===')
          console.log('Query:', searchQuery.value)
          
          // Fetch bots using search endpoint
          let botsData = []
          try {
            const botsRes = await botsAPI.searchBots(searchQuery.value)
            botsData = botsRes || []
            console.log('Bots raw:', botsData)
          } catch (bote) {
            console.error('Bots search error:', bots)
          }
          
          // Fetch users
          let usersData = []
          try {
            const usersRes = await usersAPI.search(searchQuery.value)
            usersData = usersRes.data || []
            console.log('Users:', usersData)
          } catch (ue) {
            console.error('Users fetch error:', ue)
          }
          
          // Bots already filtered by backend, just add type
          const bots = botsData.map(b => ({ ...b, type: 'bot' }))
          
          console.log('Filtered bots:', bots)
          console.log('=== SEARCH END ===')
          
          const users = usersData.map(u => ({ ...u, type: 'user' }))
          searchResults.value = [...bots, ...users]
          
        } catch (error) {
          console.error('Search error:', error)
          searchResults.value = []
        } finally {
          searching.value = false
        }
      }, 300)
    }

    const startChat = async (user) => {
      try {
        const chat = await chatsAPI.createPrivateChat(user.id)
        router.push(`/chat/${chat.id}`)
      } catch (error) {
        console.error('Error creating chat:', error)
        alert('Ошибка создания чата')
      }
    }

    const startChatWithBot = async (bot) => {
      alert('Чат с ботом доступен на странице Боты')
    }

    const openChat = (chatId) => {
      router.push(`/chat/${chatId}`)
    }

    const getChatName = (chat) => {
      if (chat.name) return chat.name
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== (currentUser.value ? currentUser.value.id : null))
        if (otherMember) {
          return otherMember.user?.full_name || otherMember.user?.email || 'Пользователь'
        }
      }
      return 'Чат'
    }

    const getChatAvatar = (chat) => {
      if (chat.chat_type === 'group') return null
      if (chat.chat_type === 'bot' && chat.bot?.avatar_url) return chat.bot.avatar_url
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== (currentUser.value ? currentUser.value.id : null))
        if (otherMember && otherMember.user?.avatar_url) {
          return otherMember.user.avatar_url
        }
      }
      return null
    }

    const getChatInitials = (chat) => {
      if (chat.chat_type === 'bot') {
        const name = chat.bot?.name || 'Бот'
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
      }
      const name = getChatName(chat)
      if (!name || name === 'Чат') return '?'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const getOtherMemberUserId = (chat) => {
      if (chat.chat_type === 'group') return null
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== (currentUser.value ? currentUser.value.id : null))
        return otherMember?.user_id || null
      }
      return null
    }

    const isOtherMemberUltra = (chat) => {
      if (chat.chat_type === 'group' || !chat.members) return false
      const otherMember = chat.members.find(m => m.user_id !== (currentUser.value ? currentUser.value.id : null))
      return otherMember?.user?.is_ultra || false
    }

    const formatTime = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      
      if (minutes < 1) return 'только что'
      if (minutes < 60) return `${minutes} мин назад`
      const hours = Math.floor(minutes / 60)
      if (hours < 24) return `${hours} ч назад`
      return date.toLocaleDateString()
    }

    const loadChats = async () => {
      loadingChats.value = true
      try {
        const response = await chatsAPI.getChats()
        chats.value = response.data || []
        // Сортируем по времени последнего сообщения
        chats.value.sort((a, b) => {
          const timeA = a.last_message?.created_at || a.updated_at
          const timeB = b.last_message?.created_at || b.updated_at
          return new Date(timeB) - new Date(timeA)
        })
      } catch (error) {
        console.error('Error loading chats:', error)
      } finally {
        loadingChats.value = false
      }
    }

    const handleGroupMemberSearch = async () => {
      if (!groupMemberSearch.value.trim()) {
        groupSearchResults.value = []
        return
      }
      try {
        const response = await usersAPI.search(groupMemberSearch.value)
        const excludeIds = [currentUser.value ? currentUser.value.id : null, ...selectedMembers.value.map(m => m.id)].filter(Boolean)
        groupSearchResults.value = (response.data || []).filter(u => !excludeIds.includes(u.id))
      } catch (error) {
        console.error('Group member search error:', error)
        groupSearchResults.value = []
      }
    }

    const toggleGroupMember = (user) => {
      const index = selectedMembers.value.findIndex(m => m.id === user.id)
      if (index === -1) {
        selectedMembers.value.push(user)
      } else {
        selectedMembers.value.splice(index, 1)
      }
    }

    const isMemberSelected = (userId) => {
      return selectedMembers.value.some(m => m.id === userId)
    }

    const removeMember = (userId) => {
      const index = selectedMembers.value.findIndex(m => m.id === userId)
      if (index !== -1) {
        selectedMembers.value.splice(index, 1)
      }
    }

    const createGroupChat = async () => {
      if (!newGroupName.value.trim() || selectedMembers.value.length === 0) {
        groupError.value = 'Заполните название и выберите хотя бы одного участника'
        return
      }

      creatingGroup.value = true
      groupError.value = ''

      try {
        const memberIds = selectedMembers.value.map(m => m.id)
        const chat = await chatsAPI.createGroupChat(newGroupName.value, memberIds)
        
        // Сброс формы
        showCreateGroup.value = false
        newGroupName.value = ''
        groupMemberSearch.value = ''
        groupSearchResults.value = []
        selectedMembers.value = []
        
        // Обновляем список чатов и переходим в новый чат
        await loadChats()
        router.push(`/chat/${chat.id}`)
      } catch (error) {
        console.error('Error creating group chat:', error)
        groupError.value = error.response?.data?.detail || 'Ошибка создания группового чата'
      } finally {
        creatingGroup.value = false
      }
    }

    const handleLogout = () => {
      localStorage.removeItem('access_token')
      router.push('/login')
    }

    const loadSeasonData = async () => {
      try {
        const { default: api } = await import('../services/api')
        const seasonRes = await api.get('/seasons/active')
        activeSeason.value = seasonRes.data
        if (seasonRes.data) {
          const progressRes = await api.get('/seasons/my-progress')
          seasonProgress.value = progressRes.data || { progress: 0, completed_tasks: [], total_reward_earned: 0 }
          const tasksRes = await api.get(`/seasons/${seasonRes.data.id}/tasks`)
          seasonTasks.value = tasksRes.data || []
        }
      } catch (error) {
        console.error('Error loading season:', error)
      }
    }

    const claimTask = async (taskId) => {
      try {
        const { default: api } = await import('../services/api')
        await api.post('/seasons/claim-task', { task_id: taskId })
        await loadSeasonData()
        alert('Награда получена!')
      } catch (error) {
        console.error('Error claiming task:', error)
        alert(error.response?.data?.detail || 'Ошибка получения награды')
      }
    }

    onMounted(async () => {
      try {
        const { authAPI } = await import('../services/api')
        currentUser.value = await authAPI.getCurrentUser()
      } catch (error) {
        console.error('Error loading user:', error)
      }
      await loadChats()
      await loadSeasonData()
      initWebSocket()
      
      // Polling for new chats (fallback)
      setInterval(async () => {
        try {
          const response = await chatsAPI.getChats()
          chats.value = response.data || []
        } catch (e) {}
      }, 5000)
    })

    return {
      currentUser,
      searchQuery,
      searchResults,
      searching,
      chats,
      loadingChats,
      showCreateGroup,
      newGroupName,
      groupMemberSearch,
      groupSearchResults,
      selectedMembers,
      creatingGroup,
      groupError,
      handleSearch,
      startChat,
      startChatWithBot,
      openChat,
      getChatName,
      getChatAvatar,
      getChatInitials,
      formatTime,
      handleGroupMemberSearch,
      toggleGroupMember,
      isMemberSelected,
      removeMember,
      createGroupChat,
      handleLogout,
      activeSeason,
      seasonProgress,
      seasonTasks,
      showSeasonModal,
      claimTask,
      onlineUsers,
      isUserOnline,
      getOtherMemberUserId,
      isOtherMemberUltra,
    }
  },
}
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
  min-height: 100vh;
  background: var(--bg-dark);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: var(--bg-card);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.profile-link {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.profile-link:hover {
  color: var(--primary-purple);
  text-decoration: underline;
}

.admin-link {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.admin-link:hover {
  transform: scale(1.1);
}

.bots-link {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.bots-link:hover {
  transform: scale(1.1);
}

.profile-link {
  color: var(--primary-purple-light);
  text-decoration: none;
  font-size: 1.25rem;
  transition: all 0.3s ease;
}

.profile-link:hover {
  transform: scale(1.1);
}

.logout-btn {
  padding: 0.625rem 1.25rem;
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: var(--error);
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.search-section,
.chats-section {
  background: var(--bg-card);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.create-group-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(147, 51, 234, 0.3);
}

.create-group-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.create-group-btn span {
  font-size: 1.2rem;
  font-weight: 700;
}

.search-box input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.search-box input::placeholder {
  color: var(--text-muted);
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
  background: rgba(10, 10, 10, 0.7);
}

.search-results {
  margin-top: 1rem;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(10, 10, 10, 0.3);
}

.user-item:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  transform: translateX(4px);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-info strong {
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.type-badge {
  margin-right: 5px;
  font-size: 1.2rem;
}

.bot-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: #9333ea;
  border-radius: 4px;
  margin-left: 8px;
  color: white;
}

.user-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.chat-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
}

.chats-list {
  max-height: 600px;
  overflow-y: auto;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(10, 10, 10, 0.3);
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--primary-purple);
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background: #22c55e;
  border: 2px solid var(--bg-dark);
  border-radius: 50%;
}

.chat-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.chat-item:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  transform: translateX(4px);
}

.chat-item.group-chat {
  border-left: 3px solid var(--primary-purple);
}

.chat-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chat-name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.chat-name-row strong {
  color: var(--text-primary);
}

.group-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  background: rgba(147, 51, 234, 0.2);
  color: var(--primary-purple-light);
  border-radius: 4px;
  font-weight: 500;
}

.bot-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border-radius: 4px;
  font-weight: 500;
}

.ultra-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  border-radius: 4px;
  font-weight: 600;
  margin-left: 0.5rem;
}

.last-message {
  font-size: 0.875rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.chat-time {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.loading,
.no-results,
.no-chats {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(147, 51, 234, 0.3);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 2rem;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
}

.modal-body .form-group {
  margin-bottom: 1.5rem;
}

.modal-body label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

.modal-body input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.modal-body input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
}

.member-search-results {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.3s ease;
  border-bottom: 1px solid var(--border-color);
}

.member-item:last-child {
  border-bottom: none;
}

.member-item:hover {
  background: var(--bg-card-hover);
}

.member-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.member-info strong {
  color: var(--text-primary);
  font-size: 0.9rem;
}

.member-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-weight: 700;
  transition: all 0.3s ease;
}

.checkbox.checked {
  background: var(--primary-purple);
  border-color: var(--primary-purple);
}

.selected-members {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.selected-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.member-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(147, 51, 234, 0.2);
  color: var(--primary-purple-light);
  border-radius: 6px;
  font-size: 0.875rem;
}

.remove-member {
  background: none;
  border: none;
  color: var(--primary-purple-light);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.remove-member:hover {
  background: rgba(147, 51, 234, 0.3);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.cancel-btn,
.create-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.create-btn {
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .content {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-width: 100%;
    margin: 1rem;
  }
}

.season-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-weight: 600;
}

.season-modal {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 500px;
  width: 90%;
}

.season-modal h2 {
  color: var(--text-primary);
  margin-bottom: 1rem;
  text-align: center;
}

.season-progress {
  margin-bottom: 1.5rem;
  text-align: center;
}

.progress-bar {
  height: 20px;
  background: rgba(10, 10, 10, 0.5);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  transition: width 0.3s ease;
}

.season-tasks h3 {
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.task-item {
  background: rgba(10, 10, 10, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.75rem;
}

.task-info strong {
  color: var(--text-primary);
}

.task-info p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0.25rem 0;
}

.task-target {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.task-reward {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.claim-btn {
  padding: 0.375rem 0.75rem;
  background: var(--primary-purple);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
}

.completed-badge {
  color: #22c55e;
  font-weight: 600;
}

.menu-dropdown {
  position: relative;
  display: inline-block;
}

.menu-btn {
  padding: 0.625rem 1.25rem;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.menu-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.dropdown-content {
  display: none;
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 0.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  overflow: hidden;
}

.menu-dropdown:hover .dropdown-content {
  display: block;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.75rem 1rem;
  color: var(--text-primary);
  text-decoration: none;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: 0.95rem;
}

.dropdown-item:hover {
  background: var(--bg-card-hover);
}

.dropdown-item.logout {
  color: var(--error);
}

.close-btn {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
}
</style>

