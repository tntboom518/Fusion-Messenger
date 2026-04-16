<template>
  <div class="page">
    <div class="top-bar">
      <router-link to="/" class="back">← Назад</router-link>
      <h1>Боты</h1>
    </div>
    
    <button class="btn-primary" @click="showCreateForm = true">+ Создать бота</button>
    
    <div v-if="error" class="error">{{ error }}</div>
    
    <!-- Create Bot Form -->
    <div v-if="showCreateForm" class="form-box">
      <h2>Создать бота</h2>
      <input v-model="newBot.name" placeholder="Имя бота" class="input" />
      <textarea v-model="newBot.description" placeholder="Описание" class="input"></textarea>
      <select v-model="newBot.language" class="input">
        <option value="python">Python</option>
        <option value="javascript">JavaScript</option>
      </select>
      <textarea v-model="newBot.code" placeholder="Код бота" class="input code"></textarea>
      <div class="hint">
        Доступно: message, user_name, user_id<br>
        Ответ: response = "текст"
      </div>
      <label class="checkbox-label">
        <input type="checkbox" v-model="newBot.is_public" />
        Публичный бот (доступен всем)
      </label>
      <div class="actions">
        <button @click="showCreateForm = false" class="btn-secondary">Отмена</button>
        <button @click="saveBot" class="btn-primary" :disabled="saving">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
    
    <!-- Bot List with Chat -->
    <div class="bots-grid">
      <div v-for="bot in bots" :key="bot.id" class="bot-item">
        <div class="bot-header">
          <div class="bot-name">{{ bot.name }}</div>
          <div class="bot-status" :class="{ active: bot.is_active }">
            {{ bot.is_active ? 'Включен' : 'Выключен' }}
          </div>
        </div>
        <div class="bot-desc">{{ bot.description || 'Нет описания' }}</div>
        
        <!-- Chat with Bot -->
        <div class="bot-chat">
          <div class="chat-messages">
            <div v-for="(msg, i) in botMessages[bot.id] || []" :key="i" :class="['msg', msg.from]">
              {{ msg.text }}
            </div>
          </div>
          <div class="chat-input">
            <input 
              v-model="botInputs[bot.id]" 
              placeholder="Напиши боту..." 
              class="input"
              @keyup.enter="sendToBot(bot)"
            />
            <button @click="sendToBot(bot)" class="btn-small">Отправить</button>
          </div>
        </div>
        
        <div class="bot-actions">
          <button @click="deleteBot(bot)" class="btn-small danger">Удалить</button>
        </div>
      </div>
    </div>
    
    <p v-if="bots.length === 0 && !loading && !showCreateForm">Нет ботов</p>
    <p v-if="loading">Загрузка...</p>
  </div>
</template>

<script>
import { onMounted, ref, reactive } from 'vue'
import { botsAPI } from '../services/api'

export default {
  name: 'Bots',
  setup() {
    const bots = ref([])
    const loading = ref(false)
    const error = ref('')
    const showCreateForm = ref(false)
    const saving = ref(false)
    
    const botMessages = reactive({})
    const botInputs = reactive({})
    
    const newBot = reactive({
      name: '',
      description: '',
      code: '',
      language: 'python',
      is_public: false
    })
    
    const loadBots = async () => {
      loading.value = true
      error.value = ''
      try {
        const response = await botsAPI.getAllBots()
        bots.value = response || []
        // Инициализируем сообщения для каждого бота
        for (const bot of bots.value) {
          if (!botMessages[bot.id]) {
            botMessages[bot.id] = []
            botInputs[bot.id] = ''
          }
        }
      } catch (e) {
        error.value = 'Ошибка загрузки'
        console.error(e)
      }
      loading.value = false
    }
    
    const saveBot = async () => {
      if (!newBot.name || !newBot.code) {
        alert('Введите имя и код бота')
        return
      }
      saving.value = true
      try {
        await botsAPI.createBot({
          name: newBot.name,
          description: newBot.description,
          code: newBot.code,
          language: newBot.language,
          is_public: newBot.is_public
        })
        showCreateForm.value = false
        newBot.name = ''
        newBot.description = ''
        newBot.code = ''
        newBot.language = 'python'
        newBot.is_public = false
        await loadBots()
      } catch (e) {
        console.error(e)
        alert('Ошибка создания бота')
      }
      saving.value = false
    }
    
    const deleteBot = async (bot) => {
      if (!confirm(`Удалить бота ${bot.name}?`)) return
      try {
        await botsAPI.deleteBot(bot.id)
        await loadBots()
      } catch (e) {
        alert('Ошибка удаления')
      }
    }
    
    const sendToBot = async (bot) => {
      const text = botInputs[bot.id]?.trim()
      if (!text) return
      
      // Добавляем сообщение пользователя
      if (!botMessages[bot.id]) {
        botMessages[bot.id] = []
      }
      botMessages[bot.id].push({ from: 'user', text })
      botInputs[bot.id] = ''
      
      try {
        const res = await botsAPI.chatWithBot(bot.id, text)
        botMessages[bot.id].push({ from: 'bot', text: res.response })
      } catch (e) {
        botMessages[bot.id].push({ from: 'bot', text: 'Ошибка' })
      }
    }
    
    onMounted(loadBots)
    
    return {
      bots, loading, error, showCreateForm, saving,
      newBot, botMessages, botInputs,
      saveBot, deleteBot, sendToBot
    }
  }
}
</script>

