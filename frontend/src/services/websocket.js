// WebSocket сервис для чата
export class ChatWebSocket {
  constructor(chatId, token, onMessage, onError) {
    this.chatId = chatId
    this.token = token
    this.onMessage = onMessage
    this.onError = onError
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  connect() {
    // Для локальной разработки используем localhost:8000, для прода - текущий хост
    const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    
    let wsUrl
    if (isLocalDev) {
      // Локальная разработка - подключаемся напрямую к бэкенду
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//localhost:8000/api/v1/ws/${this.chatId}?token=${this.token}`
      console.log('Local dev - connecting to:', wsUrl)
    } else {
      // Продакшен - используем относительный путь через nginx
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${this.chatId}?token=${this.token}`
      console.log('Production - connecting to:', wsUrl)
    }
    
    console.log('WebSocket connection details:', {
      hostname: window.location.hostname,
      isLocalDev,
      wsUrl
    })
    
    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected successfully')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          if (this.onMessage) {
            this.onMessage(data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error details:', {
          target: error.target,
          readyState: error.target?.readyState,
          url: error.target?.url,
        })
        if (this.onError) {
          this.onError(error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })
        // Попытка переподключения
        if (this.reconnectAttempts < this.maxReconnectAttempts && event.code !== 1008) {
          this.reconnectAttempts++
          setTimeout(() => {
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
            this.connect()
          }, 1000 * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      if (this.onError) {
        this.onError(error)
      }
    }
  }

  sendMessage(content, mediaData = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const messagePayload = {
        type: 'message',
        content: content,
      }
      if (mediaData) {
        messagePayload.media_type = mediaData.media_type
        messagePayload.media_filename = mediaData.media_filename
        messagePayload.media_url = mediaData.media_url
        messagePayload.media_size = mediaData.media_size
      }
      console.log('Sending WebSocket message:', messagePayload)
      this.ws.send(JSON.stringify(messagePayload))
    } else {
      console.error('WebSocket is not connected. State:', this.ws?.readyState)
    }
  }

  sendTyping() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing',
      }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}