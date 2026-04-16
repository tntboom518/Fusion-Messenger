<template>
  <div class="ultra-container">
    <header class="ultra-header">
      <button @click="goBack" class="back-btn">← Назад</button>
      <h1>⚡ Fusion Ultra</h1>
    </header>

    <div class="ultra-content">
      <!-- Текущий статус -->
      <div :class="['ultra-status-card', { active: ultraStatus.is_ultra }]">
        <div class="status-icon">{{ ultraStatus.is_ultra ? '⚡' : '🔌' }}</div>
        <div class="status-info">
          <h2>{{ ultraStatus.is_ultra ? 'Ultra АКТИВЕН' : 'Ultra НЕ АКТИВЕН' }}</h2>
          <p v-if="ultraStatus.is_ultra && ultraStatus.expires_at">
            Действует до: {{ formatDate(ultraStatus.expires_at) }}
          </p>
          <p v-else>Купите подписку для доступа к эксклюзивным функциям!</p>
        </div>
      </div>

      <!-- Покупка (только для не Ultra) -->
      <div v-if="!ultraStatus.is_ultra" class="buy-section">
        <h3>Купить подписку</h3>
        <div class="price-info">
          <span class="price">1000 ₪</span>
          <span class="period">за 1 день</span>
        </div>
        <div class="days-select">
          <button @click="buyDays = 1" :class="{ active: buyDays === 1 }">1 день</button>
          <button @click="buyDays = 7" :class="{ active: buyDays === 7 }">7 дней</button>
          <button @click="buyDays = 30" :class="{ active: buyDays === 30 }">30 дней</button>
        </div>
        <div class="total-price">
          Итого: {{ buyDays * 1000 }} шекелей
        </div>
        <button @click="buyUltra" :disabled="buying" class="buy-btn">
          {{ buying ? 'Покупка...' : `Купить за ${buyDays * 1000} ₪` }}
        </button>
        <p class="balance-info">Ваш баланс: {{ user?.balance }} ₪</p>
      </div>

      <!-- Возможности Ultra -->
      <div class="features-section">
        <h3>✨ Возможности Ultra</h3>
        <div class="features-list">
          <div class="feature">
            <span class="feature-icon">💎</span>
            <div class="feature-info">
              <strong>Уникальные бейджи</strong>
              <p>Выделяйтесь среди других с эксклюзивными бейджами профиля</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-icon">🌈</span>
            <div class="feature-info">
              <strong>Цветной ник</strong>
              <p>Ваше имя будет отображаться с градиентом во всех чатах</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-icon">⭐</span>
            <div class="feature-info">
              <strong>Золотая рамка аватара</strong>
              <p>Ваш аватар получит золотую рамку в чатах</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-icon">🎨</span>
            <div class="feature-info">
              <strong>Тема оформления</strong>
              <p>Доступ к эксклюзивным темам оформления профиля</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-icon">🔒</span>
            <div class="feature-info">
              <strong>Приватные чаты</strong>
                <p>Возможность создавать скрытые чаты с паролем</p>
            </div>
          </div>
          <div class="feature">
            <span class="feature-icon">🎁</span>
            <div class="feature-info">
              <strong>Бонус при покупке NFT</strong>
              <p>Скидка 20% на все предметы в магазине NFT</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Бейджи (только для Ultra) -->
      <div v-if="ultraStatus.is_ultra" class="badges-section">
        <h3>🎭 Ваш бейдж</h3>
        <div class="badges-grid">
          <button
            v-for="badge in ultraStatus.badges"
            :key="badge.id"
            :class="['badge-btn', { active: ultraStatus.badge === badge.id }]"
            @click="setBadge(badge.id)"
          >
            <span class="badge-emoji">{{ badge.emoji }}</span>
            <span class="badge-name">{{ badge.name }}</span>
          </button>
        </div>
        <p v-if="ultraStatus.badge" class="current-badge">
          Текущий бейдж: {{ getCurrentBadge() }}
        </p>
      </div>

      <!-- Настройки профиля Ultra -->
      <div v-if="ultraStatus.is_ultra" class="customize-section">
        <h3>🎨 Кастомизация профиля</h3>
        
        <div class="custom-option">
          <label>Цвет ника в чате:</label>
          <div class="color-options">
            <button
              v-for="color in nameColors"
              :key="color.value"
              :style="{ background: color.value }"
              :class="['color-btn', { active: profileColor === color.value }]"
              @click="setProfileColor(color.value)"
            ></button>
          </div>
        </div>

        <div class="custom-option">
          <label>Стиль аватара:</label>
          <div class="avatar-styles">
            <button
              v-for="style in avatarStyles"
              :key="style.value"
              :class="['style-btn', { active: avatarStyle === style.value }]"
              @click="setAvatarStyle(style.value)"
            >
              {{ style.label }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ultraAPI, authAPI } from '../services/api'

