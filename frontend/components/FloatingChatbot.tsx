"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ChevronDown,
  RefreshCw,
  Zap,
  CheckCircle2,
  HelpCircle,
  Minimize2,
  Maximize2,
  ExternalLink,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Square,
  Radio,
} from "lucide-react";
import Link from "next/link";
import { resilientFetch } from "@/lib/api-config";

interface Message {
  id: string;
  sender: "bot" | "user";
  text: string;
  timestamp: string;
  options?: string[];
  link?: { text: string; href: string };
  isLive?: boolean;
}

const INITIAL_SUGGESTIONS = [
  "🔍 How does automated lead discovery work?",
  "💼 How do I convert a lead into a Client?",
  "📊 Explain the 9-stage CRM pipeline",
  "💬 Can I connect my WhatsApp & Gmail?",
  "💰 What are the pricing tiers?",
  "⚡ What services does Client Magnet support?",
];

const KNOWLEDGE_RESPONSES: { [key: string]: { text: string; link?: { text: string; href: string }; options?: string[] } } = {
  discovery: {
    text: "Client Magnet continuously monitors legitimate global job feeds, freelance portals, and allows manual/CSV imports. Incoming opportunities are analyzed by AI, scored for client intent, and matched directly to your active services catalog.",
    link: { text: "Explore Leads Discovery", href: "/leads" },
    options: ["How does intent scoring work?", "What services can I configure?"],
  },
  convert: {
    text: "When a lead reaches the WON stage in your CRM Pipeline, simply click 'Convert to Client' on the card. This transitions them into an active Client retainer record, tracks total lifetime value, and starts client onboarding.",
    link: { text: "Open CRM Pipeline", href: "/crm" },
    options: ["View Clients Directory", "Explain the 9 pipeline stages"],
  },
  pipeline: {
    text: "The 9-stage CRM pipeline tracks deals through: 1. NEW ➔ 2. QUALIFIED ➔ 3. CONTACTED ➔ 4. REPLIED ➔ 5. INTERESTED ➔ 6. DISCOVERY ➔ 7. PROPOSAL ➔ 8. NEGOTIATION ➔ 9. WON / LOST. Every status movement is recorded.",
    link: { text: "Go to 9-Stage CRM", href: "/crm" },
    options: ["How do I convert a lead into a Client?", "What is intent scoring?"],
  },
  whatsapp: {
    text: "Yes! Client Magnet features a Unified Inbox with Meta WhatsApp Cloud API and Gmail integration. You can send personalized outreach, receive client replies, and generate AI consultative reply drafts with zero spam policy.",
    link: { text: "Open Unified Inbox", href: "/email" },
    options: ["How does Gmail integration work?", "What are the pricing tiers?"],
  },
  pricing: {
    text: "Client Magnet offers 3 tiers:\n• Free Starter ($0/mo): 50 active leads, 3 services, 9-stage CRM\n• Growth Agency ($29/mo): Unlimited leads, AI intent scoring, WhatsApp/Gmail inbox, Social studio\n• Enterprise ($79/mo): Priority workers, custom webhooks, dedicated cluster",
    link: { text: "View Pricing Plans", href: "/#pricing" },
    options: ["Get Started Free", "How does lead discovery work?"],
  },
  services: {
    text: "Client Magnet comes pre-configured for the 3 highest-paying freelance & agency niches:\n1. Website Design & Development (deals up to $8,000+)\n2. Graphics & Brand Identity (deals up to $4,000+)\n3. Bot & Automation Development (deals up to $6,000+)",
    link: { text: "Manage Services Catalog", href: "/services" },
    options: ["Explain the 9-stage CRM pipeline", "What are the pricing tiers?"],
  },
  outreach: {
    text: "With AI assistance, you can generate personalized, consultative outreach emails and WhatsApp messages tailored to the specific client's detected problem and your portfolio credentials in 1 click.",
    link: { text: "Draft Outreach Now", href: "/email" },
    options: ["Can I connect my WhatsApp & Gmail?", "How does automated lead discovery work?"],
  },
};

