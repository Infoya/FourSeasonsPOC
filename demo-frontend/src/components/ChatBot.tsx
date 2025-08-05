import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, ApiResponse } from '../services/api';
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      // Call the API service
      const response: ApiResponse = await sendMessage(currentInput, threadId || undefined);
      
      // Extract thread ID from response if available
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
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting right now. Please try again later.',
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
                <div className="text-xs text-gray-300">AI Chatbot</div>
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
                <p className="text-sm">{message.text}</p>
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