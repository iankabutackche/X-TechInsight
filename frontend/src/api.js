/**
 * api.js — 前端与 FastAPI 后端的通信封装
 *
 * 通过 Vite 代理，请求会转发到 http://127.0.0.1:8000
 */

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data.detail || data.message || `请求失败 (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  return data
}

export async function healthCheck() {
  const response = await fetch('/health')
  return parseJsonResponse(response)
}

export async function createChat(name, tag = 'general') {
  const response = await fetch('/chats/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, tag }),
  })

  return parseJsonResponse(response)
}

export async function listChats() {
  const response = await fetch('/chats/list')
  return parseJsonResponse(response)
}

export async function getChatMessages(chatId) {
  const response = await fetch(`/chats/${chatId}/messages`)
  return parseJsonResponse(response)
}

export async function updateChat(chatId, { name, tag } = {}) {
  const response = await fetch(`/chats/${chatId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, tag }),
  })

  return parseJsonResponse(response)
}

export async function uploadFile(file, tag = 'general') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('tag', tag)

  const response = await fetch('/files/upload', {
    method: 'POST',
    body: formData,
  })

  return parseJsonResponse(response)
}

function parseSSEBlock(rawBlock) {
  let eventName = 'message'
  let dataLine = ''

  for (const line of rawBlock.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLine = line.slice(5).trim()
    }
  }

  if (!dataLine) {
    return { eventName, data: null }
  }

  try {
    return { eventName, data: JSON.parse(dataLine) }
  } catch {
    return { eventName, data: dataLine }
  }
}

/**
 * 流式问答（SSE）
 *
 * @param {object} params
 * @param {string} params.chatId
 * @param {string} params.question
 * @param {(content: string) => void} params.onToken
 * @param {(sources: Array) => void} params.onSources
 * @param {() => void} params.onDone
 * @param {(message: string) => void} params.onError
 */
export async function streamQuery({
  chatId,
  question,
  onToken,
  onSources,
  onDone,
  onError,
}) {
  const response = await fetch('/query/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      question,
    }),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const message = data.detail || `流式请求失败 (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const rawBlock = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)

      const { eventName, data } = parseSSEBlock(rawBlock)

      if (eventName === 'token' && data?.content) {
        onToken?.(data.content)
      } else if (eventName === 'sources') {
        onSources?.(data || [])
      } else if (eventName === 'done') {
        onDone?.()
      } else if (eventName === 'error') {
        onError?.(data?.message || '生成回答失败')
      }

      boundary = buffer.indexOf('\n\n')
    }
  }

  onDone?.()
}
