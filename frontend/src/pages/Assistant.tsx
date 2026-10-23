import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Sparkles, ExternalLink, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: { resource_id: number; title: string; type: string; direct_url?: string }[];
  suggested_actions?: string[];
}

export const Assistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I am your LinkMind opportunity intelligence assistant. Ask me anything about your saved courses, internship matches, deadlines, or skill gaps.",
      suggested_actions: [
        "Which AI internships best match my resume?",
        "Which courses should I take before applying?",
        "Which opportunities have deadlines approaching?"
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    setInput('');
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const result = await api.askAssistant(text, history);
      
      const assistantMsg: Message = {
        role: 'assistant',
        content: result.response,
        citations: result.citations,
        suggested_actions: result.suggested_actions
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.message || 'Unable to retrieve answer. Please try again.'}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">AI Opportunity Assistant</h1>
            <p className="text-xs text-slate-400">Strictly grounded across your saved library and resume profile</p>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6 custom-scrollbar pr-2">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 ${m.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
              m.role === 'user'
                ? 'bg-brand-600 text-white'
                : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200'
            }`}>
              {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`max-w-2xl rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-brand-600 text-white'
                : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 shadow-sm'
            }`}>
              <div className="whitespace-pre-line">{m.content}</div>

              {/* Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                    Referenced Saved Items:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {m.citations.map((c) => (
                      <Link
                        key={c.resource_id}
                        to={`/resources/${c.resource_id}`}
                        className="flex items-center space-x-1.5 text-xs bg-slate-50 dark:bg-slate-800 hover:bg-brand-50 dark:hover:bg-brand-950/40 text-brand-600 dark:text-brand-400 font-medium px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors"
                      >
                        <span className="truncate max-w-[200px]">{c.title}</span>
                        <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested actions / questions */}
              {m.suggested_actions && m.suggested_actions.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3 pt-2">
                  {m.suggested_actions.map((act, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(act)}
                      className="text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-brand-600 px-2.5 py-1 rounded-lg transition-colors"
                    >
                      💡 {act}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <div className="w-8 h-8 rounded-xl bg-slate-200 dark:bg-slate-800 flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
            </div>
            <span>Searching your library and generating grounded advice...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input box */}
      <form onSubmit={handleFormSubmit} className="pt-3">
        <div className="flex items-center space-x-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-2 shadow-sm focus-within:border-brand-500 transition-all">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your saved courses, deadlines, missing skills..."
            className="flex-1 bg-transparent px-3 py-1.5 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-xl transition-colors shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
