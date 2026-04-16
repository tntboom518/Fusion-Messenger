<template>
  <div class="admin-container">
    <header class="header">
      <h1>⚙️ Админ-панель</h1>
      <button @click="goHome" class="back-btn">← На главную</button>
    </header>

    <div class="tabs">
      <button 
        :class="['tab', { active: activeTab === 'users' }]"
        @click="activeTab = 'users'"
      >👥 Пользователи</button>
      <button 
        :class="['tab', { active: activeTab === 'nfts' }]"
        @click="activeTab = 'nfts'; loadNFTs()"
      >🖼️ NFT Магазин</button>
      <button 
        :class="['tab', { active: activeTab === 'seasons' }]"
        @click="activeTab = 'seasons'; loadSeasons()"
      >🏆 Сезоны</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <!-- Таблица пользователей -->
    <div v-else-if="activeTab === 'users'" class="content">
      <table v-if="users.length > 0" class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Имя</th>
            <th>Баланс</th>
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
              <span class="balance">{{ user.balance || 0 }}</span>
              <button @click="showAddBalanceModal(user)" class="add-balance-btn" title="Добавить шекели">+</button>
            </td>
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
                @click="user.is_ultra ? revokeUltra(user.id) : grantUltra(user)"
                :class="['ultra-btn', { active: user.is_ultra }]"
              >
                {{ user.is_ultra ? '⚡ Убрать Ultra' : '⚡ Дать Ultra' }}
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

    <!-- Секция NFT -->
    <div v-else-if="activeTab === 'nfts'" class="content">
      <div class="nft-header">
        <button @click="showCreateNFTModal = true" class="create-nft-btn">➕ Добавить NFT</button>
      </div>
      <table v-if="nfts.length > 0" class="nft-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Картинка</th>
            <th>Название</th>
            <th>Описание</th>
            <th>Цена</th>
            <th>Редкость</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="nft in nfts" :key="nft.id">
            <td>{{ nft.id }}</td>
            <td>
              <img v-if="nft.image_url" :src="nft.image_url" class="nft-thumb" />
              <span v-else>Нет</span>
            </td>
            <td>{{ nft.name }}</td>
            <td>{{ nft.description || '-' }}</td>
            <td>{{ nft.price }}</td>
            <td>
              <span class="rarity" :class="nft.rarity">{{ nft.rarity }}</span>
            </td>
            <td>
              <span v-if="nft.is_active" class="active-badge">Активен</span>
              <span v-else class="banned-badge">Неактивен</span>
            </td>
            <td class="actions">
              <button @click="showEditNFTModal(nft)" class="edit-btn">✏️</button>
              <button @click="deleteNFT(nft.id)" class="delete-btn">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="no-users">Нет NFT предметов</div>
    </div>

    <!-- Секция Сезонов -->
    <div v-else-if="activeTab === 'seasons'" class="content">
      <div class="season-header">
        <button @click="showCreateSeasonModal = true" class="create-nft-btn">➕ Создать сезон</button>
      </div>
      <div v-if="seasons.length === 0" class="no-users">Нет сезонов</div>
      <div v-else class="seasons-list">
        <div v-for="season in seasons" :key="season.id" class="season-card">
          <div class="season-info">
            <h3>Сезон {{ season.number }}: {{ season.name }}</h3>
            <span :class="season.is_active ? 'active-badge' : 'banned-badge'">
              {{ season.is_active ? 'Активен' : 'Неактивен' }}
            </span>
          </div>
          <div class="season-actions">
            <button v-if="!season.is_active" @click="startSeason(season.id)" class="start-btn">▶️ Начать</button>
            <button v-if="season.is_active" @click="endSeason" class="end-btn">⏹️ Завершить</button>
            <button @click="openAddTaskModal(season.id)" class="add-task-btn">➕ Задание</button>
            <button @click="loadSeasonTasks(season.id)" class="view-tasks-btn">📋 Задания</button>
          </div>
          <div v-if="seasonTasks[season.id]" class="season-tasks">
            <table class="nft-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Описание</th>
                  <th>Цель</th>
                  <th>Награда</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in seasonTasks[season.id]" :key="task.id">
                  <td>{{ task.name }}</td>
                  <td>{{ task.description || '-' }}</td>
                  <td>{{ task.target_count }}</td>
                  <td>{{ task.base_reward }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
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

    <!-- Модальное окно добавления шекелей -->
    <div v-if="showAddBalanceDialog" class="modal-overlay" @click.self="showAddBalanceDialog = false">
      <div class="modal-content">
        <h3>Добавить шекели</h3>
        <p>Пользователь: {{ balanceTarget?.email }}</p>
        <p>Текущий баланс: {{ balanceTarget?.balance || 0 }}</p>
        <div class="form-group">
          <label>Сумма:</label>
          <input v-model.number="addBalanceAmount" type="number" min="1" placeholder="Введите сумму" />
        </div>
        <div class="modal-actions">
          <button @click="showAddBalanceDialog = false" class="cancel-btn">Отмена</button>
          <button @click="confirmAddBalance" class="add-balance-confirm-btn">Добавить</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания NFT -->
    <div v-if="showCreateNFTModal" class="modal-overlay" @click.self="showCreateNFTModal = false">
      <div class="modal-content">
        <h3>Создать NFT</h3>
        <div class="form-group">
          <label>Название:</label>
          <input v-model="newNFT.name" placeholder="Название NFT" />
        </div>
        <div class="form-group">
          <label>Описание:</label>
          <textarea v-model="newNFT.description" placeholder="Описание" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label>URL картинки:</label>
          <input v-model="newNFT.image_url" placeholder="https://..." />
        </div>
        <div class="form-group">
          <label>Цена:</label>
          <input v-model.number="newNFT.price" type="number" min="0" placeholder="Цена в шекелях" />
        </div>
        <div class="form-group">
          <label>Редкость:</label>
          <select v-model="newNFT.rarity">
            <option value="common">Common</option>
            <option value="rare">Rare</option>
            <option value="epic">Epic</option>
            <option value="legendary">Legendary</option>
          </select>
        </div>
        <div class="form-group">
          <label>Активен:</label>
          <input v-model="newNFT.is_active" type="checkbox" />
        </div>
        <div class="modal-actions">
          <button @click="showCreateNFTModal = false" class="cancel-btn">Отмена</button>
          <button @click="createNFT" class="save-btn">Создать</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно редактирования NFT -->
    <div v-if="showEditNFTDialog" class="modal-overlay" @click.self="showEditNFTDialog = false">
      <div class="modal-content">
        <h3>Редактировать NFT</h3>
        <div class="form-group">
          <label>Название:</label>
          <input v-model="editNFT.name" placeholder="Название NFT" />
        </div>
        <div class="form-group">
          <label>Описание:</label>
          <textarea v-model="editNFT.description" placeholder="Описание" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label>URL картинки:</label>
          <input v-model="editNFT.image_url" placeholder="https://..." />
        </div>
        <div class="form-group">
          <label>Цена:</label>
          <input v-model.number="editNFT.price" type="number" min="0" placeholder="Цена в шекелях" />
        </div>
        <div class="form-group">
          <label>Редкость:</label>
          <select v-model="editNFT.rarity">
            <option value="common">Common</option>
            <option value="rare">Rare</option>
            <option value="epic">Epic</option>
            <option value="legendary">Legendary</option>
          </select>
        </div>
        <div class="form-group">
          <label>Активен:</label>
          <input v-model="editNFT.is_active" type="checkbox" />
        </div>
        <div class="modal-actions">
          <button @click="showEditNFTDialog = false" class="cancel-btn">Отмена</button>
          <button @click="updateNFT" class="save-btn">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания сезона -->
    <div v-if="showCreateSeasonModal" class="modal-overlay" @click.self="showCreateSeasonModal = false">
      <div class="modal-content">
        <h3>Создать сезон</h3>
        <div class="form-group">
          <label>Название:</label>
          <input v-model="newSeason.name" placeholder="Название сезона" />
        </div>
        <div class="form-group">
          <label>Номер сезона:</label>
          <input v-model.number="newSeason.number" type="number" min="1" />
        </div>
        <div class="modal-actions">
          <button @click="showCreateSeasonModal = false" class="cancel-btn">Отмена</button>
          <button @click="createSeason" class="save-btn">Создать</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания задания -->
    <div v-if="showAddTaskModalDialog" class="modal-overlay" @click.self="showAddTaskModalDialog = false">
      <div class="modal-content">
        <h3>Создать задание</h3>
        <div class="form-group">
          <label>Название:</label>
          <input v-model="newTask.name" placeholder="Название задания" />
        </div>
        <div class="form-group">
          <label>Описание:</label>
          <textarea v-model="newTask.description" placeholder="Описание" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label>Цель (кол-во):</label>
          <input v-model.number="newTask.target_count" type="number" min="1" />
        </div>
        <div class="form-group">
          <label>Тип задания:</label>
          <select v-model="newTask.task_type">
            <option value="messages">Отправить сообщения</option>
            <option value="chats">Создать чаты</option>
            <option value="friends">Добавить друзей</option>
          </select>
        </div>
        <div class="form-group">
          <label>Базовая награда:</label>
          <input v-model.number="newTask.base_reward" type="number" min="0" />
        </div>
        <div class="modal-actions">
          <button @click="showAddTaskModalDialog = false" class="cancel-btn">Отмена</button>
          <button @click="createTask" class="save-btn">Создать</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, authAPI, ultraAPI } from '../services/api'
