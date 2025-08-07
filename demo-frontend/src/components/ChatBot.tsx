import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, ApiResponse } from '../services/api';
import ReactMarkdown from 'react-markdown';
import fsIcon from '../assets/images/fsIcon.jpg'
import sendIcon from '../assets/images/send.png'

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ChatBotProps {
  isOpen: boolean;
  onClose: () => void;
}

const ChatBot: React.FC<ChatBotProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to Four Seasons! I\'m your personal concierge, ready to help you plan the perfect luxury experience. How may I assist you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('connected');
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize thread_id when chatbot opens
  useEffect(() => {
    if (isOpen && !isInitialized) {
      initializeChatbot();
    }
  }, [isOpen, isInitialized]);

  const initializeChatbot = async () => {
    try {
      setConnectionStatus('connected');
      // Call the API to initialize and get thread_id
      const response: ApiResponse = await sendMessage('', undefined);

      if (response.thread_id) {
        setThreadId(response.thread_id);
        console.log('Chatbot initialized with thread_id:', response.thread_id);
      } else {
        console.warn('No thread_id received during initialization');
      }

      setIsInitialized(true);
    } catch (error) {
      console.error('Error initializing chatbot:', error);
      setConnectionStatus('disconnected');
      // Continue without thread_id if initialization fails
      setIsInitialized(true);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      setConnectionStatus('connected');
      // Call the API service with the saved thread_id
      const response: ApiResponse = await sendMessage(currentInput, threadId || undefined);

      // Update thread_id if we get a new one (shouldn't happen after initialization)
      if (response.thread_id && !threadId) {
        setThreadId(response.thread_id);
      }

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      setConnectionStatus('disconnected');
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting to the AI assistant right now. Please try again later.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chat-modal">
      <div className="chat-container">
        {/* Header */}
          <div className="chat-header bg-black text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img src={fsIcon} alt="Logo" className="w-8 h-8 rounded-full bg-white" />
              <div className='header-text'>
                <div className="font-semibold text-sm">FourSeasons</div>
                <div className="text-xs text-gray-300 flex items-center">
                  AI Chatbot
                  <span className={`ml-2 w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : 'bg-red-400'}`}></span>
                </div>
              </div>
            </div>
            <button onClick={onClose} className="text-white text-xl leading-none bg-transparent border-none p-0 hover:opacity-80">X</button>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user' : 'bot'}`}
            >
              <div className="message-content px-8">
                {message.sender === 'bot' ? (
                  <ReactMarkdown
                    components={{
                      // Style links with blue color and underline
                      a: ({ node, ...props }) => (
                        <a
                          {...props}
                          className="text-blue-600 underline hover:text-blue-800 transition-colors"
                          target="_blank"
                          rel="noopener noreferrer"
                        />
                      ),
                      // Style bold text
                      strong: ({ node, ...props }) => (
                        <strong {...props} className="font-bold" />
                      ),
                      // Style italic text
                      em: ({ node, ...props }) => (
                        <em {...props} className="italic" />
                      ),
                      // Style code blocks
                      code: ({ node, inline, ...props }: any) => (
                        inline ? (
                          <code {...props} className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" />
                        ) : (
                          <code {...props} className="block bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto" />
                        )
                      ),
                      // Style headings
                      h1: ({ node, ...props }) => (
                        <h1 {...props} className="text-xl font-bold mb-2" />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2 {...props} className="text-lg font-bold mb-2" />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3 {...props} className="text-base font-bold mb-1" />
                      ),
                      // Style lists
                      ul: ({ node, ...props }) => (
                        <ul {...props} className="list-disc list-inside mb-2" />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol {...props} className="list-decimal list-inside mb-2" />
                      ),
                      // Style paragraphs
                      p: ({ node, ...props }) => (
                        <p {...props} className="mb-2 last:mb-0" />
                      ),
                    }}
                  >
                    {message.text}
                  </ReactMarkdown>
                ) : (
                  <p className="text-sm">{message.text}</p>
                )}
                <p className="message-time">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message bot">
              <div className="message-content">
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input">
          <div className="chat-input-container">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything..."
              disabled={isLoading}
            />
            <button
             onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            type="submit"
            className="w-9 h-9 flex items-center justify-center rounded-full bg-white border border-black hover:bg-gray-100 transition-colors duration-200"
          >
            <img className='h-4' src={sendIcon} alt="" />
          </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatBot; 