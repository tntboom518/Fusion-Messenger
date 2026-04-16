<template>
  <div class="channels-container">
    <header class="channels-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h1>Каналы</h1>
      <button @click="showCreateModal = true" class="create-btn">+ Создать канал</button>
    </header>

    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'all' }]" @click="activeTab = 'all'">Все каналы</button>
      <button :class="['tab', { active: activeTab === 'my' }]" @click="loadMyChannels">Мои каналы</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="channels-list">
      <div v-for="channel in displayedChannels" :key="channel.id" class="channel-card" @click="openChannel(channel.id)">
        <div class="channel-avatar">
          {{ getInitials(channel.name) }}
        </div>
        <div class="channel-info">
          <h3 class="channel-name">{{ channel.name }}</h3>
          <p class="channel-desc">{{ channel.description || 'Описание отсутствует' }}</p>
          <div class="channel-meta">
            <span>Создатель: {{ channel.creator?.full_name || 'Неизвестно' }}</span>
            <span v-if="channel.is_admin" class="admin-badge">Админ</span>
          </div>
        </div>
      </div>
      
      <div v-if="displayedChannels.length === 0" class="empty-state">
        Каналов пока нет
      </div>
    </div>

    <!-- Modal создания канала -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Создать канал</h3>
          <button @click="showCreateModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Название</label>
            <input v-model="newChannel.name" placeholder="Название канала" class="input" />
          </div>
          <div class="form-group">
            <label>Описание</label>
            <textarea v-model="newChannel.description" placeholder="Описание канала" class="input" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="newChannel.is_public" /> Публичный канал
            </label>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showCreateModal = false" class="btn-secondary">Отмена</button>
          <button @click="createChannel" :disabled="!newChannel.name.trim()" class="btn-primary">Создать</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { channelsAPI } from '../services/api'

export default {
  name: 'Channels',
  setup() {
    const router = useRouter()
    const channels = ref([])
    const myChannels = ref([])
    const loading = ref(true)
    const activeTab = ref('all')
    const showCreateModal = ref(false)
    const newChannel = ref({
      name: '',
      description: '',
      is_public: true,
    })

    const displayedChannels = computed(() => {
      return activeTab.value === 'my' ? myChannels.value : channels.value
    })

    const loadChannels = async () => {
      try {
        const res = await channelsAPI.getChannels()
        channels.value = res.data || []
      } catch (e) {
        console.error('Error loading channels:', e)
      } finally {
        loading.value = false
      }
    }

    const loadMyChannels = async () => {
      activeTab.value = 'my'
      try {
        const res = await channelsAPI.getMyChannels()
        myChannels.value = res.data || []
      } catch (e) {
        console.error('Error loading my channels:', e)
      }
    }

    const createChannel = async () => {
      if (!newChannel.value.name.trim()) return
      try {
        const res = await channelsAPI.createChannel(newChannel.value)
        channels.value.unshift(res)
        myChannels.value.unshift(res)
        showCreateModal.value = false
        newChannel.value = { name: '', description: '', is_public: true }
      } catch (e) {
        console.error('Error creating channel:', e)
        alert('Ошибка создания канала')
      }
    }

    const openChannel = (channelId) => {
      router.push(`/channels/${channelId}`)
    }

    const goBack = () => {
      router.push('/')
    }

    const getInitials = (name) => {
      if (!name) return '?'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    onMounted(loadChannels)

    return {
      channels,
      myChannels,
      loading,
      activeTab,
      displayedChannels,
      showCreateModal,
      newChannel,
      loadMyChannels,
      createChannel,
      openChannel,
      goBack,
      getInitials,
    }
  },
}
</script>

<style scoped>
.channels-container {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-dark, #1a1a2e);
  color: var(--text-primary, #eee);
}

.channels-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--bg-card, #16213e);
  border-bottom: 1px solid var(--border-color, #333);
}

.channels-header h1 {
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
}

.create-btn {
  background: var(--primary-purple, #9333ea);
  border-color: var(--primary-purple, #9333ea);
}

.tabs {
  display: flex;
  padding: 1rem;
  gap: 0.5rem;
  background: var(--bg-card, #16213e);
}

.tab {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-secondary, #999);
  cursor: pointer;
  font-weight: 600;
}

.tab.active {
  background: var(--primary-purple, #9333ea);
  border-color: var(--primary-purple, #9333ea);
  color: white;
}

.channels-list {
  padding: 1rem;
}

.channel-card {
  display: flex;
  gap: 1rem;
  background: var(--bg-card, #16213e);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  cursor: pointer;
  border: 1px solid var(--border-color, #333);
  transition: all 0.3s ease;
}

.channel-card:hover {
  border-color: var(--primary-purple, #9333ea);
}

.channel-avatar {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary-purple, #9333ea), var(--primary-purple-light, #a855f7));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.channel-info {
  flex: 1;
  min-width: 0;
}

.channel-name {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
  color: var(--text-primary, #eee);
}

.channel-desc {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  color: var(--text-secondary, #999);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.channel-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary, #999);
}

.admin-badge {
  background: var(--primary-purple, #9333ea);
  color: white;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
}

.empty-state, .loading {
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
}

.modal-content {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  width: 100%;
  max-width: 450px;
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

.input {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-dark, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
}

.input:focus {
  outline: none;
  border-color: var(--primary-purple, #9333ea);
}

.form-group input[type="checkbox"] {
  margin-right: 0.5rem;
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
}

.btn-primary:disabled {
  opacity: 0.5;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: transparent;
  color: var(--text-secondary, #999);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  cursor: pointer;
}
</style>