<template>
  <div class="services-container">
    <header class="header">
      <h1>🛠 Сервисы</h1>
      <router-link to="/" class="back-link">← Назад</router-link>
    </header>

    <div class="content">
      <div class="services-grid">
        <div class="service-card" @click="router.push('/ultra')">
          <div class="service-icon">💎</div>
          <h3>Ultra</h3>
          <p>Подписка Ultra с бейджами и украшениями профиля</p>
        </div>

        <div class="service-card" @click="router.push('/bots')">
          <div class="service-icon">🤖</div>
          <h3>Боты</h3>
          <p>Создавайте и используйте ИИ ботов</p>
        </div>

        <div class="service-card" @click="router.push('/forum')">
          <div class="service-icon">📋</div>
          <h3>Форум</h3>
          <p>Обсуждения и посты с комментариями</p>
        </div>

        <div class="service-card" @click="router.push('/channels')">
          <div class="service-icon">📢</div>
          <h3>Каналы</h3>
          <p>Публичные каналы с подписчиками</p>
        </div>

        <div class="service-card" @click="showShop = true">
          <div class="service-icon">🛒</div>
          <h3>Магазин</h3>
          <p>Покупка предметов и украшений</p>
        </div>

        <div class="service-card" @click="showTransfer = true">
          <div class="service-icon">💰</div>
          <h3>Переводы</h3>
          <p>Перевод шекелей другим пользователям</p>
        </div>

        <div class="service-card" @click="showLeaderboard = true">
          <div class="service-icon">🏆</div>
          <h3>Рейтинг</h3>
          <p>Топ пользователей по балансу</p>
        </div>

        <div class="service-card" @click="showAchievements = true">
          <div class="service-icon">🎖️</div>
          <h3>Достижения</h3>
          <p>Ваши достижения и прогресс</p>
        </div>
      </div>
    </div>

    <!-- Магазин модалка -->
    <div v-if="showShop" class="modal-overlay" @click.self="showShop = false">
      <div class="modal">
        <h2>🛒 Магазин</h2>
        <div class="shop-items">
          <div v-for="item in shopItems" :key="item.id" class="shop-item">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-desc">{{ item.description }}</div>
            <div class="item-price">{{ item.price }} шекелей</div>
            <button @click="buyItem(item)" class="buy-btn">Купить</button>
          </div>
        </div>
        <button @click="showShop = false" class="close-btn">Закрыть</button>
      </div>
    </div>

    <!-- Переводы модалка -->
    <div v-if="showTransfer" class="modal-overlay" @click.self="showTransfer = false">
      <div class="modal">
        <h2>💰 Перевод шекелей</h2>
        <input v-model="transferData.recipient_email" type="text" placeholder="Email получателя" />
        <input v-model.number="transferData.amount" type="number" placeholder="Сумма" />
        <button @click="transferShekels" class="action-btn">Перевести</button>
        <button @click="showTransfer = false" class="close-btn">Закрыть</button>
      </div>
    </div>

    <!-- Рейтинг модалка -->
    <div v-if="showLeaderboard" class="modal-overlay" @click.self="showLeaderboard = false">
      <div class="modal">
        <h2>🏆 Топ пользователей</h2>
        <div class="leaderboard">
          <div v-for="(user, index) in leaderboard" :key="user.id" class="leaderboard-item">
            <span class="rank">{{ index + 1 }}</span>
            <span class="name">{{ user.full_name || user.email }}</span>
            <span class="balance">{{ user.balance }} ₪</span>
          </div>
        </div>
        <button @click="showLeaderboard = false" class="close-btn">Закрыть</button>
      </div>
    </div>

    <!-- Достижения модалка -->
    <div v-if="showAchievements" class="modal-overlay" @click.self="showAchievements = false">
      <div class="modal">
        <h2>🎖️ Ваши достижения</h2>
        <div class="achievements">
          <div v-for="achievement in achievements" :key="achievement.id" class="achievement">
            <div class="achievement-icon">{{ achievement.icon }}</div>
            <div class="achievement-name">{{ achievement.name }}</div>
            <div class="achievement-desc">{{ achievement.description }}</div>
            <span v-if="achievement.unlocked" class="unlocked">Получено</span>
            <span v-else class="locked">Заблокировано</span>
          </div>
        </div>
        <button @click="showAchievements = false" class="close-btn">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { default as api } from '../services/api'