export default {
  name: 'Ultra',
  setup() {
    const router = useRouter()
    const user = ref(null)
    const ultraStatus = ref({ is_ultra: false, expires_at: null, badge: null, badges: [] })
    const buyDays = ref(1)
    const buying = ref(false)
    const profileColor = ref('#ffffff')
    const avatarStyle = ref('default')

    const nameColors = [
      { label: 'Белый', value: '#ffffff' },
      { label: 'Золотой', value: '#ffd700' },
      { label: 'Розовый', value: '#ff69b4' },
      { label: 'Синий', value: '#00bfff' },
      { label: 'Зелёный', value: '#00ff7f' },
      { label: 'Фиолетовый', value: '#9400d3' },
      { label: 'Оранжевый', value: '#ff4500' },
      { label: 'Радуга', value: 'linear-gradient(90deg, red, orange, yellow, green, blue, violet)' },
    ]

    const avatarStyles = [
      { label: 'Стандарт', value: 'default' },
      { label: 'Золото', value: 'gold' },
      { label: 'Рамка', value: 'border' },
      { label: 'Блик', value: 'shine' },
    ]

    const loadData = async () => {
      try {
        user.value = await authAPI.getCurrentUser()
        ultraStatus.value = await ultraAPI.getStatus()
      } catch (e) {
        console.error('Error loading data:', e)
      }
    }

    const buyUltra = async () => {
      if (user.value.balance < buyDays.value * 1000) {
        alert('Недостаточно шекелей!')
        return
      }
      buying.value = true
      try {
        const res = await ultraAPI.buy(buyDays.value)
        user.value = res
        ultraStatus.value = await ultraAPI.getStatus()
        alert(`Успешно! Вы приобрели Ultra на ${buyDays.value} дней`)
      } catch (e) {
        alert('Ошибка покупки: ' + (e.response?.data?.detail || e.message))
      } finally {
        buying.value = false
      }
    }

    const setBadge = async (badgeId) => {
      try {
        await ultraAPI.setBadge(badgeId)
        ultraStatus.value = await ultraAPI.getStatus()
      } catch (e) {
        console.error('Error setting badge:', e)
      }
    }

    const setProfileColor = async (color) => {
      profileColor.value = color
      localStorage.setItem('ultra_profile_color', color)
      try {
        await ultraAPI.setProfileStyle(color, avatarStyle.value)
      } catch (e) {
        console.error('Error saving profile color:', e)
      }
    }

    const setAvatarStyle = async (style) => {
      avatarStyle.value = style
      localStorage.setItem('ultra_avatar_style', style)
      try {
        await ultraAPI.setProfileStyle(profileColor.value, style)
      } catch (e) {
        console.error('Error saving avatar style:', e)
      }
    }

    const getCurrentBadge = () => {
      const badge = ultraStatus.value.badges?.find(b => b.id === ultraStatus.value.badge)
      return badge ? `${badge.emoji} ${badge.name}` : 'Нет'
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
    }

    const goBack = () => {
      router.push('/profile')
    }

    onMounted(() => {
      loadData()
      profileColor.value = localStorage.getItem('ultra_profile_color') || '#ffffff'
      avatarStyle.value = localStorage.getItem('ultra_avatar_style') || 'default'
    })

    return {
      user,
      ultraStatus,
      buyDays,
      buying,
      profileColor,
      avatarStyle,
      nameColors,
      avatarStyles,
      buyUltra,
      setBadge,
      setProfileColor,
      setAvatarStyle,
      getCurrentBadge,
      formatDate,
      goBack,
    }
  },
}
</script>

