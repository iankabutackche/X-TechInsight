import { useEffect, useMemo, useRef, useState } from 'react'
import { createChat, getChatMessages, listChats, streamQuery, updateChat, uploadFile } from './api'
import MessageMarkdown from './MessageMarkdown'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.pdf', '.md', '.txt']
const SUGGESTED_TAGS = ['后端', '金融', '云计算', '前端', 'general']

const styles = {
  app: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    background: '#212121',
    color: '#ececec',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  sidebar: {
    width: '260px',
    borderRight: '1px solid #2f2f2f',
    display: 'flex',
    flexDirection: 'column',
    background: '#171717',
  },
  sidebarHeader: {
    padding: '16px',
    borderBottom: '1px solid #2f2f2f',
  },
  newChatButton: {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #3f3f3f',
    background: '#262626',
    color: '#ececec',
    cursor: 'pointer',
  },
  chatList: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px',
  },
  chatItem: {
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '6px',
    cursor: 'pointer',
    background: 'transparent',
  },
  chatItemActive: {
    background: '#2f2f2f',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
  },
  mainHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #2f2f2f',
    fontSize: '16px',
    fontWeight: 600,
  },
  messageArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
  },
  emptyState: {
    marginTop: '80px',
    textAlign: 'center',
    color: '#9ca3af',
  },
  messageBlock: {
    marginBottom: '20px',
    maxWidth: '820px',
  },
  messageRole: {
    fontSize: '12px',
    color: '#9ca3af',
    marginBottom: '6px',
  },
  userBubble: {
    display: 'inline-block',
    padding: '12px 14px',
    borderRadius: '12px',
    background: '#2f2f2f',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
  },
  assistantBubble: {
    padding: '4px 0',
    lineHeight: 1.7,
    whiteSpace: 'pre-wrap',
  },
  sourcesBox: {
    marginTop: '12px',
    padding: '12px',
    borderRadius: '10px',
    background: '#171717',
    border: '1px solid #2f2f2f',
  },
  sourceItem: {
    fontSize: '13px',
    color: '#cbd5e1',
    marginBottom: '8px',
  },
  inputBar: {
    padding: '16px 20px',
    borderTop: '1px solid #2f2f2f',
    display: 'flex',
    gap: '12px',
  },
  input: {
    flex: 1,
    padding: '12px 14px',
    borderRadius: '10px',
    border: '1px solid #3f3f3f',
    background: '#2f2f2f',
    color: '#ececec',
    outline: 'none',
  },
  sendButton: {
    padding: '0 18px',
    borderRadius: '10px',
    border: 'none',
    background: '#10a37f',
    color: '#fff',
    cursor: 'pointer',
  },
  sendButtonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  rightPanel: {
    width: '300px',
    borderLeft: '1px solid #2f2f2f',
    background: '#171717',
    padding: '16px',
    overflowY: 'auto',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 600,
    marginBottom: '12px',
  },
  tagBadge: {
    display: 'inline-block',
    padding: '6px 10px',
    borderRadius: '999px',
    background: '#2f2f2f',
    fontSize: '13px',
    marginBottom: '16px',
  },
  checkboxItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 0',
    fontSize: '14px',
    color: '#d1d5db',
  },
  hintText: {
    fontSize: '13px',
    color: '#9ca3af',
    lineHeight: 1.6,
  },
  uploadButton: {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #3f3f3f',
    background: '#262626',
    color: '#ececec',
    cursor: 'pointer',
    marginBottom: '12px',
  },
  formBox: {
    marginTop: '12px',
    padding: '12px',
    borderRadius: '10px',
    background: '#212121',
    border: '1px solid #2f2f2f',
  },
  formLabel: {
    display: 'block',
    fontSize: '12px',
    color: '#9ca3af',
    marginBottom: '6px',
  },
  formInput: {
    width: '100%',
    boxSizing: 'border-box',
    padding: '8px 10px',
    borderRadius: '8px',
    border: '1px solid #3f3f3f',
    background: '#2f2f2f',
    color: '#ececec',
    marginBottom: '10px',
    outline: 'none',
  },
  tagOptions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginBottom: '10px',
  },
  tagOption: {
    padding: '4px 8px',
    borderRadius: '999px',
    border: '1px solid #3f3f3f',
    background: '#2f2f2f',
    color: '#d1d5db',
    cursor: 'pointer',
    fontSize: '12px',
  },
  tagOptionActive: {
    border: '1px solid #10a37f',
    color: '#86efac',
  },
  formActions: {
    display: 'flex',
    gap: '8px',
  },
  secondaryButton: {
    flex: 1,
    padding: '8px 10px',
    borderRadius: '8px',
    border: '1px solid #3f3f3f',
    background: 'transparent',
    color: '#d1d5db',
    cursor: 'pointer',
  },
  primaryButton: {
    flex: 1,
    padding: '8px 10px',
    borderRadius: '8px',
    border: 'none',
    background: '#10a37f',
    color: '#fff',
    cursor: 'pointer',
  },
  saveTagButton: {
    marginTop: '8px',
    padding: '8px 12px',
    borderRadius: '8px',
    border: 'none',
    background: '#10a37f',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '13px',
  },
  statusText: {
    fontSize: '13px',
    color: '#86efac',
    marginBottom: '12px',
    lineHeight: 1.5,
  },
  errorText: {
    fontSize: '13px',
    color: '#fca5a5',
    marginBottom: '12px',
    lineHeight: 1.5,
  },
  warningBox: {
    padding: '12px',
    borderRadius: '10px',
    background: '#3f1d1d',
    border: '1px solid #ef4444',
    color: '#fecaca',
    fontSize: '13px',
    lineHeight: 1.6,
    marginBottom: '16px',
  },
}