<style>
.page {
  padding: 20px;
  color: white;
  background: #1a1a2e;
  min-height: 100vh;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.back {
  color: #9333ea;
  text-decoration: none;
  font-size: 18px;
}

.btn-primary {
  padding: 12px 24px;
  background: #9333ea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary:disabled {
  background: #666;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 12px 24px;
  background: transparent;
  color: white;
  border: 1px solid #666;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.btn-small {
  padding: 8px 12px;
  background: #333;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-small.danger {
  background: #dc2626;
}

.error {
  color: red;
  padding: 10px;
  background: rgba(255,0,0,0.1);
  border-radius: 8px;
  margin: 10px 0;
}

.form-box {
  background: #16213e;
  padding: 20px;
  border-radius: 12px;
  margin: 20px 0;
}

.form-box h2 {
  margin-top: 0;
}

.input {
  width: 100%;
  padding: 12px;
  margin: 8px 0;
  background: #0f3460;
  border: 1px solid #333;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  box-sizing: border-box;
}

.code {
  font-family: monospace;
  min-height: 150px;
}

.hint {
  font-size: 12px;
  color: #666;
  margin: 10px 0;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.bot-item {
  background: #252545;
  border-radius: 12px;
  padding: 16px;
}

.bot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bot-name {
  font-size: 18px;
  font-weight: bold;
  color: white;
}

.bot-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #444;
  color: #888;
}

.bot-status.active {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.bot-desc {
  color: #888;
  margin: 8px 0;
  font-size: 14px;
}

.bot-chat {
  margin-top: 12px;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
}

.chat-messages {
  height: 150px;
  overflow-y: auto;
  padding: 10px;
  background: #1a1a2e;
}

.msg {
  padding: 6px 10px;
  margin: 4px 0;
  border-radius: 8px;
  font-size: 14px;
}

.msg.user {
  background: #9333ea;
  color: white;
  margin-left: 20px;
}

.msg.bot {
  background: #333;
  color: white;
  margin-right: 20px;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #252545;
}

.chat-input .input {
  flex: 1;
  padding: 8px;
  border: 1px solid #333;
  border-radius: 6px;
  background: #1a1a2e;
  color: white;
}

.bot-actions {
  margin-top: 12px;
}

.error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.bot-item {
  background: #16213e;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #333;
}

.bot-name {
  font-size: 18px;
  font-weight: bold;
  color: #9333ea;
}

.bot-desc {
  color: #aaa;
  font-size: 14px;
  margin: 8px 0;
}

.bot-lang {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
}

.bot-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #333;
  display: inline-block;
  margin: 8px 0;
}

.bot-status.active {
  background: #22c55e;
  color: white;
}

.bot-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #16213e;
  padding: 24px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
}

.modal-content h3 {
  margin-top: 0;
}

.response {
  margin-top: 15px;
  padding: 12px;
  background: #0f3460;
  border-radius: 8px;
  color: #22c55e;
}

.chat-modal {
  max-width: 500px;
  height: 80vh;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #0f3460;
  border-radius: 8px;
  margin: 10px 0;
  max-height: 400px;
}

.msg {
  padding: 8px 12px;
  border-radius: 8px;
  margin: 8px 0;
  max-width: 80%;
}

.msg.user {
  background: #9333ea;
  margin-left: auto;
}

.msg.bot {
  background: #333;
}

.chat-input {
  display: flex;
  gap: 10px;
}

.chat-input .input {
  flex: 1;
}
</style>