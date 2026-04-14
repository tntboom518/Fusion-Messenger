<template>
  <div class="admin-container">
    <header class="header">
      <h1>⚙️ Админ-панель</h1>
      <button @click="goHome" class="back-btn">← На главную</button>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="content">
      <table v-if="users.length > 0" class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Имя</th>
            <th>Статус</th>
            <th>Причина бана</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.full_name || '-' }}</td>
            <td>
              <span v-if="user.is_banned" class="banned-badge">Заблокирован</span>
              <span v-else class="active-badge">Активен</span>
            </td>
            <td>{{ user.ban_reason || '-' }}</td>
            <td class="actions">
              <button 
                v-if="!user.is_banned && !user.is_superuser"
                @click="showBanModal(user)"
                class="ban-btn"
              >
                🚫 Забанить
              </button>
              <button 
                v-if="user.is_banned"
                @click="unbanUser(user.id)"
                class="unban-btn"
              >
                ✅ Разбанить
              </button>
              <button 
                v-if="!user.is_superuser"
                @click="deleteUser(user)"
                class="delete-btn"
              >
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-users">Нет пользователей</div>
    </div>

    <!-- Модальное окно бана -->
    <div v-if="showBanDialog" class="modal-overlay" @click.self="showBanDialog = false">
      <div class="modal-content">
        <h3>Заблокировать пользователя</h3>
        <p>{{ banTarget?.email }}</p>
        <textarea 
          v-model="banReason" 
          placeholder="Причина бана (необязательно)"
          rows="3"
        ></textarea>
        <div class="modal-actions">
          <button @click="showBanDialog = false" class="cancel-btn">Отмена</button>
          <button @click="confirmBan" class="ban-confirm-btn">Забанить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, authAPI } from '../services/api'

export default {
  name: 'Admin',
  setup() {
    const router = useRouter()
    const users = ref([])
    const loading = ref(true)
    const activeTab = ref('users')
    const currentUser = ref(null)
    const showBanDialog = ref(false)
    const banTarget = ref(null)
    const banReason = ref('')

    const loadUsers = async () => {
      loading.value = true
      try {
        const response = await usersAPI.getAll()
        users.value = response.data || []
      } catch (error) {
        console.error('Error loading users:', error)
      } finally {
        loading.value = false
      }
    }

    const showBanModal = (user) => {
      banTarget.value = user
      banReason.value = ''
      showBanDialog.value = true
    }

    const confirmBan = async () => {
      try {
        await usersAPI.banUser(banTarget.value.id, banReason.value || null)
        showBanDialog.value = false
        await loadUsers()
      } catch (error) {
        console.error('Error banning user:', error)
        alert('Ошибка бана')
      }
    }

    const unbanUser = async (userId) => {
      if (!confirm('Разблокировать пользователя?')) return
      try {
        await usersAPI.unbanUser(userId)
        await loadUsers()
      } catch (error) {
        console.error('Error unbanning user:', error)
        alert('Ошибка разбана')
      }
    }

    const deleteUser = async (user) => {
      if (!confirm(`Удалить пользователя ${user.email}?`)) return
      try {
        await usersAPI.deleteUser(user.id)
        await loadUsers()
      } catch (error) {
        console.error('Error deleting user:', error)
        alert('Ошибка удаления')
      }
    }

    const goHome = () => {
      router.push('/')
    }

    onMounted(async () => {
      try {
        currentUser.value = await authAPI.getCurrentUser()
        if (!currentUser.value.is_superuser) {
          router.push('/')
          return
        }
        await loadUsers()
      } catch (error) {
        console.error('Error:', error)
        router.push('/login')
      }
    })

    watch(activeTab, loadUsers)

    return {
      users,
      loading,
      activeTab,
      showBanDialog,
      banTarget,
      banReason,
      showBanModal,
      confirmBan,
      unbanUser,
      deleteUser,
      goHome,
    }
  },
}
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  min-height: 100vh;
  background: var(--bg-dark);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header h1 {
  color: var(--text-primary);
  font-size: 1.5rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  padding: 0.75rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab.active {
  background: var(--primary-purple);
  color: white;
  border-color: var(--primary-purple);
}

.content {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.users-table th {
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-secondary);
  font-weight: 600;
}

.users-table td {
  color: var(--text-primary);
}

.banned-badge {
  padding: 0.25rem 0.5rem;
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border-radius: 4px;
  font-size: 0.85rem;
}

.active-badge {
  padding: 0.25rem 0.5rem;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border-radius: 4px;
  font-size: 0.85rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.ban-btn, .unban-btn, .delete-btn {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;
}

.ban-btn {
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
}

.ban-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.unban-btn {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.unban-btn:hover {
  background: rgba(34, 197, 94, 0.3);
}

.delete-btn {
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.no-users {
  padding: 2rem;
  text-align: center;
  color: var(--text-secondary);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

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
  background: var(--bg-card);
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal-content h3 {
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.modal-content p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.modal-content textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  resize: vertical;
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.cancel-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-card-hover);
  border: none;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
}

.ban-confirm-btn {
  padding: 0.5rem 1rem;
  background: var(--error);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}
</style>