function App() {
  const fileInputRef = useRef(null)
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [messagesByChatId, setMessagesByChatId] = useState({})
  const [allDocuments, setAllDocuments] = useState([])
  const [mountedDocsByChatId, setMountedDocsByChatId] = useState({})
  const [inputValue, setInputValue] = useState('')
  const [isCreatingChat, setIsCreatingChat] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newChatName, setNewChatName] = useState('')
  const [newChatTag, setNewChatTag] = useState('后端')
  const [editingTag, setEditingTag] = useState('')
  const [isSavingTag, setIsSavingTag] = useState(false)

  const activeChat = useMemo(
    () => chats.find((chat) => chat.id === activeChatId) ?? null,
    [chats, activeChatId],
  )

  const activeMessages = activeChatId ? messagesByChatId[activeChatId] || [] : []

  const activeMountedDocIds = useMemo(
    () => (activeChatId ? mountedDocsByChatId[activeChatId] || [] : []),
    [mountedDocsByChatId, activeChatId],
  )

  const isDocMountedForChat = (chatId, docId) =>
    (mountedDocsByChatId[chatId] || []).includes(docId)

  const domainConflicts = useMemo(() => {
    if (!activeChat) {
      return []
    }
    return allDocuments.filter(
      (doc) =>
        activeMountedDocIds.includes(doc.id) &&
        doc.tag &&
        doc.tag !== activeChat.tag,
    )
  }, [allDocuments, activeChat, activeMountedDocIds])

  useEffect(() => {
    const loadAllChats = async () => {
      try {
        const chatList = await listChats()
        setChats(chatList)
        if (chatList.length > 0) {
          setActiveChatId((currentId) => currentId || chatList[0].id)
        }
      } catch (error) {
        console.error('加载对话列表失败:', error)
      }
    }

    loadAllChats()
  }, [])

  useEffect(() => {
    if (!activeChatId) {
      return
    }

    const loadMessages = async () => {
      try {
        const messages = await getChatMessages(activeChatId)
        setMessagesByChatId((prev) => ({
          ...prev,
          [activeChatId]: messages.map((message) => ({
            id: `db-${message.id}`,
            role: message.role,
            content: message.content,
            sources: [],
          })),
        }))
      } catch (error) {
        console.error('加载对话历史失败:', error)
      }
    }

    loadMessages()
  }, [activeChatId])

  useEffect(() => {
    setEditingTag(activeChat?.tag || '')
  }, [activeChat])

  const toggleDocument = (docId) => {
    if (!activeChatId) {
      return
    }

    setMountedDocsByChatId((prev) => {
      const current = prev[activeChatId] || []
      const next = current.includes(docId)
        ? current.filter((id) => id !== docId)
        : [...current, docId]

      return { ...prev, [activeChatId]: next }
    })
  }

  const openCreateForm = () => {
    setNewChatName(`新对话 ${chats.length + 1}`)
    setNewChatTag('后端')
    setShowCreateForm(true)
  }

  const handleCreateChat = async () => {
    const name = newChatName.trim()
    const tag = newChatTag.trim() || 'general'

    if (!name) {
      window.alert('请输入对话名称')
      return
    }

    try {
      setIsCreatingChat(true)
      const chat = await createChat(name, tag)
      setChats((prev) => [chat, ...prev])
      setActiveChatId(chat.id)
      setMessagesByChatId((prev) => ({ ...prev, [chat.id]: [] }))
      setShowCreateForm(false)
    } catch (error) {
      window.alert(error.message || '创建对话失败')
    } finally {
      setIsCreatingChat(false)
    }
  }

  const handleSaveTag = async () => {
    if (!activeChat) {
      return
    }

    const tag = editingTag.trim() || 'general'

    try {
      setIsSavingTag(true)
      const updated = await updateChat(activeChat.id, { tag })
      setChats((prev) =>
        prev.map((chat) => (chat.id === updated.id ? updated : chat)),
      )
    } catch (error) {
      window.alert(error.message || '保存标签失败')
    } finally {
      setIsSavingTag(false)
    }
  }

  const appendAssistantContent = (chatId, token) => {
    setMessagesByChatId((prev) => {
      const currentMessages = [...(prev[chatId] || [])]
      const lastMessage = currentMessages[currentMessages.length - 1]

      if (!lastMessage || lastMessage.role !== 'assistant') {
        return prev
      }

      currentMessages[currentMessages.length - 1] = {
        ...lastMessage,
        content: `${lastMessage.content}${token}`,
      }

      return { ...prev, [chatId]: currentMessages }
    })
  }

  const attachSources = (chatId, sources) => {
    setMessagesByChatId((prev) => {
      const currentMessages = [...(prev[chatId] || [])]
      const lastMessage = currentMessages[currentMessages.length - 1]

      if (!lastMessage || lastMessage.role !== 'assistant') {
        return prev
      }

      currentMessages[currentMessages.length - 1] = {
        ...lastMessage,
        sources,
      }

      return { ...prev, [chatId]: currentMessages }
    })
  }

  const handleSend = async () => {
    if (!activeChatId || !inputValue.trim() || isSending) {
      return
    }

    const question = inputValue.trim()
    setInputValue('')

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
    }
    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      sources: [],
    }

    setMessagesByChatId((prev) => ({
      ...prev,
      [activeChatId]: [...(prev[activeChatId] || []), userMessage, assistantMessage],
    }))

    setIsSending(true)

    try {
      await streamQuery({
        chatId: activeChatId,
        question,
        onToken: (token) => appendAssistantContent(activeChatId, token),
        onSources: (sources) => attachSources(activeChatId, sources),
        onError: (message) => appendAssistantContent(activeChatId, `\n[错误] ${message}`),
      })
    } catch (error) {
      appendAssistantContent(activeChatId, `\n[错误] ${error.message || '发送失败'}`)
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  const handleUploadClick = () => {
    if (!activeChat) {
      window.alert('请先创建一个对话，再上传文档')
      return
    }
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''

    if (!file || !activeChat) {
      return
    }

    const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setUploadError(`暂不支持的格式，仅支持 ${ALLOWED_EXTENSIONS.join(', ')}`)
      setUploadMessage('')
      return
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError('文件超过 10MB 上限')
      setUploadMessage('')
      return
    }

    setIsUploading(true)
    setUploadError('')
    setUploadMessage('正在上传并后台解析，请稍候...')

    try {
      const result = await uploadFile(file, activeChat.tag)
      setAllDocuments((prev) => {
        const exists = prev.some((doc) => doc.id === result.file_id)
        if (exists) {
          return prev.map((doc) =>
            doc.id === result.file_id
              ? { ...doc, name: result.filename, tag: result.tag }
              : doc,
          )
        }
        return [
          {
            id: result.file_id,
            name: result.filename,
            tag: result.tag,
          },
          ...prev,
        ]
      })
      setMountedDocsByChatId((prev) => ({
        ...prev,
        [activeChatId]: [...new Set([...(prev[activeChatId] || []), result.file_id])],
      }))
      setUploadMessage(result.message || '上传成功，文档正在入库')
    } catch (error) {
      setUploadError(error.message || '上传失败')
      setUploadMessage('')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div style={styles.app}>
      <aside style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <button
            type="button"
            style={styles.newChatButton}
            onClick={openCreateForm}
            disabled={isCreatingChat}
          >
            + 新建对话
          </button>

          {showCreateForm && (
            <div style={styles.formBox}>
              <label style={styles.formLabel}>对话名称</label>
              <input
                style={styles.formInput}
                value={newChatName}
                onChange={(event) => setNewChatName(event.target.value)}
                placeholder="例如：技术栈讨论"
              />

              <label style={styles.formLabel}>领域标签</label>
              <div style={styles.tagOptions}>
                {SUGGESTED_TAGS.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    style={{
                      ...styles.tagOption,
                      ...(newChatTag === tag ? styles.tagOptionActive : {}),
                    }}
                    onClick={() => setNewChatTag(tag)}
                  >
                    {tag}
                  </button>
                ))}
              </div>
              <input
                style={styles.formInput}
                value={newChatTag}
                onChange={(event) => setNewChatTag(event.target.value)}
                placeholder="可自定义，例如：医疗、法律"
              />

              <div style={styles.formActions}>
                <button
                  type="button"
                  style={styles.secondaryButton}
                  onClick={() => setShowCreateForm(false)}
                >
                  取消
                </button>
                <button
                  type="button"
                  style={styles.primaryButton}
                  onClick={handleCreateChat}
                  disabled={isCreatingChat}
                >
                  {isCreatingChat ? '创建中...' : '确认创建'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div style={styles.chatList}>
          {chats.length === 0 ? (
            <div style={{ ...styles.hintText, padding: '12px' }}>还没有对话，先点上方按钮创建一个。</div>
          ) : (
            chats.map((chat) => {
              const isActive = chat.id === activeChatId
              return (
                <div
                  key={chat.id}
                  style={{
                    ...styles.chatItem,
                    ...(isActive ? styles.chatItemActive : {}),
                  }}
                  onClick={() => setActiveChatId(chat.id)}
                >
                  <div>{chat.name}</div>
                  <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                    {chat.tag}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </aside>

      <main style={styles.main}>
        <header style={styles.mainHeader}>
          {activeChat?.name || '请选择或创建对话'}
        </header>

        <section style={styles.messageArea}>
          {!activeChat ? (
            <div style={styles.emptyState}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>X-TechInsight</div>
              <div>点击左侧「新建对话」开始。</div>
            </div>
          ) : activeMessages.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>X-TechInsight</div>
              <div>输入问题，例如：项目用了哪些技术栈？</div>
            </div>
          ) : (
            activeMessages.map((message) => (
              <div key={message.id} style={styles.messageBlock}>
                <div style={styles.messageRole}>
                  {message.role === 'user' ? '你' : 'AI 助手'}
                </div>
                {message.role === 'user' ? (
                  <div style={styles.userBubble}>{message.content}</div>
                ) : (
                  <>
                    <div style={styles.assistantBubble}>
                      {message.content ? (
                        <MessageMarkdown content={message.content} />
                      ) : (
                        isSending ? '正在思考...' : ''
                      )}
                    </div>
                    {message.sources?.length > 0 && (
                      <div style={styles.sourcesBox}>
                        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
                          来源证据
                        </div>
                        {message.sources.map((source) => (
                          <div key={source.index} style={styles.sourceItem}>
                            [Source {source.index}] {source.source_file} | page=
                            {source.page_index}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </section>

        <footer style={styles.inputBar}>
          <input
            style={styles.input}
            placeholder={activeChat ? '输入你的问题...' : '请先创建对话'}
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!activeChat || isSending}
          />
          <button
            type="button"
            style={{
              ...styles.sendButton,
              ...((!activeChat || isSending) ? styles.sendButtonDisabled : {}),
            }}
            onClick={handleSend}
            disabled={!activeChat || isSending}
          >
            {isSending ? '生成中...' : '发送'}
          </button>
        </footer>
      </main>

      <aside style={styles.rightPanel}>
        <div style={styles.sectionTitle}>当前对话配置</div>

        <label style={styles.formLabel}>领域标签</label>
        <input
          style={styles.formInput}
          value={editingTag}
          onChange={(event) => setEditingTag(event.target.value)}
          placeholder="例如：后端、金融、云计算"
          disabled={!activeChat}
        />
        <button
          type="button"
          style={{
            ...styles.saveTagButton,
            ...((!activeChat || isSavingTag) ? styles.sendButtonDisabled : {}),
          }}
          onClick={handleSaveTag}
          disabled={!activeChat || isSavingTag}
        >
          {isSavingTag ? '保存中...' : '保存标签'}
        </button>

        <div style={{ ...styles.tagBadge, marginTop: '12px' }}>
          当前生效：{activeChat?.tag || '未选择'}
        </div>

        {domainConflicts.length > 0 && (
          <div style={styles.warningBox}>
            <strong>领域冲突提醒</strong>
            <div style={{ marginTop: '8px' }}>
              当前对话领域是「{activeChat.tag}」，但以下文档属于不同领域：
            </div>
            <ul style={{ margin: '8px 0 0 18px', padding: 0 }}>
              {domainConflicts.map((doc) => (
                <li key={doc.id}>
                  {doc.name}（{doc.tag}）
                </li>
              ))}
            </ul>
            <div style={{ marginTop: '8px' }}>
              继续挂载可能引入检索噪音，建议取消勾选或更换对话。
            </div>
          </div>
        )}

        <div style={styles.sectionTitle}>知识库挂载</div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          type="button"
          style={{
            ...styles.uploadButton,
            ...(isUploading || !activeChat ? styles.sendButtonDisabled : {}),
          }}
          onClick={handleUploadClick}
          disabled={isUploading || !activeChat}
        >
          {isUploading ? '上传中...' : '上传文档 (.pdf/.md/.txt)'}
        </button>

        {uploadMessage && <div style={styles.statusText}>{uploadMessage}</div>}
        {uploadError && <div style={styles.errorText}>{uploadError}</div>}

        {allDocuments.length === 0 ? (
          <p style={styles.hintText}>还没有文档，点击上方按钮上传到全局资源池。</p>
        ) : (
          allDocuments.map((doc) => (
            <label key={doc.id} style={styles.checkboxItem}>
              <input
                type="checkbox"
                checked={activeMountedDocIds.includes(doc.id)}
                onChange={() => toggleDocument(doc.id)}
              />
              <span>
                {doc.name}
                {doc.tag ? ` (${doc.tag})` : ''}
                {!isDocMountedForChat(activeChatId, doc.id) && activeChatId
                  ? ' · 未挂载到本对话'
                  : ''}
              </span>
            </label>
          ))
        )}

        <p style={{ ...styles.hintText, marginTop: '16px' }}>
          文档进入全局资源池；勾选表示挂载到「当前对话」。未勾选的对话不会使用该文档，也不会触发领域冲突提醒。
        </p>
      </aside>
    </div>
  )
}

export default App
