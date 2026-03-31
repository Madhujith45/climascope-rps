import React, { useState, useRef, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

export default function FloatingChatbot({ selectedDevice }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([{ content: "Hi! I'm your ClimaScope AI assistant. Do you need insights on your current climate data?", role: "assistant" }])
  const [inputStr, setInputStr] = useState("")
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isOpen, loading])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputStr.trim()) return

    const userText = inputStr.trim()
    setInputStr("")
    setMessages(p => [...p, { role: 'user', content: userText }])
    setLoading(true)

    try {
      const token = getAuthToken()
      // Fetch current context data first
      let contextData = {}
      try {
        const url = selectedDevice 
          ? `/api/data/latest?n=1&device_id=${selectedDevice}` 
          : `/api/data/latest?n=1`
        const d_res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
        if (d_res.ok) {
          const arr = await d_res.json()
          if (arr.length > 0) contextData = arr[0]
        }
      } catch (e) { console.error("Could not fetch context data for chat", e) }

      // Send to AI endpoint
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: userText, message: userText, context: contextData })
      })

      const payload = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(payload.detail || payload.error || payload.reply || 'Failed to reach AI')
      }

      const assistantText = payload.reply || payload.response || 'AI temporarily unavailable.'
      setMessages(p => [...p, { role: 'assistant', content: assistantText }])

    } catch (err) {
      const fallback = err?.message?.trim() || 'AI temporarily unavailable. Please try again.'
      setMessages(p => [...p, { role: 'assistant', content: `⚠️ ${fallback}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Expanding chat window */}
      <div 
        className={`glass-card flex flex-col transition-all duration-300 origin-bottom-right mb-4 overflow-hidden shadow-2xl ${isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-0 pointer-events-none'}`}
        style={{ width: 340, height: 450, background: 'rgba(15, 25, 40, 0.95)', border: '1px solid rgba(255,255,255,0.1)' }}
      >
        {/* Header */}
        <div className="flex bg-gradient-to-r from-teal-500/20 to-blue-500/20 px-4 py-3 items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-2">
            <span className="text-xl">🤖</span>
            <div className="font-semibold text-white text-sm">ClimaScope AI</div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white transition-colors">✕</button>
        </div>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex max-w-[85%] ${m.role === 'user' ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}>
              <div 
                className={`text-sm px-3 py-2 rounded-2xl ${m.role === 'user' ? 'bg-blue-500/80 text-white rounded-tr-sm shadow-blue-500/20 shadow-lg' : 'bg-white/10 text-gray-100 rounded-tl-sm shadow-black/20 shadow-lg'} leading-relaxed whitespace-pre-wrap break-words inline-block`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex mr-auto bg-white/5 px-4 py-2 rounded-2xl rounded-tl-sm inline-block">
              <span className="flex items-center gap-1.5 opacity-60">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input area */}
        <form onSubmit={handleSend} className="p-3 bg-black/20 border-t border-white/5 relative">
          <input 
            type="text" 
            value={inputStr}
            onChange={(e) => setInputStr(e.target.value)}
            disabled={loading}
            placeholder="Ask about your climate data..." 
            className="w-full bg-white/5 text-white text-sm rounded-xl px-4 py-2.5 pr-10 outline-none focus:bg-white/10 transition-colors"
          />
          <button 
            type="submit" 
            disabled={loading || !inputStr.trim()} 
            className="absolute right-5 flex items-center justify-center p-1.5 text-teal-400 hover:text-white disabled:opacity-40 transition-colors"
            style={{ top: '50%', transform: 'translateY(-50%)' }}
          >
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>

      {/* Trigger button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`absolute bottom-0 right-0 w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95 z-50 border border-white/10 ${isOpen ? 'rotate-90 scale-90 opacity-0 pointer-events-none' : 'rotate-0 opacity-100'}`}
        style={{ background: 'linear-gradient(135deg, #14b8a6, #3b82f6)' }}
      >
        <span className="text-2xl drop-shadow-md">✨</span>
      </button>
    </div>
  )
}