const router = useRouter()
const showShop = ref(false)
const showTransfer = ref(false)
const showLeaderboard = ref(false)
const showAchievements = ref(false)

const shopItems = ref([])
const leaderboard = ref([])
const achievements = ref([
  { id: 1, icon: '💬', name: 'Чатка', description: 'Отправить 100 сообщений', unlocked: false },
  { id: 2, icon: '👥', name: 'Командный игрок', description: 'Создать 5 групп', unlocked: false },
  { id: 3, icon: '📢', name: 'Вещатель', description: 'Создать канал', unlocked: false },
  { id: 4, icon: '💎', name: 'Премиум', description: 'Купить Ultra', unlocked: false },
  { id: 5, icon: '🤖', name: 'Создатель', description: 'Создать бота', unlocked: false },
  { id: 6, icon: '💰', name: 'Богач', description: 'Накопить 1000 шекелей', unlocked: false },
])

const transferData = ref({
  recipient_email: '',
  amount: 0,
})

onMounted(async () => {
  try {
    const shopRes = await api.get('/ultra/shop')
    shopItems.value = shopRes.data?.data || []
  } catch (e) {
    shopItems.value = [
      { id: 1, name: 'Золотой ник', description: 'Золотой цвет ника', price: 500 },
      { id: 2, name: 'Анимированный аватар', description: 'Анимированный аватар', price: 1000 },
    ]
  }

  try {
    const lbRes = await api.get('/users/leaderboard')
    leaderboard.value = lbRes.data || []
  } catch (e) {
    leaderboard.value = []
  }
})

const buyItem = async (item) => {
  try {
    await api.post('/ultra/buy-item', { item_id: item.id })
    alert('Успешно куплено!')
    showShop.value = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка покупки')
  }
}

const transferShekels = async () => {
  if (!transferData.value.recipient_email || !transferData.value.amount) {
    alert('Заполните все поля')
    return
  }
  try {
    const userRes = await api.get('/users/search?q=' + transferData.value.recipient_email)
    const users = userRes.data || []
    const recipient = users.find(u => u.email === transferData.value.recipient_email)
    if (!recipient) {
      alert('Пользователь не найден')
      return
    }
    await api.post('/ultra/transfer', {
      recipient_id: recipient.id,
      amount: transferData.value.amount,
    })
    alert('Перевод выполнен!')
    showTransfer.value = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка перевода')
  }
}
</script>

<style scoped>
.services-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
}

.header h1 {
  margin: 0;
}

.back-link {
  color: #4ecdc4;
  text-decoration: none;
}

.content {
  padding: 20px;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.service-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.service-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.2);
}

.service-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.service-card h3 {
  margin: 10px 0;
}

.service-card p {
  font-size: 14px;
  opacity: 0.8;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1a1a2e;
  border-radius: 15px;
  padding: 30px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal h2 {
  margin-top: 0;
}

.shop-items, .achievements {
  display: grid;
  gap: 15px;
}

.shop-item, .achievement {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 15px;
}

.item-price {
  color: #ffd700;
  font-weight: bold;
}

.buy-btn {
  background: #4ecdc4;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 10px;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.rank {
  font-size: 20px;
  font-weight: bold;
  color: #ffd700;
}

.balance {
  color: #4ecdc4;
}

.close-btn {
  background: #ff6b6b;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 20px;
  width: 100%;
}

input {
  width: 100%;
  padding: 12px;
  margin-bottom: 10px;
  border: none;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.action-btn {
  width: 100%;
  padding: 12px;
  background: #4ecdc4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-bottom: 10px;
}

.unlocked {
  color: #4ecdc4;
}

.locked {
  color: #666;
}
</style>