<style scoped>
.ultra-container {
  max-width: 600px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-dark, #1a1a2e);
  color: var(--text-primary, #eee);
}

.ultra-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  border-bottom: 1px solid var(--border-color, #333);
}

.ultra-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #000;
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.2);
  border: none;
  border-radius: 8px;
  color: #000;
  cursor: pointer;
  font-weight: 600;
}

.ultra-content {
  padding: 1rem;
}

.ultra-status-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  margin-bottom: 1.5rem;
  border: 2px solid #333;
}

.ultra-status-card.active {
  border-color: #ffd700;
  background: linear-gradient(135deg, #1a1a2e 0%, #2a2a1e 100%);
}

.status-icon {
  font-size: 3rem;
}

.status-info h2 {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
}

.status-info p {
  margin: 0;
  color: var(--text-secondary, #999);
  font-size: 0.9rem;
}

.buy-section {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  text-align: center;
}

.buy-section h3 {
  margin: 0 0 1rem;
  color: var(--primary-purple-light, #a855f7);
}

.price-info {
  margin-bottom: 1rem;
}

.price {
  font-size: 2rem;
  font-weight: bold;
  color: #ffd700;
}

.period {
  color: var(--text-secondary, #999);
}

.days-select {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.days-select button {
  padding: 0.5rem 1rem;
  background: var(--bg-dark, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
}

.days-select button.active {
  background: var(--primary-purple, #9333ea);
  border-color: var(--primary-purple, #9333ea);
}

.total-price {
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.buy-btn {
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  border: none;
  border-radius: 12px;
  color: #000;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s;
}

.buy-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.buy-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.balance-info {
  margin-top: 1rem;
  color: var(--text-secondary, #999);
  font-size: 0.9rem;
}

.features-section {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.features-section h3 {
  margin: 0 0 1rem;
  color: var(--primary-purple-light, #a855f7);
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--bg-dark, #1a1a2e);
  border-radius: 8px;
}

.feature-icon {
  font-size: 1.5rem;
}

.feature-info strong {
  display: block;
  margin-bottom: 0.25rem;
}

.feature-info p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary, #999);
}

.badges-section {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.badges-section h3 {
  margin: 0 0 1rem;
  color: var(--primary-purple-light, #a855f7);
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.badge-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 1rem 0.5rem;
  background: var(--bg-dark, #1a1a2e);
  border: 2px solid var(--border-color, #333);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.badge-btn:hover {
  border-color: #ffd700;
}

.badge-btn.active {
  border-color: #ffd700;
  background: rgba(255, 215, 0, 0.1);
}

.badge-emoji {
  font-size: 1.5rem;
}

.badge-name {
  font-size: 0.75rem;
  color: var(--text-secondary, #999);
}

.current-badge {
  margin-top: 1rem;
  text-align: center;
  color: #ffd700;
  font-weight: 600;
}

.customize-section {
  background: var(--bg-card, #16213e);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.customize-section h3 {
  margin: 0 0 1rem;
  color: var(--primary-purple-light, #a855f7);
}

.custom-option {
  margin-bottom: 1.5rem;
}

.custom-option label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary, #999);
}

.color-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.color-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
}

.color-btn.active {
  border-color: #fff;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.avatar-styles {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.style-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-dark, #1a1a2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-primary, #eee);
  cursor: pointer;
}

.style-btn.active {
  background: var(--primary-purple, #9333ea);
  border-color: var(--primary-purple, #9333ea);
}
</style>