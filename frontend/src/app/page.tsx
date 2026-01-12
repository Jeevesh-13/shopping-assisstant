'use client';

import { useState, useRef, useEffect } from 'react';
import {
  Send, Sparkles, Smartphone, Search, Menu, Plus,
  MessageSquare, History, Settings, User, Zap,
  ChevronRight, Star, TrendingUp, ShieldCheck
} from 'lucide-react';
import ProductCard from '@/components/ProductCard';
import { sendChatMessage } from '@/lib/api';
import { APP_METADATA, UI_TEXT, CONVERSATION, COLORS } from '@/lib/constants';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  products?: any[];
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: input,
        session_id: sessionId || undefined,
        conversation_history: messages.slice(-5).map((m) => ({
          role: m.role,
          content: m.content,
          timestamp: m.timestamp.toISOString(),
        })),
      });

      if (!sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        products: response.products,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: error.message || UI_TEXT.CHAT.ERROR_DEFAULT,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (prompt: string) => {
    setInput(prompt);
    // Optional: Auto-submit or just focus
    inputRef.current?.focus();
  };

  // -- UI Components --

  const Sidebar = () => (
    <>
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-10 md:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed md:relative z-20 h-full bg-[#09090b] border-r border-[#27272a] transition-all duration-300 ${sidebarOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full md:w-20 md:translate-x-0'
          } flex flex-col`}
      >
        <div className="p-4 flex items-center gap-3 border-b border-[#27272a]">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shrink-0">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div className={`overflow-hidden transition-all duration-300 ${sidebarOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}>
            <h1 className="font-bold text-lg text-white">{APP_METADATA.NAME}</h1>
            <p className="text-xs text-gray-400">{APP_METADATA.VERSION}</p>
          </div>
        </div>

        <div className="p-2 flex-1 overflow-y-auto">
          <button
            onClick={() => { setMessages([]); setSessionId(''); setSidebarOpen(false); }}
            className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#27272a] text-gray-300 hover:text-white transition-colors mb-4 group min-h-[44px]"
          >
            <div className="w-8 h-8 rounded-lg bg-[#27272a] group-hover:bg-[#3f3f46] flex items-center justify-center">
              <Plus className="w-5 h-5" />
            </div>
            <span className={`transition-all duration-300 ${sidebarOpen ? 'opacity-100' : 'opacity-0 hidden'}`}>
              {UI_TEXT.SIDEBAR.NEW_CHAT}
            </span>
          </button>

          <div className="mb-2">
            <p className={`text-xs font-semibold text-gray-500 px-3 mb-2 uppercase ${!sidebarOpen && 'hidden'}`}>Recent</p>
            {[1, 2, 3].map((i) => (
              <button key={i} className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#27272a] text-gray-400 hover:text-white transition-colors min-h-[44px]">
                <History className="w-4 h-4 shrink-0" />
                <span className={`truncate text-sm ${!sidebarOpen && 'hidden'}`}>
                  {i === 1 ? 'Best gaming phones...' : i === 2 ? 'iPhone vs Samsung...' : 'Budget 5G options...'}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="p-2 border-t border-[#27272a]">
          <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#27272a] text-gray-400 hover:text-white transition-colors min-h-[44px]">
            <Settings className="w-5 h-5 shrink-0" />
            <span className={`${!sidebarOpen && 'hidden'}`}>Settings</span>
          </button>
          <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#27272a] text-gray-400 hover:text-white transition-colors min-h-[44px]">
            <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500" />
            <div className={`flex flex-col items-start ${!sidebarOpen && 'hidden'}`}>
              <span className="text-sm font-medium text-white">Guest User</span>
              <span className="text-xs text-gray-500">Free Plan</span>
            </div>
          </button>
        </div>
      </aside>
    </>
  );

  const WelcomeView = () => (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col items-center">
      <div className="max-w-4xl w-full space-y-8 md:space-y-12 py-6 md:py-10">

        {/* Hero Section */}
        <div className="text-center space-y-4 md:space-y-6 animate-fade-in">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500 tracking-tight pb-2 px-4">
            The Future of Shopping is Here
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed px-4">
            I'm your personal AI expert. Whether you need a
            <span className="text-blue-400 font-semibold"> gaming beast</span>, a
            <span className="text-purple-400 font-semibold"> camera pro</span>, or a
            <span className="text-green-400 font-semibold"> budget king</span>, I'll find it instantly.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
          {[
            {
              icon: <Zap className="w-6 h-6 text-yellow-400" />,
              title: "Instant Compare",
              desc: "Compare specs side-by-side in milliseconds."
            },
            {
              icon: <TrendingUp className="w-6 h-6 text-blue-400" />,
              title: "Real-time Prices",
              desc: "Always get the latest pricing and deals."
            },
            {
              icon: <ShieldCheck className="w-6 h-6 text-green-400" />,
              title: "Unbiased AI",
              desc: "Recommendations based on specs, not ads."
            }
          ].map((feature, i) => (
            <div key={i} className="p-5 md:p-6 rounded-2xl bg-[#18181b] border border-[#27272a] hover:border-blue-500/50 transition-all group">
              <div className="w-12 h-12 rounded-lg bg-[#27272a] group-hover:bg-[#3f3f46] flex items-center justify-center mb-3 md:mb-4 transition-colors">
                {feature.icon}
              </div>
              <h3 className="text-white font-bold mb-2 text-base md:text-lg">{feature.title}</h3>
              <p className="text-sm text-gray-400">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Suggested Prompts */}
        <div className="space-y-4">
          <p className="text-xs md:text-sm font-semibold text-gray-500 uppercase tracking-wider text-center">Try asking about</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
            {[
              "Best camera phone under ₹40,000",
              "Gaming phones with 120Hz display",
              "iPhone 15 vs Samsung S24",
              "5G phones with best battery life"
            ].map((text, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(text)}
                className="group flex items-center justify-between p-4 rounded-xl bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-blue-500 transition-all text-left min-h-[56px]"
              >
                <span className="text-sm md:text-base text-gray-300 group-hover:text-white font-medium pr-2">{text}</span>
                <ChevronRight className="w-4 h-4 shrink-0 text-gray-600 group-hover:text-blue-500 opacity-0 group-hover:opacity-100 transition-all" />
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );

  const ChatView = () => (
    <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6 scroll-smooth">
      <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">
        {messages.map((message, index) => (
          <div key={index} className={`flex gap-2 sm:gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            {message.role === 'assistant' && (
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1 shadow-lg shadow-blue-900/20">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
            )}

            <div className={`flex-1 max-w-3xl ${message.role === 'user' ? 'flex justify-end' : ''}`}>
              <div className={`
                p-4 sm:p-5 rounded-2xl shadow-sm
                ${message.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-[#18181b] border border-[#27272a] text-gray-100 rounded-tl-sm'
                }
              `}>
                <p className="whitespace-pre-wrap leading-relaxed text-sm sm:text-base">{message.content}</p>
              </div>

              {message.products && message.products.length > 0 && (
                <div className="mt-4 sm:mt-6 space-y-3 sm:space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="h-px flex-1 bg-[#27272a]"></span>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-widest">
                      {message.products.length} Products Found
                    </span>
                    <span className="h-px flex-1 bg-[#27272a]"></span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    {message.products.map((product: any) => (
                      <ProductCard key={product.id} product={product} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#27272a] flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-2 sm:gap-4">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-600 flex items-center justify-center shrink-0 animate-pulse">
              <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <div className="p-4 sm:p-5 rounded-2xl bg-[#18181b] border border-[#27272a] rounded-tl-sm flex items-center gap-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs sm:text-sm text-gray-400">Analyzing products...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#09090b] text-gray-100 font-sans overflow-hidden">
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative w-full h-full">
        {/* Mobile Header */}
        <header className="md:hidden h-14 sm:h-16 border-b border-[#27272a] flex items-center justify-between px-4 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-sm sm:text-base">ShopAI</span>
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 text-gray-400 min-h-[44px] min-w-[44px] flex items-center justify-center">
            <Menu className="w-6 h-6" />
          </button>
        </header>

        {/* View Switcher */}
        {messages.length === 0 ? <WelcomeView /> : <ChatView />}

        {/* Input Area */}
        <div className="p-3 sm:p-4 md:p-6 bg-[#09090b] safe-area-bottom">
          <div className="max-w-4xl mx-auto relative group">
            <div className={`absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl opacity-20 group-hover:opacity-40 transition duration-500 blur ${isLoading ? 'opacity-50 animate-pulse' : ''}`}></div>
            <div className="relative bg-[#18181b] rounded-2xl shadow-xl flex items-center border border-[#27272a] focus-within:border-blue-500/50 transition-colors">
              <div className="pl-3 sm:pl-4">
                <Search className="w-5 h-5 text-gray-500" />
              </div>
              <form onSubmit={handleSubmit} className="flex-1 flex">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask for recommendations, specs, or comparisons..."
                  disabled={isLoading}
                  className="w-full bg-transparent text-white p-3 sm:p-4 focus:outline-none placeholder-gray-500 text-sm sm:text-base"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-3 sm:p-4 pr-4 sm:pr-6 text-blue-500 hover:text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                >
                  <Send className="w-5 h-5" />
                </button>
              </form>
            </div>
            <p className="text-center text-xs text-gray-500 mt-2 sm:mt-3 px-2">
              AI can make mistakes. Please check product details.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
