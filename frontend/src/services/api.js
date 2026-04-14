import axios from 'axios'

const API_BASE_URL = '/api/v1'

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для добавления токена к запросам
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API методы
export const authAPI = {
  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    const response = await axios.post(`${API_BASE_URL}/login/access-token`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  register: async (email, password, fullName) => {
    const response = await api.post('/users/signup', {
      email,
      password,
      full_name: fullName || null,
    })
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me')
    return response.data
  },
  
  uploadAvatar: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await axios.post(`${API_BASE_URL}/users/me/avatar`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  deleteAvatar: async () => {
    const response = await axios.delete(`${API_BASE_URL}/users/me/avatar`)
    return response.data
  },
  
  transferShekels: async (recipientId, amount) => {
    const response = await axios.post(`${API_BASE_URL}/users/me/transfer`, {
      recipient_id: recipientId,
      amount: amount
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    return response.data
  },
  
  addBalance: async (amount) => {
    const response = await axios.post(`${API_BASE_URL}/users/me/add-balance`, { amount }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    return response.data
  },
  
  deleteAccount: async () => {
    const response = await api.delete('/users/me')
    return response.data
  },
}

export const usersAPI = {
  search: async (query) => {
    const response = await api.get('/users/search', { params: { query } })
    return response.data
  },
  
  getAll: async (skip = 0, limit = 100) => {
    const response = await api.get('/users/all', { params: { skip, limit } })
    return response.data
  },
  
  banUser: async (userId, reason = null) => {
    const response = await api.post(`/users/${userId}/ban`, reason ? { reason } : {})
    return response.data
  },
  
  unbanUser: async (userId) => {
    const response = await api.post(`/users/${userId}/unban`)
    return response.data
  },
  
  deleteUser: async (userId) => {
    const response = await api.delete(`/users/${userId}`)
    return response.data
  },
}

export const chatsAPI = {
  getChats: async () => {
    const response = await api.get('/chats/')
    return response.data
  },
  
  getChat: async (chatId) => {
    const response = await api.get(`/chats/${chatId}`)
    return response.data
  },
  
  createPrivateChat: async (userId) => {
    const response = await api.post(`/chats/private/${userId}`)
    return response.data
  },
  
  createGroupChat: async (name, memberIds) => {
    const response = await api.post('/chats/group', {
      chat_type: 'group',
      name: name,
      member_ids: memberIds,
    })
    return response.data
  },
  
  addMembersToGroup: async (chatId, memberIds) => {
    const response = await api.post(`/chats/${chatId}/members`, {
      member_ids: memberIds,
    })
    return response.data
  },
  
  getMessages: async (chatId, skip = 0, limit = 50) => {
    const response = await api.get(`/chats/${chatId}/messages`, {
      params: { skip, limit },
    })
    return response.data
  },
  
  updateMemberRole: async (chatId, memberId, role) => {
    const response = await api.patch(`/chats/${chatId}/members/${memberId}/role`, { role })
    return response.data
  },
  
  removeMember: async (chatId, memberId) => {
    const response = await api.delete(`/chats/${chatId}/members/${memberId}`)
    return response.data
  },
  
  leaveChat: async (chatId) => {
    const response = await api.post(`/chats/${chatId}/leave`)
    return response.data
  },
  
  updateChatName: async (chatId, name) => {
    const response = await api.patch(`/chats/${chatId}/name`, { name })
    return response.data
  },
}

export const messagesAPI = {
  sendMessage: async (chatId, content, mediaData = null) => {
    console.log('messagesAPI.sendMessage called:', { chatId, content, mediaData })
    const payload = { content }
    if (mediaData) {
      payload.media_type = mediaData.media_type
      payload.media_filename = mediaData.media_filename
      payload.media_url = mediaData.media_url
      payload.media_size = mediaData.media_size
    }
    console.log('Sending payload to API:', payload)
    const response = await api.post(`/media/${chatId}`, payload)
    return response.data
  },
  
  uploadMedia: async (file) => {
    console.log('messagesAPI.uploadMedia called:', file.name, file.type, file.size)
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/media/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    console.log('Upload response:', response.data)
    return response.data
  },
  
  deleteMessage: async (messageId) => {
    const response = await api.delete(`/messages/${messageId}`)
    return response.data
  },
}

export const nftAPI = {
  getShop: async () => {
    const response = await api.get('/users/shop')
    return response.data
  },
  
  getUserNFTs: async () => {
    const response = await api.get('/users/me/nfts')
    return response.data
  },
  
  buyNFT: async (itemId) => {
    const response = await api.post('/users/me/buy', { item_id: itemId })
    return response.data
  },
}

export default api