import api from '../services/api'

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
    const showAddBalanceDialog = ref(false)
    const balanceTarget = ref(null)
    const addBalanceAmount = ref(0)
    const nfts = ref([])
    const showCreateNFTModal = ref(false)
    const showEditNFTDialog = ref(false)
    const newNFT = ref({
      name: '',
      description: '',
      image_url: '',
      price: 0,
      rarity: 'common',
      is_active: true
    })
    const editNFT = ref({
      id: null,
      name: '',
      description: '',
      image_url: '',
      price: 0,
      rarity: 'common',
      is_active: true
    })

    const seasons = ref([])
    const showCreateSeasonModal = ref(false)
    const showAddTaskModalDialog = ref(false)
    const selectedSeasonId = ref(null)
    const seasonTasks = ref({})
    const newSeason = ref({ name: '', number: 1 })
    const newTask = ref({
      name: '',
      description: '',
      target_count: 1,
      task_type: 'messages',
      base_reward: 10
    })

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

    const grantUltra = async (user) => {
      const hours = prompt('Сколько часов добавить?', '2')
      if (!hours) return
      const hoursNum = parseInt(hours)
      if (isNaN(hoursNum) || hoursNum <= 0) {
        alert('Введите корректное число часов')
        return
      }
      try {
        await ultraAPI.grant(user.id, hoursNum)
        await loadUsers()
        alert(`Выдано ${hoursNum} часов Ultra пользователю ${user.email}`)
      } catch (error) {
        console.error('Error granting Ultra:', error)
        alert('Ошибка выдачи Ultra')
      }
    }

    const revokeUltra = async (userId) => {
      if (!confirm('Забрать Ultra у пользователя?')) return
      try {
        await ultraAPI.revoke(userId)
        await loadUsers()
        alert('Ultra успешно забран')
      } catch (error) {
        console.error('Error revoking Ultra:', error)
        alert('Ошибка отзыва Ultra')
      }
    }

    const showAddBalanceModal = (user) => {
      balanceTarget.value = user
      addBalanceAmount.value = 0
      showAddBalanceDialog.value = true
    }

    const confirmAddBalance = async () => {
      if (!addBalanceAmount.value || addBalanceAmount.value <= 0) {
        alert('Введите корректную сумму')
        return
      }
      try {
        await usersAPI.addBalance(balanceTarget.value.id, addBalanceAmount.value)
        showAddBalanceDialog.value = false
        await loadUsers()
        alert(`Добавлено ${addBalanceAmount.value} шекелей пользователю ${balanceTarget.value.email}`)
      } catch (error) {
        console.error('Error adding balance:', error)
        alert('Ошибка добавления шекелей')
      }
    }

    const loadNFTs = async () => {
      try {
        const response = await api.get('/users/shop')
        nfts.value = response.data || []
      } catch (error) {
        console.error('Error loading NFTs:', error)
      }
    }

    const createNFT = async () => {
      if (!newNFT.value.name || newNFT.value.price < 0) {
        alert('Заполните название и цену')
        return
      }
      try {
        await api.post('/users/nft', newNFT.value)
        showCreateNFTModal.value = false
        newNFT.value = {
          name: '',
          description: '',
          image_url: '',
          price: 0,
          rarity: 'common',
          is_active: true
        }
        await loadNFTs()
        alert('NFT создан!')
      } catch (error) {
        console.error('Error creating NFT:', error)
        alert('Ошибка создания NFT')
      }
    }

    const showEditNFTModal = (nft) => {
      editNFT.value = { ...nft }
      showEditNFTDialog.value = true
    }

    const updateNFT = async () => {
      try {
        await api.put(`/users/nft/${editNFT.value.id}`, editNFT.value)
        showEditNFTDialog.value = false
        await loadNFTs()
        alert('NFT обновлён!')
      } catch (error) {
        console.error('Error updating NFT:', error)
        alert('Ошибка обновления NFT')
      }
    }

    const deleteNFT = async (nftId) => {
      if (!confirm('Удалить этот NFT?')) return
      try {
        await api.delete(`/users/nft/${nftId}`)
        await loadNFTs()
        alert('NFT удалён!')
      } catch (error) {
        console.error('Error deleting NFT:', error)
        alert('Ошибка удаления NFT')
      }
    }

    const loadSeasons = async () => {
      try {
        const response = await api.get('/seasons/')
        seasons.value = response.data || []
      } catch (error) {
        console.error('Error loading seasons:', error)
      }
    }

    const createSeason = async () => {
      if (!newSeason.value.name || !newSeason.value.number) {
        alert('Заполните название и номер сезона')
        return
      }
      try {
        await api.post('/seasons/admin/create', newSeason.value)
        showCreateSeasonModal.value = false
        newSeason.value = { name: '', number: 1 }
        await loadSeasons()
        alert('Сезон создан!')
      } catch (error) {
        console.error('Error creating season:', error)
        alert('Ошибка создания сезона')
      }
    }

    const startSeason = async (seasonId) => {
      try {
        await api.post('/seasons/admin/start', { season_id: seasonId })
        await loadSeasons()
        alert('Сезон начат!')
      } catch (error) {
        console.error('Error starting season:', error)
        alert('Ошибка начала сезона')
      }
    }

    const endSeason = async () => {
      try {
        await api.post('/seasons/admin/end')
        await loadSeasons()
        alert('Сезон завершён!')
      } catch (error) {
        console.error('Error ending season:', error)
        alert('Ошибка завершения сезона')
      }
    }

    const openAddTaskModal = (seasonId) => {
      selectedSeasonId.value = seasonId
      newTask.value = {
        name: '',
        description: '',
        target_count: 1,
        task_type: 'messages',
        base_reward: 10
      }
      showAddTaskModalDialog.value = true
    }

    const createTask = async () => {
      if (!newTask.value.name || !newTask.value.target_count) {
        alert('Заполните название и цель задания')
        return
      }
      try {
        await api.post(`/seasons/admin/${selectedSeasonId.value}/tasks`, newTask.value)
        showAddTaskModalDialog.value = false
        alert('Задание создано!')
        loadSeasonTasks(selectedSeasonId.value)
      } catch (error) {
        console.error('Error creating task:', error)
        alert('Ошибка создания задания')
      }
    }

    const loadSeasonTasks = async (seasonId) => {
      try {
        const response = await api.get(`/seasons/${seasonId}/tasks`)
        seasonTasks.value[seasonId] = response.data || []
      } catch (error) {
        console.error('Error loading tasks:', error)
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

    watch(activeTab, (newTab) => {
      if (newTab === 'users') {
        loadUsers()
      } else if (newTab === 'nfts') {
        loadNFTs()
      } else if (newTab === 'seasons') {
        loadSeasons()
      }
    })

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
      grantUltra,
      revokeUltra,
      showAddBalanceModal,
      confirmAddBalance,
      showAddBalanceDialog,
      balanceTarget,
      addBalanceAmount,
      nfts,
      showCreateNFTModal,
      showEditNFTDialog,
      newNFT,
      editNFT,
      loadNFTs,
      createNFT,
      showEditNFTModal,
      updateNFT,
      deleteNFT,
      seasons,
      showCreateSeasonModal,
      showAddTaskModalDialog,
      selectedSeasonId,
      seasonTasks,
      newSeason,
      newTask,
      loadSeasons,
      createSeason,
      startSeason,
      endSeason,
      openAddTaskModal,
      createTask,
      loadSeasonTasks,
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

.ban-btn, .unban-btn, .ultra-btn, .delete-btn {
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

.ultra-btn {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
}

.ultra-btn:hover {
  transform: scale(1.05);
}

.ultra-btn.active {
  background: rgba(148, 163, 184, 0.3);
  color: var(--text-primary);
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

.add-balance-btn {
  padding: 0.2rem 0.5rem;
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 4px;
  color: #22c55e;
  cursor: pointer;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

.add-balance-btn:hover {
  background: rgba(34, 197, 94, 0.3);
}

.balance {
  color: var(--primary-purple-light);
  font-weight: 600;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  box-sizing: border-box;
}

.add-balance-confirm-btn {
  padding: 0.5rem 1rem;
  background: #22c55e;
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
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

.nft-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.create-nft-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-purple);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.create-nft-btn:hover {
  background: var(--primary-purple-light);
}

.nft-table {
  width: 100%;
  border-collapse: collapse;
}

.nft-table th,
.nft-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.nft-table th {
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-secondary);
  font-weight: 600;
}

.nft-thumb {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
}

.rarity {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.rarity.common {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.rarity.rare {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.rarity.epic {
  background: rgba(139, 92, 246, 0.2);
  color: #8b5cf6;
}

.rarity.legendary {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.edit-btn {
  padding: 0.375rem 0.75rem;
  background: rgba(59, 130, 246, 0.2);
  border: none;
  border-radius: 6px;
  color: #3b82f6;
  cursor: pointer;
}

.edit-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.save-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-purple);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  box-sizing: border-box;
}

.form-group input[type="checkbox"] {
  width: auto;
}

.season-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.season-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.season-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.season-info h3 {
  color: var(--text-primary);
  margin: 0;
}

.season-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.start-btn {
  padding: 0.5rem 1rem;
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  color: #22c55e;
  cursor: pointer;
}

.end-btn {
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: var(--error);
  cursor: pointer;
}

.add-task-btn, .view-tasks-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-purple);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
}

.season-tasks {
  margin-top: 1rem;
}
</style>