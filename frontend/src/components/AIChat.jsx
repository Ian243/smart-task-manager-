import React, { useState } from 'react';
import { Bot, X, Send } from 'lucide-react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';

const AIChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: 'ai', content: 'Hi! I am your AI assistant. How can I help you manage tasks today?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.post('/ai/chat', { message: userMsg });
      setMessages(prev => [...prev, { role: 'ai', content: res.data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: 'Failed to communicate with AI agent.' }]);
    }
    setLoading(false);
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="absolute bottom-6 right-6 h-14 w-14 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg flex items-center justify-center transition-transform hover:scale-110 z-40"
      >
        <Bot className="h-6 w-6" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className="absolute bottom-24 right-6 w-80 sm:w-96 glass-card overflow-hidden flex flex-col shadow-2xl z-50 border border-primary-100"
            style={{ height: '500px', maxHeight: '80vh' }}
          >
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-4 flex justify-between items-center text-white">
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5" />
                <span className="font-semibold">AI Assistant</span>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white/50">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                    msg.role === 'user' ? 'bg-primary-500 text-white rounded-br-none' : 
                    msg.role === 'error' ? 'bg-red-100 text-red-700 rounded-bl-none' : 'bg-white shadow-sm border border-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white shadow-sm border border-gray-100 text-gray-500 rounded-2xl rounded-bl-none px-4 py-2 text-sm flex items-center space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              )}
            </div>
            
            <form onSubmit={sendMessage} className="p-3 bg-white border-t border-gray-100 flex items-center gap-2">
              <input 
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask me anything..." 
                className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                disabled={loading}
              />
              <button 
                type="submit" 
                disabled={!input.trim() || loading}
                className="h-10 w-10 bg-primary-600 text-white rounded-full flex items-center justify-center hover:bg-primary-700 disabled:opacity-50 transition-colors shrink-0"
              >
                <Send className="h-4 w-4 ml-0.5" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AIChat;
