<template>
  <div class="profile-container">
    <header class="header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h1>Профиль</h1>
      <div></div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="profile-content">
      <div class="profile-card">
        <h2>Информация о пользователе</h2>
        
        <div class="avatar-section">
          <div class="avatar-wrapper" @click="triggerAvatarUpload">
            <img v-if="user.avatar_url" :src="user.avatar_url" alt="Avatar" class="avatar-img" />
            <div v-else class="avatar-placeholder">
              {{ getInitials(user.full_name || user.email) }}
            </div>
            <div class="avatar-overlay">
              <span>📷</span>
            </div>
          </div>
          <input 
            ref="avatarInput" 
            type="file" 
            accept="image/*" 
            @change="handleAvatarChange" 
            hidden 
          />
          <button v-if="user.avatar_url" @click="handleAvatarDelete" class="remove-avatar-btn">
            Удалить аватарку
          </button>
        </div>

        <div class="profile-info">
          <div class="info-item">
            <label>Email:</label>
            <span>{{ user.email }}</span>
          </div>
          <div class="info-item">
            <label>Имя:</label>
            <div class="edit-field">
              <span v-if="!editingName">{{ user.full_name || 'Не указано' }}</span>
              <input 
                v-else 
                v-model="editedName" 
                class="name-input"
                maxlength="100"
              />
              <button v-if="!editingName" @click="startEditName" class="edit-btn">✏️</button>
              <div v-else class="edit-actions">
                <button @click="saveName" class="save-btn">✓</button>
                <button @click="cancelEditName" class="cancel-btn">✕</button>
              </div>
            </div>
          </div>
        </div>

        <div class="balance-section">
          <h3>💰 Шекели</h3>
          <div class="balance-display">
            <span class="balance-amount">{{ user.balance || 0 }}</span>
            <span class="balance-label">шекелей</span>
          </div>
          <div class="balance-actions">
            <button @click="addShekels" class="add-balance-btn">🎁 Получить 1000</button>
            <button @click="showTransferModal = true" class="transfer-btn">Перевести</button>
          </div>
        </div>

        <div class="nft-section">
          <div class="nft-header">
            <h3>🖼️ NFT Коллекция</h3>
            <div class="nft-tabs">
              <button 
                :class="{ active: nftTab === 'shop' }" 
                @click="nftTab = 'shop'"
              >Магазин</button>
              <button 
                :class="{ active: nftTab === 'collection' }" 
                @click="loadUserNFTs(); nftTab = 'collection'"
              >Моя коллекция ({{ userNfts.length }})</button>
            </div>
          </div>

          <div v-if="nftTab === 'shop'" class="nft-shop">
            <div v-if="shopLoading" class="nft-loading">Загрузка...</div>
            <div v-else-if="shopItems.length === 0" class="nft-empty">
              Магазин пуст
            </div>
            <div v-else class="nft-grid">
              <div 
                v-for="item in shopItems" 
                :key="item.id" 
                class="nft-card"
                :class="item.rarity"
              >
                <div class="nft-image">
                  <img v-if="item.image_url" :src="item.image_url" :alt="item.name" />
                  <div v-else class="nft-placeholder">🎨</div>
                </div>
                <div class="nft-info">
                  <h4>{{ item.name }}</h4>
                  <p class="nft-description">{{ item.description }}</p>
                  <div class="nft-meta">
                    <span class="nft-rarity" :class="item.rarity">{{ item.rarity }}</span>
                    <span class="nft-price">💰 {{ item.price }}</span>
                  </div>
                </div>
                <button 
                  @click="buyNFT(item)" 
                  class="buy-btn"
                  :disabled="buyingItem === item.id || (user.balance || 0) < item.price"
                >
                  {{ buyingItem === item.id ? '...' : 'Купить' }}
                </button>
              </div>
            </div>
          </div>

          <div v-else class="nft-collection">
            <div v-if="nftLoading" class="nft-loading">Загрузка...</div>
            <div v-else-if="userNfts.length === 0" class="nft-empty">
              У вас пока нет NFT
            </div>
            <div v-else class="nft-grid">
              <div 
                v-for="nft in userNfts" 
                :key="nft.id" 
                class="nft-card owned"
                :class="nft.item.rarity"
              >
                <div class="nft-image">
                  <img v-if="nft.item.image_url" :src="nft.item.image_url" :alt="nft.item.name" />
                  <div v-else class="nft-placeholder">🎨</div>
                </div>
                <div class="nft-info">
                  <h4>{{ nft.item.name }}</h4>
                  <p class="nft-description">{{ nft.item.description }}</p>
                  <div class="nft-meta">
                    <span class="nft-rarity" :class="nft.item.rarity">{{ nft.item.rarity }}</span>
                    <span class="nft-date">{{ formatDate(nft.purchased_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="danger-zone">
          <h3>Опасная зона</h3>
          <p>Удаление аккаунта необратимо. Все ваши данные будут удалены.</p>
          <button @click="handleDelete" class="delete-btn" :disabled="deleting">
            {{ deleting ? 'Удаление...' : 'Удалить аккаунт' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно перевода шекелей -->
    <div v-if="showTransferModal" class="modal-overlay" @click.self="showTransferModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Перевод шекелей</h3>
          <button @click="showTransferModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p>Ваш баланс: {{ user.balance || 0 }} шекелей</p>
          <div class="form-group">
            <label>Email получателя:</label>
            <input v-model="transferEmail" type="email" placeholder="user@example.com" />
          </div>
          <div class="form-group">
            <label>Сумма:</label>
            <input v-model.number="transferAmount" type="number" min="1" placeholder="0" />
          </div>
          <p v-if="transferError" class="error">{{ transferError }}</p>
        </div>
        <div class="modal-footer">
          <button @click="showTransferModal = false" class="cancel-btn">Отмена</button>
          <button @click="doTransfer" class="transfer-confirm-btn" :disabled="transferring">
            {{ transferring ? 'Перевод...' : 'Перевести' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { nftAPI } from '@/services/api.js'

const API_BASE_URL = '/api/v1'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const user = ref(null)
    const loading = ref(true)
    const deleting = ref(false)
    const avatarInput = ref(null)
    const editingName = ref(false)
    const editedName = ref('')
    const savingName = ref(false)
    const showTransferModal = ref(false)
    const transferEmail = ref('')
    const transferAmount = ref(0)
    const transferError = ref('')
    const transferring = ref(false)
    const nftTab = ref('shop')
    const shopItems = ref([])
    const shopLoading = ref(true)
    const userNfts = ref([])
    const nftLoading = ref(false)
    const buyingItem = ref(null)

    const loadUser = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/users/me`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        user.value = response.data
        loadShopItems()
      } catch (error) {
        console.error('Error loading user:', error)
        router.push('/login')
      } finally {
        loading.value = false
      }
    }

    const addShekels = async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/users/me/add-balance`, { amount: 1000 }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        user.value = response.data
        alert('+1000 шекелей!')
      } catch (error) {
        console.error('Error adding shekels:', error)
        alert('Ошибка')
      }
    }

    const loadShopItems = async () => {
      shopLoading.value = true
      try {
        shopItems.value = await nftAPI.getShop()
      } catch (error) {
        console.error('Error loading shop:', error)
      } finally {
        shopLoading.value = false
      }
    }

    const loadUserNFTs = async () => {
      nftLoading.value = true
      try {
        userNfts.value = await nftAPI.getUserNFTs()
      } catch (error) {
        console.error('Error loading NFTs:', error)
      } finally {
        nftLoading.value = false
      }
    }

    const buyNFT = async (item) => {
      if ((user.value.balance || 0) < item.price) {
        alert('Недостаточно шекелей!')
        return
      }
      
      buyingItem.value = item.id
      try {
        const newNft = await nftAPI.buyNFT(item.id)
        userNfts.value.push(newNft)
        user.value.balance -= item.price
        alert(`Поздравляем! Вы купили "${item.name}"!`)
      } catch (error) {
        console.error('Error buying NFT:', error)
        alert(error.response?.data?.detail || 'Ошибка покупки')
      } finally {
        buyingItem.value = null
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU')
    }

    const getInitials = (name) => {
      if (!name) return '?'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const triggerAvatarUpload = () => {
      avatarInput.value?.click()
    }

    const handleAvatarChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      if (file.size > 2 * 1024 * 1024) {
        alert('Файл слишком большой. Максимум 2 МБ')
        return
      }
      
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await axios.post(`${API_BASE_URL}/users/me/avatar`, formData, {
          headers: { 
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'multipart/form-data'
          }
        })
        user.value = response.data
        alert('Аватарка загружена!')
      } catch (error) {
        console.error('Error uploading avatar:', error)
        alert('Ошибка загрузки аватарки')
      }
      event.target.value = ''
    }

    const handleAvatarDelete = async () => {
      if (!confirm('Удалить аватарку?')) return
      
      try {
        const response = await axios.delete(`${API_BASE_URL}/users/me/avatar`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        user.value = response.data
        alert('Аватарка удалена')
      } catch (error) {
        console.error('Error deleting avatar:', error)
        alert('Ошибка удаления аватарки')
      }
    }

    const doTransfer = async () => {
      if (!transferEmail.value || !transferAmount.value || transferAmount.value <= 0) {
        transferError.value = 'Заполните все поля'
        return
      }
      
      if (transferAmount.value > user.value.balance) {
        transferError.value = 'Недостаточно шекелей'
        return
      }
      
      transferring.value = true
      transferError.value = ''
      
      try {
        // Найдём пользователя по email
        const searchResponse = await axios.get(`${API_BASE_URL}/users/search?query=${transferEmail.value}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        
        const recipient = searchResponse.data.data.find(u => u.email === transferEmail.value)
        if (!recipient) {
          transferError.value = 'Пользователь не найден'
          return
        }
        
        await axios.post(`${API_BASE_URL}/users/me/transfer`, {
          recipient_id: recipient.id,
          amount: transferAmount.value
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        
        user.value.balance -= transferAmount.value
        showTransferModal.value = false
        transferEmail.value = ''
        transferAmount.value = 0
        alert('Перевод выполнен!')
      } catch (error) {
        console.error('Error transferring:', error)
        transferError.value = error.response?.data?.detail || 'Ошибка перевода'
      } finally {
        transferring.value = false
      }
    }

    const startEditName = () => {
      editedName.value = user.value.full_name || ''
      editingName.value = true
    }

    const cancelEditName = () => {
      editingName.value = false
      editedName.value = ''
    }

    const saveName = async () => {
      if (editedName.value === (user.value.full_name || '')) {
        cancelEditName()
        return
      }
      
      savingName.value = true
      try {
        const response = await axios.patch(`${API_BASE_URL}/users/me`, {
          full_name: editedName.value || null
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        user.value = response.data
        editingName.value = false
        alert('Имя сохранено!')
      } catch (error) {
        console.error('Error saving name:', error)
        alert('Ошибка сохранения')
      } finally {
        savingName.value = false
      }
    }

    const handleDelete = async () => {
      if (!confirm('Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо.')) {
        return
      }

      deleting.value = true
      try {
        await axios.delete(`${API_BASE_URL}/users/me`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
        })
        localStorage.removeItem('access_token')
        alert('Аккаунт успешно удален')
        router.push('/login')
      } catch (error) {
        console.error('Error deleting account:', error)
        alert('Ошибка удаления аккаунта')
      } finally {
        deleting.value = false
      }
    }

    const goBack = () => {
      router.push('/')
    }

    onMounted(() => {
      loadUser()
    })

    return {
      user,
      loading,
      deleting,
      avatarInput,
      editingName,
      editedName,
      showTransferModal,
      transferEmail,
      transferAmount,
      transferError,
      nftTab,
      shopItems,
      shopLoading,
      userNfts,
      nftLoading,
      buyingItem,
      getInitials,
      triggerAvatarUpload,
      handleAvatarChange,
      handleAvatarDelete,
      addShekels,
      doTransfer,
      startEditName,
      cancelEditName,
      saveName,
      handleDelete,
      goBack,
      loadUserNFTs,
      buyNFT,
      formatDate,
    }
  },
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
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

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-weight: 500;
}

.back-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.header h1 {
  margin: 0;
  flex: 1;
  text-align: center;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.profile-content {
  background: var(--bg-card);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.profile-card h2 {
  margin-top: 0;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border-color);
}

.avatar-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid var(--primary-purple);
}

.avatar-wrapper:hover {
  transform: scale(1.05);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  font-size: 2.5rem;
  font-weight: 700;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay span {
  font-size: 2rem;
}

.remove-avatar-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: var(--error);
  cursor: pointer;
}

.profile-info {
  margin-bottom: 2rem;
}

.info-item {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.info-item label {
  font-weight: 500;
  width: 150px;
  color: var(--text-secondary);
}

.info-item span {
  color: var(--text-primary);
}

.balance-section {
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: rgba(147, 51, 234, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(147, 51, 234, 0.3);
}

.balance-section h3 {
  margin: 0 0 1rem 0;
  color: var(--text-primary);
}

.balance-display {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.balance-amount {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-purple-light);
}

.balance-label {
  color: var(--text-secondary);
}

.balance-actions {
  display: flex;
  gap: 0.5rem;
}

.transfer-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-purple);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.transfer-btn:hover {
  background: var(--primary-purple-light);
}

.add-balance-btn {
  padding: 0.5rem 1rem;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-balance-btn:hover {
  background: rgba(34, 197, 94, 0.3);
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

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.modal-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
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
  border-radius: 6px;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-purple);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.cancel-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-card-hover);
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
}

.transfer-confirm-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-purple);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.transfer-confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: var(--error);
  font-size: 0.875rem;
}

.edit-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.name-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--primary-purple);
  border-radius: 6px;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
}

.edit-btn, .save-btn, .cancel-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem 0.5rem;
}

.edit-btn:hover {
  opacity: 0.7;
}

.save-btn {
  color: #22c55e;
}

.cancel-btn {
  color: var(--error);
}

.danger-zone {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.danger-zone h3 {
  margin-top: 0;
  color: var(--error);
}

.danger-zone p {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.delete-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  cursor: pointer;
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.3);
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.nft-section {
  margin: 1.5rem 0;
  padding: 1.5rem;
  background: rgba(20, 20, 30, 0.5);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.nft-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.nft-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.nft-tabs {
  display: flex;
  gap: 0.5rem;
}

.nft-tabs button {
  padding: 0.5rem 1rem;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.nft-tabs button.active {
  background: var(--primary-purple);
  border-color: var(--primary-purple);
  color: white;
}

.nft-tabs button:hover:not(.active) {
  border-color: var(--primary-purple);
  color: var(--text-primary);
}

.nft-shop, .nft-collection {
  min-height: 200px;
}

.nft-loading, .nft-empty {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.nft-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.nft-card {
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.nft-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(147, 51, 234, 0.2);
}

.nft-card.common {
  border-color: rgba(156, 163, 175, 0.3);
}

.nft-card.rare {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
}

.nft-card.epic {
  border-color: rgba(168, 85, 247, 0.5);
  box-shadow: 0 0 15px rgba(168, 85, 247, 0.3);
}

.nft-card.legendary {
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
}

.nft-card.owned {
  opacity: 0.9;
}

.nft-image {
  width: 100%;
  aspect-ratio: 1;
  background: rgba(30, 30, 40, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nft-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nft-placeholder {
  font-size: 3rem;
}

.nft-info {
  padding: 1rem;
}

.nft-info h4 {
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
  font-size: 1rem;
}

.nft-description {
  margin: 0 0 0.75rem 0;
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nft-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.nft-rarity {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.nft-rarity.common {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.nft-rarity.rare {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.nft-rarity.epic {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.nft-rarity.legendary {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.nft-price {
  color: var(--primary-purple-light);
  font-weight: 600;
}

.nft-date {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.buy-btn {
  width: 100%;
  padding: 0.75rem;
  background: var(--primary-purple);
  color: white;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s ease;
}

.buy-btn:hover:not(:disabled) {
  background: var(--primary-purple-light);
}

.buy-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>