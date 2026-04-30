'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { mitraChat, translateText, getMitraStatus } from '@/app/lib/api';

// ── Supported Languages ──────────────────────────────────────────
const LANGUAGES = [
  { code: 'en', label: 'English', speechCode: 'en-IN', flag: '🇬🇧' },
  { code: 'hi', label: 'हिन्दी', speechCode: 'hi-IN', flag: '🇮🇳' },
  { code: 'mr', label: 'मराठी', speechCode: 'mr-IN', flag: '🇮🇳' },
  { code: 'ta', label: 'தமிழ்', speechCode: 'ta-IN', flag: '🇮🇳' },
  { code: 'te', label: 'తెలుగు', speechCode: 'te-IN', flag: '🇮🇳' },
  { code: 'kn', label: 'ಕನ್ನಡ', speechCode: 'kn-IN', flag: '🇮🇳' },
  { code: 'bn', label: 'বাংলা', speechCode: 'bn-IN', flag: '🇮🇳' },
  { code: 'gu', label: 'ગુજરાતી', speechCode: 'gu-IN', flag: '🇮🇳' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ', speechCode: 'pa-IN', flag: '🇮🇳' },
];

interface ChatMessage {
  id: string;
  role: 'user' | 'mitra';
  text: string;          // displayed text (in user's language)
  originalText?: string; // original English text (for Mitra responses)
  timestamp: Date;
  isLoading?: boolean;
}

const quickPrompts = [
  { label: 'Check my crop health', icon: '🌾' },
  { label: 'Should I water today?', icon: '💧' },
  { label: 'Fertilizer advice', icon: '🧪' },
  { label: 'Weather impact on my field', icon: '🌦️' },
  { label: 'Best time to harvest', icon: '🌿' },
  { label: 'Soil analysis', icon: '🏔️' },
];

export default function MitraAIPage() {
  const router = useRouter();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [selectedLang, setSelectedLang] = useState(LANGUAGES[0]);
  const [showLangPicker, setShowLangPicker] = useState(false);
  const [mitraOnline, setMitraOnline] = useState<boolean | null>(null);
  const [bars, setBars] = useState([3, 5, 7, 5, 3]);

  // ── Check Mitra status on mount ────────────────────────────────
  useEffect(() => {
    getMitraStatus()
      .then((res) => {
        if (res?.models) {
          setMitraOnline(res.models.mitra || false);
        }
      })
      .catch(() => setMitraOnline(false));
  }, []);

  // ── Auto-scroll to bottom ─────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Animate voice bars ─────────────────────────────────────────
  useEffect(() => {
    if (!isListening) return;
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.floor(Math.random() * 8) + 2));
    }, 150);
    return () => clearInterval(interval);
  }, [isListening]);

  // ── Send message ───────────────────────────────────────────────
  const sendMessage = useCallback(async (rawText: string) => {
    if (!rawText.trim() || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const mitraMsgId = `mitra-${Date.now()}`;

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      text: rawText,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    // Add loading placeholder for Mitra
    setMessages(prev => [...prev, {
      id: mitraMsgId,
      role: 'mitra',
      text: '',
      timestamp: new Date(),
      isLoading: true,
    }]);

    try {
      // Step 1: Translate user input to English if not English
      let englishText = rawText;
      if (selectedLang.code !== 'en') {
        englishText = await translateText(rawText, selectedLang.code, 'en');
      }

      // Step 2: Send to Mitra backend (always in English)
      const res = await mitraChat(englishText);

      let mitraResponseText = '';
      if (res?.response) {
        mitraResponseText = res.response;
      } else if (res?.status === 'success' && res?.response) {
        mitraResponseText = res.response;
      } else {
        mitraResponseText = 'I received your message but couldn\'t generate a response. Please try again.';
      }

      // Step 3: Translate Mitra response back to user's language
      let displayText = mitraResponseText;
      if (selectedLang.code !== 'en') {
        displayText = await translateText(mitraResponseText, 'en', selectedLang.code);
      }

      // Update the loading message with actual response
      setMessages(prev => prev.map(m =>
        m.id === mitraMsgId
          ? { ...m, text: displayText, originalText: mitraResponseText, isLoading: false }
          : m
      ));
    } catch (err: any) {
      setMessages(prev => prev.map(m =>
        m.id === mitraMsgId
          ? {
              ...m,
              text: mitraOnline === false
                ? '⚠️ Mitra AI is not available right now. Please ensure Ollama is running with the gpt4o-s:20b model.'
                : `⚠️ Error: ${err?.message || 'Could not reach Mitra. Check backend connection.'}`,
              isLoading: false,
            }
          : m
      ));
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, selectedLang, mitraOnline]);

  // ── Voice input (Web Speech API) ───────────────────────────────
  const toggleVoice = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser. Please use Chrome.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = selectedLang.speechCode;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
      setIsListening(false);
      // Auto-send after voice input
      setTimeout(() => sendMessage(transcript), 300);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please allow microphone permissions.');
      }
    };

    recognition.onend = () => setIsListening(false);

    recognition.start();
  }, [isListening, selectedLang, sendMessage]);

  // ── Text-to-Speech for Mitra responses ─────────────────────────
  const speakText = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLang.speechCode;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }, [selectedLang]);

  // ── Handle Enter key ───────────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    sendMessage(prompt);
  };

  return (
    <div className="mitra-page">
      {/* Header */}
      <div className="mitra-header">
        <div className="mitra-logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5">
            <line x1="4" y1="8" x2="4" y2="16" /><line x1="8" y1="4" x2="8" y2="20" />
            <line x1="12" y1="6" x2="12" y2="18" /><line x1="16" y1="4" x2="16" y2="20" />
            <line x1="20" y1="8" x2="20" y2="16" />
          </svg>
          <span className="mitra-brand">Mitra AI</span>
          {mitraOnline !== null && (
            <span className={`mitra-status-dot ${mitraOnline ? 'mitra-status-dot--online' : 'mitra-status-dot--offline'}`} />
          )}
        </div>

        {/* Language Picker */}
        <div className="mitra-header-actions">
          <button
            className="mitra-lang-btn"
            onClick={() => setShowLangPicker(!showLangPicker)}
            aria-label="Change language"
            id="btn-lang-picker"
          >
            <span>{selectedLang.flag}</span>
            <span className="mitra-lang-label">{selectedLang.label}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <button className="mitra-close-btn" onClick={() => router.back()} aria-label="Close">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--gray-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Language Picker Dropdown */}
      {showLangPicker && (
        <div className="mitra-lang-dropdown">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              className={`mitra-lang-option ${lang.code === selectedLang.code ? 'mitra-lang-option--active' : ''}`}
              onClick={() => { setSelectedLang(lang); setShowLangPicker(false); }}
            >
              <span>{lang.flag}</span>
              <span>{lang.label}</span>
              {lang.code === selectedLang.code && (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Chat Messages Area */}
      <div className="mitra-chat-area">
        {messages.length === 0 ? (
          <div className="mitra-welcome">
            <div className="mitra-welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="1.5">
                <line x1="4" y1="8" x2="4" y2="16" /><line x1="8" y1="4" x2="8" y2="20" />
                <line x1="12" y1="6" x2="12" y2="18" /><line x1="16" y1="4" x2="16" y2="20" />
                <line x1="20" y1="8" x2="20" y2="16" />
              </svg>
            </div>
            <h2 className="mitra-welcome-title">Namaste! I&apos;m Mitra 🙏</h2>
            <p className="mitra-welcome-sub">
              Your AI farming assistant. Ask me anything about your crops, soil, weather, or farming practices.
            </p>
            <p className="mitra-welcome-hint">
              🎤 Tap the mic to speak in {selectedLang.label} — I understand multiple languages!
            </p>

            {/* Quick Prompts */}
            <div className="mitra-quick-grid">
              {quickPrompts.map(q => (
                <button
                  key={q.label}
                  className="mitra-quick-card"
                  onClick={() => handleQuickPrompt(q.label)}
                >
                  <span className="mitra-quick-icon">{q.icon}</span>
                  <span className="mitra-quick-text">{q.label}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mitra-messages">
            {messages.map(msg => (
              <div key={msg.id} className={`mitra-msg ${msg.role === 'user' ? 'mitra-msg--user' : 'mitra-msg--mitra'}`}>
                {msg.role === 'mitra' && (
                  <div className="mitra-msg-avatar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5">
                      <line x1="4" y1="8" x2="4" y2="16" /><line x1="8" y1="4" x2="8" y2="20" />
                      <line x1="12" y1="6" x2="12" y2="18" /><line x1="16" y1="4" x2="16" y2="20" />
                      <line x1="20" y1="8" x2="20" y2="16" />
                    </svg>
                  </div>
                )}
                <div className={`mitra-msg-bubble ${msg.isLoading ? 'mitra-msg-bubble--loading' : ''}`}>
                  {msg.isLoading ? (
                    <div className="mitra-typing">
                      <span className="mitra-typing-dot" />
                      <span className="mitra-typing-dot" />
                      <span className="mitra-typing-dot" />
                    </div>
                  ) : (
                    <>
                      <p className="mitra-msg-text">{msg.text}</p>
                      {msg.role === 'mitra' && !msg.text.startsWith('⚠️') && (
                        <button
                          className="mitra-speak-btn"
                          onClick={() => speakText(msg.text)}
                          aria-label="Read aloud"
                          title="Read aloud"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                          </svg>
                        </button>
                      )}
                    </>
                  )}
                </div>
                <span className="mitra-msg-time">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Voice Animation (when listening) */}
      {isListening && (
        <div className="mitra-voice-overlay">
          <div className="mitra-voice-bars">
            {bars.map((h, i) => (
              <div key={i} className="mitra-bar mitra-bar--active" style={{ height: `${h * 6}px` }} />
            ))}
          </div>
          <p className="mitra-voice-label">
            Listening in {selectedLang.label}...
          </p>
          <button className="mitra-voice-cancel" onClick={() => setIsListening(false)}>
            Tap to cancel
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="mitra-input-area">
        <div className="mitra-input-row">
          <textarea
            ref={inputRef}
            className="mitra-text-input"
            placeholder={selectedLang.code === 'en' ? 'Ask Mitra anything...' : `Type in ${selectedLang.label}...`}
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
            id="mitra-chat-input"
          />

          {/* Voice Button */}
          <button
            className={`mitra-mic-btn ${isListening ? 'mitra-mic-btn--active' : ''}`}
            onClick={toggleVoice}
            aria-label={isListening ? 'Stop listening' : 'Start listening'}
            disabled={isLoading}
            id="btn-mitra-mic"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </button>

          {/* Send Button */}
          <button
            className="mitra-send-btn"
            onClick={() => sendMessage(inputText)}
            disabled={!inputText.trim() || isLoading}
            aria-label="Send message"
            id="btn-mitra-send"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