export default function FloatingChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-1",
      sender: "bot",
      text: "👋 Hi there! I'm Magnet AI, your live 24/7 autonomous voice & growth copilot. You can speak to me or type your questions about acquiring clients, closing deals, and scaling revenue!",
      timestamp: "Just now",
      options: INITIAL_SUGGESTIONS.slice(0, 4),
      isLive: true,
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [unreadCount, setUnreadCount] = useState(1);

  // Voice States
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentlySpeakingId, setCurrentlySpeakingId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isMinimized, isTyping]);

  // Clean text for speech synthesis
  const cleanTextForSpeech = (rawText: string) => {
    return rawText
      .replace(/[*#_`>•]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/[\n\r]+/g, ". ")
      .trim();
  };

  // Text-To-Speech (Voice Output)
  const speakText = (text: string, msgId?: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const clean = cleanTextForSpeech(text);
    if (!clean) return;

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    // Pick natural voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) => (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Premium") || v.name.includes("Samantha")) && v.lang.startsWith("en")
    );
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    utterance.onstart = () => {
      setIsSpeaking(true);
      if (msgId) setCurrentlySpeakingId(msgId);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setCurrentlySpeakingId(null);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setCurrentlySpeakingId(null);
    };

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentlySpeakingId(null);
    }
  };

  // Speech-To-Text (Microphone Voice Input)
  const startListening = () => {
    if (typeof window === "undefined") return;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setInputValue(transcript);
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Failed to start voice recognition:", err);
      setIsListening(false);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
    setIsMinimized(false);
    setUnreadCount(0);
  };

  const getFallbackBotReply = (userQuery: string): { text: string; link?: { text: string; href: string }; options?: string[] } => {
    const q = userQuery.toLowerCase();

    if (q.includes("lead") || q.includes("discover") || q.includes("source") || q.includes("find client")) {
      return KNOWLEDGE_RESPONSES.discovery;
    }
    if (q.includes("convert") || q.includes("client") || q.includes("won") || q.includes("retainer")) {
      return KNOWLEDGE_RESPONSES.convert;
    }
    if (q.includes("pipeline") || q.includes("stage") || q.includes("crm") || q.includes("kanban") || q.includes("funnel")) {
      return KNOWLEDGE_RESPONSES.pipeline;
    }
    if (q.includes("whatsapp") || q.includes("gmail") || q.includes("email") || q.includes("message") || q.includes("inbox")) {
      return KNOWLEDGE_RESPONSES.whatsapp;
    }
    if (q.includes("price") || q.includes("pricing") || q.includes("cost") || q.includes("plan") || q.includes("free") || q.includes("subscription")) {
      return KNOWLEDGE_RESPONSES.pricing;
    }
    if (q.includes("service") || q.includes("web") || q.includes("graphic") || q.includes("bot") || q.includes("niche")) {
      return KNOWLEDGE_RESPONSES.services;
    }
    if (q.includes("outreach") || q.includes("draft") || q.includes("proposal") || q.includes("pitch")) {
      return KNOWLEDGE_RESPONSES.outreach;
    }
    if (q.includes("hello") || q.includes("hi") || q.includes("hey")) {
      return {
        text: "Hello! Great to connect with you. What would you like to explore about Client Magnet today?",
        options: ["🔍 How does automated lead discovery work?", "📊 Explain the 9-stage CRM pipeline", "💰 What are the pricing tiers?"],
      };
    }

    return {
      text: `That's a great question about "${userQuery}". Client Magnet is engineered to automate your entire freelance client acquisition process—from discovering high-budget job leads and scoring client intent with AI, to organizing your deals in a 9-stage CRM and managing omnichannel communication.`,
      options: [
        "🔍 How does automated lead discovery work?",
        "📊 Explain the 9-stage CRM pipeline",
        "💬 Can I connect my WhatsApp & Gmail?",
        "💰 What are the pricing tiers?",
      ],
      link: { text: "Explore Live Dashboard", href: "/crm" },
    };
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputValue).trim();
    if (!query) return;

    if (isListening) {
      stopListening();
    }
    stopSpeaking();

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    try {
      const res = await resilientFetch("/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });

      if (res.ok) {
        const data = await res.json();
        const msgId = `bot-${Date.now()}`;
        const replyContent = data.reply || data.text;
        const botMsg: Message = {
          id: msgId,
          sender: "bot",
          text: replyContent,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          link: data.link,
          options: data.options,
          isLive: true,
        };
        setMessages((prev) => [...prev, botMsg]);
        setIsTyping(false);

        // Auto-speak if voice mode is enabled
        if (isVoiceEnabled) {
          speakText(replyContent, msgId);
        }
        return;
      }
    } catch (e) {
      console.warn("Live AI chat fetch failed, falling back to instant knowledge engine:", e);
    }

    // Fallback response
    const reply = getFallbackBotReply(query);
    const msgId = `bot-${Date.now()}`;
    const botMsg: Message = {
      id: msgId,
      sender: "bot",
      text: reply.text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      link: reply.link,
      options: reply.options,
      isLive: true,
    };
    setMessages((prev) => [...prev, botMsg]);
    setIsTyping(false);

    if (isVoiceEnabled) {
      speakText(reply.text, msgId);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    stopSpeaking();
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: "bot",
        text: "Chat history cleared. How can I assist you today?",
        timestamp: "Just now",
        options: INITIAL_SUGGESTIONS.slice(0, 4),
      },
    ]);
  };

  return (
    <>
      {/* -------------------------------------------------------------------- */}
      {/* Floating Trigger Launcher Button (Always visible bottom-right)       */}
      {/* -------------------------------------------------------------------- */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
          {/* Subtle invitation tooltip on desktop */}
          <div className="hidden md:flex items-center gap-2 rounded-2xl bg-slate-900/95 border border-slate-800 px-3.5 py-2 text-xs font-bold text-white shadow-xl backdrop-blur-md animate-in fade-in slide-in-from-right-4 duration-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Ask Magnet Voice & AI Copilot</span>
          </div>

          <button
            onClick={handleOpen}
            className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-sky-600 via-blue-600 to-indigo-600 text-white shadow-2xl shadow-sky-500/40 hover:scale-110 active:scale-95 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-sky-400/30"
            aria-label="Open AI Voice Assistant"
          >
            {/* Animated glowing aura ring */}
            <span className="absolute -inset-1 rounded-full bg-gradient-to-r from-sky-400 to-indigo-500 opacity-60 blur-md group-hover:opacity-100 transition duration-300 -z-10 animate-pulse-glow" />

            <Bot className="h-7 w-7 transition-transform group-hover:rotate-12 duration-200" />

            {/* Unread badge */}
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-[10px] font-black text-white border-2 border-slate-950 animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* Floating Chat Modal Window                                           */}
      {/* -------------------------------------------------------------------- */}
      {isOpen && (
        <div
          className={`fixed z-50 transition-all duration-300 ${
            isMinimized
              ? "bottom-6 right-6 h-14 w-80"
              : "bottom-4 right-4 sm:bottom-6 sm:right-6 w-[calc(100vw-32px)] sm:w-[420px] h-[600px] max-h-[85vh]"
          } rounded-3xl border border-slate-700/80 bg-slate-950/95 shadow-2xl shadow-black/80 backdrop-blur-xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-200`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-slate-950 px-4 py-3.5">
            <div className="flex items-center gap-2.5">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20">
                <Bot className="h-5 w-5" />
                <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 border-2 border-slate-900" />
              </div>
              <div>
                <h3 className="text-xs font-black text-white flex items-center gap-1.5">
                  Magnet AI Copilot
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[9px] font-bold text-emerald-400 border border-emerald-500/30">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    LIVE VOICE & AI
                  </span>
                </h3>
                <p className="text-[10px] text-slate-400">Autonomous Voice & Client Growth Agent</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {/* Voice auto-speak toggle button */}
              <button
                onClick={() => {
                  const nextState = !isVoiceEnabled;
                  setIsVoiceEnabled(nextState);
                  if (!nextState) stopSpeaking();
                }}
                className={`rounded-lg p-1.5 transition ${
                  isVoiceEnabled
                    ? "bg-sky-500/20 text-sky-400 border border-sky-500/40"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
                title={isVoiceEnabled ? "Voice Auto-Read Enabled" : "Enable Voice Auto-Read"}
              >
                {isVoiceEnabled ? <Volume2 className="h-4 w-4 text-sky-400 animate-pulse" /> : <VolumeX className="h-4 w-4" />}
              </button>

              {/* Stop Speaking Button (if active) */}
              {isSpeaking && (
                <button
                  onClick={stopSpeaking}
                  className="rounded-lg p-1.5 text-rose-400 hover:bg-rose-500/20 transition border border-rose-500/30"
                  title="Stop AI voice"
                >
                  <Square className="h-3.5 w-3.5 fill-rose-400" />
                </button>
              )}

              <button
                onClick={clearChat}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition"
                title="Clear chat history"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition"
                title={isMinimized ? "Maximize" : "Minimize"}
              >
                {isMinimized ? <Maximize2 className="h-3.5 w-3.5" /> : <Minimize2 className="h-3.5 w-3.5" />}
              </button>
              <button
                onClick={() => {
                  stopSpeaking();
                  stopListening();
                  setIsOpen(false);
                }}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-rose-400 transition"
                title="Close chat"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Chat Messages Body (Hidden when minimized) */}
          {!isMinimized && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${
                      msg.sender === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div className="flex items-end gap-2 max-w-[88%]">
                      {msg.sender === "bot" && (
                        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-sky-600 text-white text-[10px] font-bold shadow-xs">
                          <Bot className="h-3.5 w-3.5" />
                        </div>
                      )}

                      <div
                        className={`relative rounded-2xl px-4 py-2.5 shadow-sm leading-relaxed whitespace-pre-line group ${
                          msg.sender === "user"
                            ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white font-medium rounded-br-xs"
                            : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-xs"
                        }`}
                      >
                        {msg.text}

                        {/* Speaker button on bot message */}
                        {msg.sender === "bot" && (
                          <div className="mt-2 pt-1.5 border-t border-slate-800/60 flex items-center justify-between gap-2">
                            <button
                              onClick={() => {
                                if (currentlySpeakingId === msg.id && isSpeaking) {
                                  stopSpeaking();
                                } else {
                                  speakText(msg.text, msg.id);
                                }
                              }}
                              className="inline-flex items-center gap-1 text-[10px] text-sky-400 hover:text-sky-300 font-semibold"
                            >
                              {currentlySpeakingId === msg.id && isSpeaking ? (
                                <>
                                  <Square className="h-2.5 w-2.5 fill-rose-400 text-rose-400" />
                                  <span className="text-rose-400">Stop Speaking</span>
                                </>
                              ) : (
                                <>
                                  <Volume2 className="h-3 w-3" />
                                  <span>Listen Aloud</span>
                                </>
                              )}
                            </button>

                            {/* Optional action link */}
                            {msg.link && (
                              <Link
                                href={msg.link.href}
                                onClick={() => setIsOpen(false)}
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-400 hover:text-indigo-300 hover:underline"
                              >
                                {msg.link.text} <ExternalLink className="h-2.5 w-2.5" />
                              </Link>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <span className="text-[9px] text-slate-500 mt-1 px-1">{msg.timestamp}</span>

                    {/* Suggested follow-up quick chips */}
                    {msg.options && msg.options.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 max-w-[90%]">
                        {msg.options.map((opt, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(opt)}
                            className="rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-[10px] font-semibold text-sky-300 hover:bg-slate-800 hover:border-sky-500/40 transition active:scale-95 text-left"
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Animated Typing Indicator */}
                {isTyping && (
                  <div className="flex items-center gap-2 text-slate-400">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-sky-600 text-white text-[10px]">
                      <Bot className="h-3.5 w-3.5" />
                    </div>
                    <div className="rounded-2xl bg-slate-900 border border-slate-800 px-3.5 py-2 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Bar with Voice Microphone */}
              <div className="p-3 border-t border-slate-800 bg-slate-950">
                {isListening && (
                  <div className="mb-2 flex items-center justify-between rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs text-rose-400 animate-pulse">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping" />
                      <span className="font-semibold text-[11px]">Listening to your voice... speak now</span>
                    </div>
                    <button
                      onClick={stopListening}
                      className="text-[10px] font-bold text-rose-300 underline"
                    >
                      Done
                    </button>
                  </div>
                )}

                <div className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/90 px-3 py-1.5 focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-500/20 transition">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={isListening ? "Listening..." : "Ask or speak to Magnet AI..."}
                    className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
                  />

                  {/* Microphone Voice Input Button */}
                  <button
                    type="button"
                    onClick={isListening ? stopListening : startListening}
                    className={`flex h-7 w-7 items-center justify-center rounded-xl transition ${
                      isListening
                        ? "bg-rose-500 text-white animate-pulse"
                        : "text-slate-400 hover:bg-slate-800 hover:text-sky-400"
                    }`}
                    title={isListening ? "Stop Recording" : "Speak your message"}
                  >
                    {isListening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
                  </button>

                  {/* Send Button */}
                  <button
                    onClick={() => handleSendMessage()}
                    disabled={!inputValue.trim() || isTyping}
                    className="flex h-7 w-7 items-center justify-center rounded-xl bg-sky-500 text-white hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-md"
                    aria-label="Send message"
                  >
                    <Send className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="mt-1.5 flex items-center justify-center gap-2 text-[9px] text-slate-500">
                  <span>🎙️ Voice Input Enabled</span>
                  <span>•</span>
                  <span>🔊 Text-to-Speech Ready</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
