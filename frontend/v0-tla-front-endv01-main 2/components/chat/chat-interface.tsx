"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Paperclip, Bot, User, RefreshCw, ThumbsUp, ThumbsDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { FirstTimeState } from "@/components/empty-placeholder"
import { DocumentSelector } from "@/components/chat/document-selector"
import { adkClient } from "@/lib/adk-client"
import { authService } from "@/lib/auth/auth-service"

type Message = {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([])
  const [isDocPanelCollapsed, setIsDocPanelCollapsed] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const currentQuery = inputValue
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: currentQuery,
      role: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      // Get user info from auth service
      const user = authService.getCurrentUser()
      const userId = user?.id || 'anonymous'

      // Build context for the query including document content
      const selectedDocContent = selectedDocuments
        .map(docId => availableDocuments.find(doc => doc.id === docId))
        .filter(doc => doc?.content)
        .map(doc => `Document: ${doc.title}\nContent: ${doc.content}`)
        .join('\n\n')

      const context = {
        documents: selectedDocuments.length > 0 ? selectedDocuments : undefined,
        document_content: selectedDocContent || undefined,
        section_type: 'document_chat',
        generation_purpose: 'document_analysis'
      }

      // Call the real ADK service
      const response = await adkClient.queryRAG({
        user_id: userId,
        query: currentQuery,
        context,
        parameters: {
          max_tokens: 2000,
          temperature: 0.7
        }
      })

      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        role: "assistant",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat error:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I encountered an error while processing your request: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        role: "assistant",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocuments((prev) => (prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]))
  }

  const handleDocumentsUpdate = (documents: any[]) => {
    setAvailableDocuments(documents)
  }

  const toggleDocPanel = () => {
    setIsDocPanelCollapsed(!isDocPanelCollapsed)
  }

  return (
    <div className="flex flex-row gap-2 h-[calc(100vh-220px)] min-h-[500px]">
      {/* Document selector sidebar - collapsible */}
      <div
        className={`${
          isDocPanelCollapsed ? "w-12" : "w-full md:w-64 lg:w-80"
        } flex-shrink-0 transition-all duration-300 h-full`}
      >
        <DocumentSelector
          onSelect={handleDocumentSelect}
          selectedDocuments={selectedDocuments}
          onToggleCollapse={toggleDocPanel}
          isCollapsed={isDocPanelCollapsed}
          onDocumentsUpdate={handleDocumentsUpdate}
        />
      </div>

      {/* Chat container */}
      <div className="flex-grow flex flex-col h-full relative">
        <Card className="flex-grow flex flex-col h-full overflow-hidden border border-gray-200 rounded-lg">
          {/* Chat messages area */}
          <div className="flex-grow overflow-y-auto p-4 space-y-4 pb-[70px]">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <FirstTimeState
                  title="Start a conversation"
                  description="Ask questions about your documents to get AI-powered insights and answers."
                  itemType="message"
                  variant="default"
                  icon={<Bot />}
                  showHelpTip={true}
                  helpTipText="Try asking specific questions about your IEPs, student data, or educational resources."
                />
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === "user" ? "bg-[#14b8a6] text-white" : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center">
                        {message.role === "user" ? (
                          <User size={14} className="text-[#14b8a6]" />
                        ) : (
                          <Bot size={14} className="text-[#14b8a6]" />
                        )}
                      </div>
                      <span className="text-xs font-medium">{message.role === "user" ? "You" : "AI Assistant"}</span>
                      <span className="text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {message.role === "assistant" && (
                      <div className="flex items-center gap-2 mt-2 justify-end">
                        <button className="p-1 rounded-full hover:bg-gray-200 transition-colors" aria-label="Thumbs up">
                          <ThumbsUp size={14} />
                        </button>
                        <button
                          className="p-1 rounded-full hover:bg-gray-200 transition-colors"
                          aria-label="Thumbs down"
                        >
                          <ThumbsDown size={14} />
                        </button>
                        <button
                          className="p-1 rounded-full hover:bg-gray-200 transition-colors"
                          aria-label="Regenerate response"
                        >
                          <RefreshCw size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
                  <div className="flex space-x-2">
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area - fixed at bottom with proper spacing */}
          <div className="absolute bottom-2 left-0 right-0 px-4">
            <div className="flex items-center gap-2 bg-white p-2 border border-gray-200 rounded-lg shadow-sm">
              <div className="relative flex-grow">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message..."
                  className="w-full border border-gray-300 rounded-lg py-3 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:border-transparent resize-none min-h-[46px] max-h-[120px]"
                  rows={1}
                  style={{ height: "46px", overflow: "auto" }}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label="Attach file"
                >
                  <Paperclip size={18} />
                </button>
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="bg-[#14b8a6] hover:bg-[#0f9e8a] text-white h-[46px] px-4"
              >
                <Send size={18} />
                <span className="ml-2 hidden sm:inline">Send</span>
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
