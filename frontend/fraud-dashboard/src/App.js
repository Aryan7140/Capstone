import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "./firebase";
import AuthPage from "./Auth";

// ========================================
// DESIGN TOKENS
// ========================================
const colors = {
  bg: "#0a0e1a",
  surface: "#111827",
  surfaceLight: "#1e293b",
  border: "#1f2937",
  accent: "#6366f1",
  accentGlow: "rgba(99, 102, 241, 0.3)",
  green: "#22c55e",
  red: "#ef4444",
  orange: "#f59e0b",
  cyan: "#06b6d4",
  purple: "#a855f7",
  white: "#f8fafc",
  muted: "#94a3b8",
  textSecondary: "#64748b",
};

const PIE_COLORS = ["#ef4444", "#f59e0b", "#22c55e"];
const SPAM_PIE_COLORS = ["#ef4444", "#a855f7", "#22c55e"];

// ========================================
// REUSABLE COMPONENTS
// ========================================

const Card = ({ children, style = {}, glow = false }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    style={{
      background: `linear-gradient(135deg, ${colors.surface} 0%, ${colors.surfaceLight} 100%)`,
      padding: "24px",
      borderRadius: "16px",
      border: `1px solid ${colors.border}`,
      boxShadow: glow
        ? `0 0 30px ${colors.accentGlow}, 0 8px 32px rgba(0,0,0,0.4)`
        : "0 8px 32px rgba(0,0,0,0.3)",
      ...style,
    }}
  >
    {children}
  </motion.div>
);

const StatCard = ({ label, value, color, icon }) => (
  <Card style={{ flex: 1, minWidth: "160px", textAlign: "center" }} glow={color === colors.red}>
    <div style={{ fontSize: "28px", marginBottom: "8px" }}>{icon}</div>
    <div style={{ fontSize: "36px", fontWeight: "800", color, textShadow: `0 0 20px ${color}40` }}>{value}</div>
    <div style={{ fontSize: "13px", color: colors.muted, marginTop: "4px", textTransform: "uppercase", letterSpacing: "1.5px" }}>{label}</div>
  </Card>
);

const SectionTitle = ({ children, icon }) => (
  <h2 style={{ fontSize: "20px", fontWeight: "700", color: colors.white, marginBottom: "16px", display: "flex", alignItems: "center", gap: "10px" }}>
    <span style={{ fontSize: "22px" }}>{icon}</span>{children}
  </h2>
);

const Badge = ({ label, type }) => {
  const badgeColors = {
    DIGITAL_ARREST_SCAM: { bg: "#dc262620", text: "#ef4444", border: "#ef444440" },
    SUSPICIOUS: { bg: "#f59e0b20", text: "#f59e0b", border: "#f59e0b40" },
    SAFE: { bg: "#22c55e20", text: "#22c55e", border: "#22c55e40" },
    CRITICAL: { bg: "#dc262620", text: "#ef4444", border: "#ef444440" },
    HIGH: { bg: "#f97316aa", text: "#fb923c", border: "#f9731640" },
    MEDIUM: { bg: "#06b6d420", text: "#06b6d4", border: "#06b6d440" },
    LOW: { bg: "#22c55e20", text: "#22c55e", border: "#22c55e40" },
    FRAUD: { bg: "#dc262620", text: "#ef4444", border: "#ef444440" },
  };
  const c = badgeColors[type] || badgeColors.SAFE;
  return (
    <span style={{ display: "inline-block", padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: "700", letterSpacing: "0.5px", background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
      {label}
    </span>
  );
};

const TabButton = ({ active, children, onClick }) => (
  <button onClick={onClick} style={{ padding: "12px 28px", background: active ? `linear-gradient(135deg, ${colors.accent}, ${colors.purple})` : "transparent", color: active ? colors.white : colors.muted, border: active ? "none" : `1px solid ${colors.border}`, borderRadius: "12px", cursor: "pointer", fontSize: "14px", fontWeight: "600", transition: "all 0.3s ease", letterSpacing: "0.5px" }}>
    {children}
  </button>
);

const InputField = ({ label, icon, value, onChange, placeholder, type = "text", required = false }) => (
  <div style={{ marginBottom: "16px" }}>
    <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: colors.muted, marginBottom: "6px", textTransform: "uppercase", letterSpacing: "1px" }}>
      {icon} {label} {required && <span style={{ color: colors.red }}>*</span>}
    </label>
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{ width: "100%", padding: "14px 16px", borderRadius: "12px", border: `1px solid ${colors.border}`, background: colors.bg, color: colors.white, fontSize: "15px", fontFamily: "inherit", boxSizing: "border-box", outline: "none", transition: "border-color 0.2s" }}
      onFocus={(e) => (e.target.style.borderColor = colors.accent)}
      onBlur={(e) => (e.target.style.borderColor = colors.border)}
    />
  </div>
);

const MetricBox = ({ label, value, color }) => (
  <div style={{ background: colors.bg, padding: "16px", borderRadius: "12px", textAlign: "center" }}>
    <div style={{ fontSize: "24px", fontWeight: "700", color }}>{value}</div>
    <div style={{ fontSize: "11px", color: colors.muted, marginTop: "4px", textTransform: "uppercase" }}>{label}</div>
  </div>
);

// Format INR
const formatINR = (num) => {
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(1)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(1)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)}K`;
  return `₹${num}`;
};


// ========================================
// ANIMATED SCORE COMPONENTS
// ========================================

/** Animated number counter — smoothly counts from 0 → target */
const AnimatedCounter = ({ value, duration = 1800, decimals = 1 }) => {
  const [display, setDisplay] = useState(0);
  const displayRef = useRef(0);

  useEffect(() => {
    const target = typeof value === "number" ? value : parseFloat(value) || 0;
    const start = displayRef.current;
    if (target === start) return;

    const startTime = performance.now();
    let raf;
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;
      const rounded = parseFloat(current.toFixed(decimals));
      
      setDisplay(rounded);
      displayRef.current = rounded;
      
      if (progress < 1) raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [value, duration, decimals]);

  return <>{display}</>;
};


/** SVG Circular Threat Gauge with animated draw + color transitions */
const ThreatScoreGauge = ({ score, size = 160 }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const target = typeof score === "number" ? score : parseFloat(score) || 0;
    const startTime = performance.now();
    let raf;
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / 2000, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(target * eased * 10) / 10);
      if (progress < 1) raf = requestAnimationFrame(animate);
      else setAnimatedScore(target);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const getColor = (s) => {
    if (s >= 70) return "#ef4444";
    if (s >= 50) return "#f97316";
    if (s >= 30) return "#f59e0b";
    if (s >= 15) return "#06b6d4";
    return "#22c55e";
  };

  const strokeWidth = 10;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;
  const color = getColor(animatedScore);

  const getLabel = (s) => {
    if (s >= 70) return "CRITICAL";
    if (s >= 50) return "HIGH";
    if (s >= 30) return "MEDIUM";
    if (s >= 15) return "LOW";
    return "SAFE";
  };

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1e293b" strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            transition: "stroke 0.4s ease",
            filter: `drop-shadow(0 0 10px ${color}80)`,
          }}
        />
      </svg>
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)", textAlign: "center"
      }}>
        <div style={{
          fontSize: size * 0.24, fontWeight: "800", color,
          textShadow: `0 0 24px ${color}60`,
          animation: animatedScore >= 50 ? "score-glow 2s ease-in-out infinite" : "none",
        }}>
          {animatedScore}%
        </div>
        <div style={{
          fontSize: size * 0.075, color: colors.muted,
          textTransform: "uppercase", letterSpacing: "2px", marginTop: "2px"
        }}>
          {getLabel(animatedScore)}
        </div>
      </div>
    </div>
  );
};

/** Mini metric with animated counter */
const AnimatedMetric = ({ label, value, suffix = "%", color, icon }) => (
  <div style={{
    background: colors.bg, padding: "14px 16px", borderRadius: "12px",
    textAlign: "center", minWidth: "110px"
  }}>
    {icon && <div style={{ fontSize: "16px", marginBottom: "4px" }}>{icon}</div>}
    <div style={{ fontSize: "22px", fontWeight: "700", color }}>
      <AnimatedCounter value={value} />{suffix}
    </div>
    <div style={{
      fontSize: "10px", color: colors.muted, marginTop: "4px",
      textTransform: "uppercase", letterSpacing: "0.8px"
    }}>
      {label}
    </div>
  </div>
);


/** Live mic waveform visualization */
const MicWaveform = () => (
  <div style={{ display: "flex", alignItems: "center", gap: "3px", height: "24px" }}>
    {[1, 2, 3, 4, 5].map((n) => (
      <div key={n} style={{
        width: "3px",
        background: "#ef4444",
        borderRadius: "2px",
        animation: `wave-bar-${n} 0.${5 + n}s ease-in-out infinite`,
      }} />
    ))}
  </div>
);


// ========================================
// MAIN APP
// ========================================
export default function App() {
  // === AUTHENTICATION STATE ===
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const [activeTab, setActiveTab] = useState("investigate");

  // Transaction fraud state
  const [txnData, setTxnData] = useState([]);
  const [txnAlerts, setTxnAlerts] = useState([]);
  const [txnFilter, setTxnFilter] = useState("");

  // Investigation state
  const [phoneNumber, setPhoneNumber] = useState("");
  const [callerName, setCallerName] = useState("");
  const [emailInput, setEmailInput] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [investigateResult, setInvestigateResult] = useState(null);
  const [isInvestigating, setIsInvestigating] = useState(false);

  // Spam-only state
  const [spamSummary, setSpamSummary] = useState(null);

  // Collapsible
  const [showShap, setShowShap] = useState(false);
  const [showNetwork, setShowNetwork] = useState(false);

  // ========================================
  // SPEECH RECOGNITION (Mic) STATE
  // ========================================
  const [isListening, setIsListening] = useState(false);
  const [micError, setMicError] = useState("");
  const [micSupported, setMicSupported] = useState(true);
  const recognitionRef = useRef(null);
  const baseTextRef = useRef("");       // text in textarea when recording started
  const interimDisplayRef = useRef(""); // current interim text being shown

  // Check browser support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicSupported(false);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  const startListening = useCallback(() => {
    setMicError("");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicError("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    // Request mic permission explicitly
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        // Permission granted — stop the stream tracks (we only needed permission)
        stream.getTracks().forEach(track => track.stop());

        const recognition = new SpeechRecognition();
        // Auto-detect: en-IN handles English + Romanized Hindi (Hinglish) natively
        // This is the best single-language setting for mixed Hindi-English input
        recognition.lang = "en-IN";
        recognition.interimResults = true;  // KEY: enable interim results for real-time display
        recognition.continuous = true;
        recognition.maxAlternatives = 1;

        // Capture the text currently in the textarea as the "base"
        baseTextRef.current = messageInput;
        interimDisplayRef.current = "";

        recognition.onstart = () => {
          setIsListening(true);
        };

        recognition.onresult = (event) => {
          let allFinalizedText = "";
          let currentInterim = "";

          // Iterate ALL results (not just from resultIndex) to capture
          // the full finalized text from this recording session
          for (let i = 0; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              allFinalizedText += transcript + " ";
            } else {
              currentInterim += transcript;
            }
          }

          interimDisplayRef.current = currentInterim;

          // Real-time update: show base + finalized + interim in textarea
          const base = baseTextRef.current;
          const spacer = base && !base.endsWith(" ") && !base.endsWith("\n") ? " " : "";
          const fullText = base + spacer + allFinalizedText + currentInterim;
          setMessageInput(fullText);
        };

        recognition.onerror = (event) => {
          if (event.error === "not-allowed") {
            setMicError("Microphone access denied. Please allow mic permission in your browser settings.");
          } else if (event.error === "no-speech") {
            setMicError("No speech detected. Please try again.");
          } else if (event.error === "network") {
            setMicError("Network error during speech recognition. Check your internet connection.");
          } else {
            setMicError(`Speech recognition error: ${event.error}`);
          }
          setIsListening(false);
          recognitionRef.current = null;
        };

        recognition.onend = () => {
          // Clean up: keep only base + finalized text (no dangling interim)
          setMessageInput(prev => {
            // Remove any trailing interim by reconstructing from what was finalized
            // The last onresult already set the text, just trim any trailing whitespace
            return prev.trim();
          });
          setIsListening(false);
          recognitionRef.current = null;
        };

        recognitionRef.current = recognition;
        recognition.start();
      })
      .catch((err) => {
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
          setMicError("Microphone access denied. Please allow mic permission in your browser settings.");
        } else {
          setMicError(`Could not access microphone: ${err.message}`);
        }
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      // Capture the CURRENT messageInput at the moment of starting
      // (we read directly since startListening uses baseTextRef)
      baseTextRef.current = messageInput;
      startListening();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isListening, messageInput, startListening, stopListening]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Fetch data on mount
  useEffect(() => {
    fetch("http://localhost:8000/summary").then((r) => r.json()).then(setTxnData).catch(() => {});
    fetch("http://localhost:8000/alerts").then((r) => r.json()).then(setTxnAlerts).catch(() => {});
    fetch("http://localhost:8000/spam/summary").then((r) => r.json()).then(setSpamSummary).catch(() => {});
  }, []);

  // Full investigation
  const runInvestigation = async () => {
    if (!messageInput.trim()) return;
    setIsInvestigating(true);
    try {
      const res = await fetch("http://localhost:8000/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: messageInput, phone_number: phoneNumber, name: callerName, email: emailInput }),
      });
      const result = await res.json();
      setInvestigateResult(result);
    } catch (err) {
      console.error("Investigation failed:", err);
    }
    setIsInvestigating(false);
  };

  const threatColor = (level) => ({ CRITICAL: colors.red, HIGH: colors.orange, MEDIUM: colors.cyan, LOW: colors.green }[level] || colors.muted);

  // === AUTHENTICATION GATEWAY ===
  if (authLoading) {
    return (
      <div style={{ minHeight: "100vh", background: colors.bg, display: "flex", alignItems: "center", justifyContent: "center", color: colors.white }}>
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }} style={{ fontSize: "40px" }}>⏳</motion.div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuthSuccess={(u) => setUser(u)} />;
  }

  return (
    <div style={{ minHeight: "100vh", background: `linear-gradient(180deg, ${colors.bg} 0%, #0d1321 100%)`, color: colors.white, fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>

      {/* HEADER */}
      <header style={{ padding: "24px 40px", borderBottom: `1px solid ${colors.border}`, background: `linear-gradient(135deg, ${colors.bg}ee, ${colors.surface}cc)`, backdropFilter: "blur(20px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: "1400px", margin: "0 auto" }}>
          <div>
            <h1 style={{ fontSize: "26px", fontWeight: "800", margin: 0, background: `linear-gradient(135deg, ${colors.accent}, ${colors.cyan})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              🛡️ FraudShield
            </h1>
            <p style={{ fontSize: "13px", color: colors.muted, margin: "4px 0 0" }}>Real-time fraud detection & spam caller identification</p>
          </div>
          <div style={{ display: "flex", gap: "24px", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: "8px" }}>
              <TabButton active={activeTab === "investigate"} onClick={() => setActiveTab("investigate")}>🔍 Investigate</TabButton>
              <TabButton active={activeTab === "dashboard"} onClick={() => setActiveTab("dashboard")}>📊 Dashboard</TabButton>
              <TabButton active={activeTab === "alerts"} onClick={() => setActiveTab("alerts")}>🚨 Alerts</TabButton>
            </div>
            
            <div style={{ height: "30px", width: "1px", background: colors.border }}></div>
            
            <button 
              onClick={() => signOut(auth)}
              style={{
                padding: "8px 16px",
                background: "transparent",
                color: colors.muted,
                border: `1px solid ${colors.border}`,
                borderRadius: "10px",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                transition: "all 0.2s"
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = colors.red; e.currentTarget.style.borderColor = colors.red; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = colors.muted; e.currentTarget.style.borderColor = colors.border; }}
            >
              <span>👤 {user?.email ? user.email.replace("@capstone.user", "") : "Account"}</span>
              <span style={{ marginLeft: "4px" }}>• Log Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* MAIN */}
      <main style={{ maxWidth: "1400px", margin: "0 auto", padding: "32px 40px" }}>
        <AnimatePresence mode="wait">

          {/* ==================== INVESTIGATE TAB ==================== */}
          {activeTab === "investigate" && (
            <motion.div key="investigate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>

              {/* INPUT FORM */}
              <Card glow style={{ marginBottom: "24px" }}>
                <SectionTitle icon="🔍">Investigate Suspicious Call / Message</SectionTitle>
                <p style={{ color: colors.muted, fontSize: "14px", marginBottom: "20px" }}>
                  Enter the caller details and message. The system will detect spam, extract account numbers, and look up receiver transaction history.
                </p>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
                  <InputField label="Phone Number" icon="📞" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="e.g. 9876543210" />
                  <InputField label="Caller Name" icon="👤" value={callerName} onChange={(e) => setCallerName(e.target.value)} placeholder="e.g. Unknown Caller" />
                  <InputField label="Email Address" icon="📧" value={emailInput} onChange={(e) => setEmailInput(e.target.value)} placeholder="e.g. scammer@fake.com" />
                </div>

                <div style={{ marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <label style={{ fontSize: "13px", fontWeight: "600", color: colors.muted, textTransform: "uppercase", letterSpacing: "1px" }}>
                      💬 Message / Call Transcript <span style={{ color: colors.red }}>*</span>
                    </label>
                    {/* Mic Button — no language selector, auto-detects English + Hindi */}
                    {micSupported && (
                      <button
                        onClick={toggleListening}
                        title={isListening ? "Stop recording" : "Start voice input (English + Hindi auto-detect)"}
                        style={{
                          width: "42px",
                          height: "42px",
                          borderRadius: "50%",
                          border: isListening ? "2px solid #ef4444" : `1px solid ${colors.border}`,
                          background: isListening
                            ? "radial-gradient(circle, #ef444440 0%, #dc262615 100%)"
                            : colors.bg,
                          color: isListening ? "#ef4444" : colors.muted,
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "20px",
                          transition: "all 0.3s ease",
                          animation: isListening ? "mic-pulse 1.5s ease-in-out infinite" : "none",
                          boxShadow: isListening ? "0 0 20px rgba(239, 68, 68, 0.4)" : "none",
                        }}
                        onMouseEnter={(e) => { if (!isListening) { e.currentTarget.style.borderColor = colors.accent; e.currentTarget.style.color = colors.accent; } }}
                        onMouseLeave={(e) => { if (!isListening) { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.color = colors.muted; } }}
                      >
                        🎙️
                      </button>
                    )}
                  </div>

                  {/* Mic Status Bar with waveform */}
                  {isListening && (
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "10px 16px",
                      marginBottom: "8px",
                      borderRadius: "10px",
                      background: "linear-gradient(135deg, #ef444415, #dc262610)",
                      border: "1px solid #ef444430",
                      fontSize: "13px",
                      color: "#ef4444",
                    }}>
                      <MicWaveform />
                      <span style={{ fontWeight: "600" }}>Listening…</span>
                      <span style={{ color: "#ef444480", fontSize: "11px" }}>
                        Auto-detecting English & Hindi
                      </span>
                      <button
                        onClick={stopListening}
                        style={{
                          marginLeft: "auto",
                          padding: "6px 16px",
                          borderRadius: "8px",
                          border: "1px solid #ef444440",
                          background: "#ef444420",
                          color: "#ef4444",
                          cursor: "pointer",
                          fontSize: "12px",
                          fontWeight: "700",
                          transition: "all 0.2s"
                        }}
                      >
                        ⏹ Stop
                      </button>
                    </div>
                  )}

                  {/* Mic Error */}
                  {micError && (
                    <div style={{
                      padding: "8px 14px",
                      marginBottom: "8px",
                      borderRadius: "10px",
                      background: "#f59e0b15",
                      border: "1px solid #f59e0b30",
                      fontSize: "13px",
                      color: "#f59e0b",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}>
                      ⚠️ {micError}
                      <button onClick={() => setMicError("")} style={{ background: "transparent", border: "none", color: "#f59e0b", cursor: "pointer", fontSize: "16px" }}>✕</button>
                    </div>
                  )}

                  {/* Mic Not Supported */}
                  {!micSupported && (
                    <div style={{
                      padding: "8px 14px",
                      marginBottom: "8px",
                      borderRadius: "10px",
                      background: "#64748b15",
                      border: "1px solid #64748b30",
                      fontSize: "13px",
                      color: "#64748b",
                    }}>
                      🎙️ Voice input is not supported in this browser. Please use Google Chrome or Microsoft Edge.
                    </div>
                  )}

                  <textarea
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder={isListening ? "🎙️ Listening... Your speech will appear here in real-time..." : "Paste the suspicious message, SMS, or call transcript here...\n\nExample: This is CBI officer. Transfer ₹2,00,000 to ACC182189 immediately or you will be arrested."}
                    style={{
                      width: "100%",
                      minHeight: "140px",
                      padding: "16px",
                      borderRadius: "12px",
                      border: `1px solid ${isListening ? "#ef444460" : colors.border}`,
                      background: isListening ? `linear-gradient(180deg, ${colors.bg}, #ef444408)` : colors.bg,
                      color: colors.white,
                      fontSize: "15px",
                      fontFamily: "inherit",
                      resize: "vertical",
                      boxSizing: "border-box",
                      outline: "none",
                      transition: "border-color 0.3s, background 0.3s",
                    }}
                    onFocus={(e) => { if (!isListening) e.target.style.borderColor = colors.accent; }}
                    onBlur={(e) => { if (!isListening) e.target.style.borderColor = colors.border; }}
                  />
                </div>

                <div style={{ display: "flex", gap: "12px" }}>
                  <button onClick={runInvestigation} disabled={isInvestigating || !messageInput.trim()} style={{ padding: "14px 32px", background: isInvestigating ? colors.muted : `linear-gradient(135deg, ${colors.accent}, ${colors.purple})`, color: colors.white, border: "none", borderRadius: "12px", cursor: isInvestigating ? "wait" : "pointer", fontSize: "15px", fontWeight: "700" }}>
                    {isInvestigating ? "⏳ Investigating..." : "🔍 Investigate Now"}
                  </button>
                  <button onClick={() => { setMessageInput(""); setPhoneNumber(""); setCallerName(""); setEmailInput(""); setInvestigateResult(null); }} style={{ padding: "14px 24px", background: "transparent", color: colors.muted, border: `1px solid ${colors.border}`, borderRadius: "12px", cursor: "pointer", fontSize: "14px" }}>
                    Clear All
                  </button>
                </div>
              </Card>

              {/* SAMPLE SCENARIOS */}
              {!investigateResult && (
                <Card>
                  <SectionTitle icon="💡">Try Sample Scenarios</SectionTitle>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    {[
                      { phone: "9876543210", name: "CBI Officer", msg: "This is CBI officer. You are under digital arrest for money laundering. Transfer ₹2,00,000 to ACC973758 immediately." },
                      { phone: "8765432109", name: "", msg: "Send me your bank account password and OTP to verify your account number 12345678901234." },
                      { phone: "7654321098", name: "Unknown", msg: "Your Aadhaar is linked to fraud account ACC182189. Verify identity immediately or your bank account will be frozen." },
                      { phone: "", name: "", msg: "Hey, are we meeting for dinner tonight at 7?" },
                    ].map((s, i) => (
                      <button key={i} onClick={() => { setPhoneNumber(s.phone); setCallerName(s.name); setMessageInput(s.msg); }}
                        style={{ padding: "14px 16px", background: colors.bg, color: colors.muted, border: `1px solid ${colors.border}`, borderRadius: "12px", cursor: "pointer", fontSize: "13px", textAlign: "left", lineHeight: "1.5", transition: "all 0.2s ease" }}
                        onMouseEnter={(e) => { e.target.style.borderColor = colors.accent; e.target.style.color = colors.white; }}
                        onMouseLeave={(e) => { e.target.style.borderColor = colors.border; e.target.style.color = colors.muted; }}
                      >
                        {s.phone && <span style={{ color: colors.cyan, fontSize: "12px" }}>📞 {s.phone} </span>}
                        {s.name && <span style={{ color: colors.purple, fontSize: "12px" }}>| {s.name} </span>}
                        <br />{s.msg.length > 100 ? s.msg.slice(0, 100) + "…" : s.msg}
                      </button>
                    ))}
                  </div>
                </Card>
              )}

              {/* INVESTIGATION RESULTS */}
              <AnimatePresence>
                {investigateResult && (
                  <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>

                    {/* FIREBASE HISTORY BANNERS */}
                    {investigateResult.firebase_history && investigateResult.firebase_history.previously_flagged && (
                      <div style={{ padding: "16px", marginBottom: "24px", background: "#ef444420", border: `2px solid ${colors.red}`, borderRadius: "12px", display: "flex", gap: "12px", alignItems: "flex-start", boxShadow: `0 0 20px ${colors.red}40` }}>
                        <div style={{ fontSize: "24px" }}>⚠️</div>
                        <div>
                          <h3 style={{ margin: "0 0 8px 0", color: colors.red, fontSize: "16px", fontWeight: "700" }}>Previously Flagged Entities Detected</h3>
                          <p style={{ margin: 0, color: colors.white, fontSize: "14px", lineHeight: "1.5" }}>
                            The following details have been flagged in prior fraud investigations. Threat score increased!
                            <br/>
                            <span style={{ color: colors.red, fontWeight: "600", display: "block", marginTop: "4px" }}>
                              {investigateResult.firebase_history.flagged_entities.join(", ")}
                            </span>
                          </p>
                        </div>
                      </div>
                    )}
                    
                    {investigateResult.firebase_history && investigateResult.firebase_history.safe_entities?.length > 0 && (
                      <div style={{ padding: "12px", marginBottom: "24px", background: "#22c55e15", border: `1px solid #22c55e40`, borderRadius: "12px", display: "flex", gap: "12px", alignItems: "center" }}>
                        <div style={{ fontSize: "20px" }}>✅</div>
                        <div style={{ color: colors.white, fontSize: "13px" }}>
                          <span style={{ color: colors.green, fontWeight: "700" }}>Database Match: </span> 
                          These entities were previously logged and marked as SAFE: {investigateResult.firebase_history.safe_entities.join(", ")}
                        </div>
                      </div>
                    )}

                    {/* ─── OVERALL THREAT — with animated gauge ─── */}
                    <Card style={{ marginBottom: "24px", borderLeft: `4px solid ${threatColor(investigateResult.overall_threat_level)}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "20px" }}>
                        <div style={{ flex: 1 }}>
                          <SectionTitle icon="🎯">Investigation Result</SectionTitle>
                          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                            <Badge label={`THREAT: ${investigateResult.overall_threat_level}`} type={investigateResult.overall_threat_level} />
                            {investigateResult.has_fraud_linked_account && (
                              <span style={{ padding: "4px 12px", borderRadius: "20px", fontSize: "11px", fontWeight: "700", background: "#dc262630", color: colors.red, border: `1px solid #ef444440` }}>
                                ⚠️ FRAUD-LINKED ACCOUNT
                              </span>
                            )}
                            {/* Threat category badges */}
                            {investigateResult.spam_analysis?.threat_categories?.map((cat, i) => (
                              <Badge key={i} label={cat} type={cat === "VIOLENCE" || cat === "EXTORTION" ? "CRITICAL" : cat === "HARASSMENT" || cat === "INTIMIDATION" ? "HIGH" : "MEDIUM"} />
                            ))}
                          </div>

                          {/* Animated breakdown metrics */}
                          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                            <AnimatedMetric label="Threat Score" value={investigateResult.spam_analysis?.spam_probability || 0} color={colors.red} icon="⚡" />
                            <AnimatedMetric label="Rule Score" value={investigateResult.spam_analysis?.rule_score || 0} color={colors.orange} icon="🔑" />
                            <AnimatedMetric label="ML Score" value={investigateResult.spam_analysis?.ml_spam_probability || 0} color={colors.cyan} icon="🤖" />
                            <AnimatedMetric label="Keyword Score" value={investigateResult.spam_analysis?.keyword_score || 0} color={colors.purple} icon="📝" />
                          </div>
                        </div>

                        {/* Animated circular gauge */}
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                          <ThreatScoreGauge score={investigateResult.combined_threat_score ?? investigateResult.spam_analysis?.combined_score ?? 0} size={170} />
                        </div>
                      </div>

                      {/* Score Breakdown bar */}
                      {investigateResult.score_breakdown && (
                        <div style={{ display: "flex", gap: "16px", marginTop: "20px", paddingTop: "16px", borderTop: `1px solid ${colors.border}` }}>
                          <div style={{ flex: 1, textAlign: "center" }}>
                            <div style={{ fontSize: "18px", fontWeight: "700", color: colors.cyan }}>
                              <AnimatedCounter value={investigateResult.score_breakdown.spam_score} />%
                            </div>
                            <div style={{ fontSize: "10px", color: colors.muted, textTransform: "uppercase", marginTop: "2px" }}>Spam Score</div>
                          </div>
                          <div style={{ width: "1px", background: colors.border }} />
                          <div style={{ flex: 1, textAlign: "center" }}>
                            <div style={{ fontSize: "18px", fontWeight: "700", color: colors.orange }}>
                              +<AnimatedCounter value={investigateResult.score_breakdown.account_risk_boost} />%
                            </div>
                            <div style={{ fontSize: "10px", color: colors.muted, textTransform: "uppercase", marginTop: "2px" }}>Account Risk</div>
                          </div>
                          <div style={{ width: "1px", background: colors.border }} />
                          <div style={{ flex: 1, textAlign: "center" }}>
                            <div style={{ fontSize: "18px", fontWeight: "700", color: colors.purple }}>
                              +<AnimatedCounter value={investigateResult.score_breakdown.amount_boost} />%
                            </div>
                            <div style={{ fontSize: "10px", color: colors.muted, textTransform: "uppercase", marginTop: "2px" }}>Amount Boost</div>
                          </div>
                        </div>
                      )}
                    </Card>

                    {/* CALLER + SPAM + ENTITIES — 3 columns */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px", marginBottom: "24px" }}>

                      {/* Caller Info */}
                      <Card>
                        <SectionTitle icon="📞">Caller Info</SectionTitle>
                        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                          <div style={{ background: colors.bg, padding: "12px 16px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase" }}>Phone</div>
                            <div style={{ fontSize: "16px", fontWeight: "600", fontFamily: "monospace", color: colors.cyan }}>
                              {investigateResult.caller_info?.phone_number || "Not provided"}
                            </div>
                          </div>
                          <div style={{ background: colors.bg, padding: "12px 16px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase" }}>Name</div>
                            <div style={{ fontSize: "16px", fontWeight: "600" }}>
                              {investigateResult.caller_info?.name || "Unknown"}
                            </div>
                          </div>
                          {investigateResult.caller_info?.email && (
                            <div style={{ background: colors.bg, padding: "12px 16px", borderRadius: "10px" }}>
                              <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase" }}>Email</div>
                              <div style={{ fontSize: "14px", fontWeight: "600", color: colors.orange }}>
                                {investigateResult.caller_info.email}
                              </div>
                            </div>
                          )}
                        </div>
                      </Card>

                      {/* Spam Analysis — FIXED: shows effective threat prob, not raw ML */}
                      <Card>
                        <SectionTitle icon="📱">Threat Analysis</SectionTitle>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "12px" }}>
                          <div style={{ background: colors.bg, padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                            <div style={{ fontSize: "24px", fontWeight: "700", color: colors.red }}>
                              <AnimatedCounter value={investigateResult.spam_analysis?.spam_probability || 0} />%
                            </div>
                            <div style={{ fontSize: "11px", color: colors.muted, marginTop: "4px", textTransform: "uppercase" }}>Threat Prob</div>
                          </div>
                          <div style={{ background: colors.bg, padding: "16px", borderRadius: "12px", textAlign: "center" }}>
                            <div style={{ fontSize: "24px", fontWeight: "700", color: colors.orange }}>
                              <AnimatedCounter value={investigateResult.spam_analysis?.keyword_score || 0} />%
                            </div>
                            <div style={{ fontSize: "11px", color: colors.muted, marginTop: "4px", textTransform: "uppercase" }}>Keyword Score</div>
                          </div>
                        </div>
                        <Badge label={investigateResult.spam_analysis?.decision || "N/A"} type={investigateResult.spam_analysis?.decision} />
                        {investigateResult.spam_analysis?.keyword_matches?.length > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "12px" }}>
                            {investigateResult.spam_analysis.keyword_matches.slice(0, 8).map((kw, i) => (
                              <span key={i} style={{ padding: "3px 8px", background: `${colors.red}15`, color: colors.red, borderRadius: "6px", fontSize: "11px" }}>{kw}</span>
                            ))}
                          </div>
                        )}
                      </Card>

                      {/* Extracted Entities */}
                      <Card>
                        <SectionTitle icon="🔎">Extracted Entities</SectionTitle>
                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                          <div style={{ background: colors.bg, padding: "12px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "4px" }}>🏦 Account Numbers</div>
                            {investigateResult.extracted_entities?.account_numbers?.length > 0 ? (
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                                {investigateResult.extracted_entities.account_numbers.map((a, i) => (
                                  <span key={i} style={{ padding: "4px 10px", background: `${colors.accent}20`, color: colors.accent, borderRadius: "8px", fontSize: "13px", fontFamily: "monospace", fontWeight: "700" }}>{a}</span>
                                ))}
                              </div>
                            ) : <span style={{ color: colors.textSecondary, fontSize: "13px" }}>None found</span>}
                          </div>
                          <div style={{ background: colors.bg, padding: "12px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "4px" }}>📞 Phone Numbers</div>
                            {investigateResult.extracted_entities?.phone_numbers?.length > 0 ? (
                              investigateResult.extracted_entities.phone_numbers.map((p, i) => (
                                <span key={`ph-${i}`} style={{ marginRight: "8px", fontFamily: "monospace", color: colors.cyan, fontSize: "13px" }}>{p}</span>
                              ))
                            ) : <span style={{ color: colors.textSecondary, fontSize: "13px" }}>None found</span>}
                          </div>
                          <div style={{ background: colors.bg, padding: "12px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "4px" }}>📧 Emails</div>
                            {investigateResult.extracted_entities?.emails?.length > 0 ? (
                              investigateResult.extracted_entities.emails.map((e, i) => (
                                <span key={`em-${i}`} style={{ marginRight: "8px", fontFamily: "monospace", color: colors.orange, fontSize: "13px" }}>{e}</span>
                              ))
                            ) : <span style={{ color: colors.textSecondary, fontSize: "13px" }}>None found</span>}
                          </div>
                          <div style={{ background: colors.bg, padding: "12px", borderRadius: "10px" }}>
                            <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "4px" }}>💰 Amounts Mentioned</div>
                            {investigateResult.extracted_entities?.amounts_inr?.length > 0 ? (
                              investigateResult.extracted_entities.amounts_inr.map((a, i) => (
                                <span key={i} style={{ marginRight: "8px", fontWeight: "700", color: colors.orange, fontSize: "14px" }}>{formatINR(a)}</span>
                              ))
                            ) : <span style={{ color: colors.textSecondary, fontSize: "13px" }}>None found</span>}
                          </div>
                        </div>
                      </Card>
                    </div>

                    {/* ACCOUNT INVESTIGATIONS */}
                    {investigateResult.account_investigations?.map((acc, idx) => (
                      <Card key={idx} style={{ marginBottom: "20px", borderLeft: `4px solid ${acc.found ? threatColor(acc.risk_level) : colors.muted}` }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                          <SectionTitle icon="🏦">Account: {acc.account_id}</SectionTitle>
                          {acc.found ? (
                            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                              <Badge label={`RISK: ${acc.risk_level}`} type={acc.risk_level} />
                              {acc.in_fraud_report && <Badge label="IN FRAUD REPORT" type="CRITICAL" />}
                              <Badge label={`Role: ${acc.role}`} type="MEDIUM" />
                            </div>
                          ) : <Badge label="NOT FOUND IN DATABASE" type="LOW" />}
                        </div>

                        {acc.found && acc.risk_profile && (
                          <>
                            {/* Stats Grid */}
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "12px", marginBottom: "20px" }}>
                              <MetricBox label="Total Txns" value={acc.risk_profile.total_transactions} color={colors.white} />
                              <MetricBox label="Fraud Txns" value={acc.risk_profile.fraud_count} color={acc.risk_profile.fraud_count > 0 ? colors.red : colors.green} />
                              <MetricBox label="Fraud %" value={`${acc.risk_profile.fraud_percentage}%`} color={acc.risk_profile.fraud_percentage > 10 ? colors.red : colors.green} />
                              <MetricBox label="Total Amount" value={formatINR(acc.risk_profile.total_amount_inr)} color={colors.cyan} />
                              <MetricBox label="Avg Risk" value={`${(acc.risk_profile.avg_risk_engine * 100).toFixed(1)}%`} color={acc.risk_profile.avg_risk_engine > 0.5 ? colors.orange : colors.green} />
                            </div>

                            {/* Profile Details */}
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                              <div style={{ background: colors.bg, padding: "14px", borderRadius: "10px" }}>
                                <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "8px" }}>📍 Top Locations</div>
                                {Object.entries(acc.risk_profile.locations || {}).map(([loc, cnt], i) => (
                                  <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", color: colors.white, marginBottom: "4px" }}>
                                    <span>{loc}</span><span style={{ color: colors.muted }}>{cnt}</span>
                                  </div>
                                ))}
                              </div>
                              <div style={{ background: colors.bg, padding: "14px", borderRadius: "10px" }}>
                                <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "8px" }}>📱 Devices Used</div>
                                {Object.entries(acc.risk_profile.devices_used || {}).map(([dev, cnt], i) => (
                                  <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", color: colors.white, marginBottom: "4px" }}>
                                    <span>{dev}</span><span style={{ color: colors.muted }}>{cnt}</span>
                                  </div>
                                ))}
                              </div>
                              <div style={{ background: colors.bg, padding: "14px", borderRadius: "10px" }}>
                                <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "8px" }}>💳 Payment Channels</div>
                                {Object.entries(acc.risk_profile.payment_channels || {}).map(([ch, cnt], i) => (
                                  <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", color: colors.white, marginBottom: "4px" }}>
                                    <span>{ch}</span><span style={{ color: colors.muted }}>{cnt}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Connected Accounts */}
                            {(Object.keys(acc.connected_accounts?.sent_to || {}).length > 0 || Object.keys(acc.connected_accounts?.received_from || {}).length > 0) && (
                              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                                <div style={{ background: colors.bg, padding: "14px", borderRadius: "10px" }}>
                                  <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "8px" }}>📤 Sent To (Top Receivers)</div>
                                  {Object.entries(acc.connected_accounts?.sent_to || {}).slice(0, 5).map(([a, c], i) => (
                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontFamily: "monospace", color: colors.white, marginBottom: "4px" }}>
                                      <span>{a}</span><span style={{ color: colors.muted }}>{c} txns</span>
                                    </div>
                                  ))}
                                  {Object.keys(acc.connected_accounts?.sent_to || {}).length === 0 && <span style={{ color: colors.textSecondary, fontSize: "12px" }}>None</span>}
                                </div>
                                <div style={{ background: colors.bg, padding: "14px", borderRadius: "10px" }}>
                                  <div style={{ fontSize: "11px", color: colors.muted, textTransform: "uppercase", marginBottom: "8px" }}>📥 Received From (Top Senders)</div>
                                  {Object.entries(acc.connected_accounts?.received_from || {}).slice(0, 5).map(([a, c], i) => (
                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontFamily: "monospace", color: colors.white, marginBottom: "4px" }}>
                                      <span>{a}</span><span style={{ color: colors.muted }}>{c} txns</span>
                                    </div>
                                  ))}
                                  {Object.keys(acc.connected_accounts?.received_from || {}).length === 0 && <span style={{ color: colors.textSecondary, fontSize: "12px" }}>None</span>}
                                </div>
                              </div>
                            )}

                            {/* Transaction History Table */}
                            <div style={{ fontSize: "13px", fontWeight: "600", color: colors.muted, marginBottom: "8px", textTransform: "uppercase" }}>📋 Recent Transaction History</div>
                            <div style={{ maxHeight: "300px", overflowY: "auto", borderRadius: "10px", border: `1px solid ${colors.border}` }}>
                              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                                <thead>
                                  <tr style={{ background: colors.bg, position: "sticky", top: 0 }}>
                                    {["Txn ID", "Date", "Sender", "Receiver", "Amount (₹)", "Type", "Location", "Fraud", "Risk"].map(h => (
                                      <th key={h} style={{ padding: "10px 8px", textAlign: "left", color: colors.muted, fontWeight: "700", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {acc.transaction_history?.map((t, i) => (
                                    <tr key={i} style={{ borderBottom: `1px solid ${colors.border}` }}
                                      onMouseEnter={(e) => (e.currentTarget.style.background = `${colors.accent}10`)}
                                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                                      <td style={tdStyle}><span style={{ fontFamily: "monospace" }}>{t.transaction_id}</span></td>
                                      <td style={tdStyle}>{t.timestamp?.slice(0, 10)}</td>
                                      <td style={tdStyle}><span style={{ fontFamily: "monospace", fontSize: "11px" }}>{t.sender}</span></td>
                                      <td style={tdStyle}><span style={{ fontFamily: "monospace", fontSize: "11px" }}>{t.receiver}</span></td>
                                      <td style={tdStyle}><span style={{ fontWeight: "600" }}>{formatINR(t.amount_inr)}</span></td>
                                      <td style={tdStyle}>{t.type}</td>
                                      <td style={tdStyle}>{t.location}</td>
                                      <td style={tdStyle}>{t.is_fraud ? <span style={{ color: colors.red, fontWeight: "700" }}>YES</span> : <span style={{ color: colors.green }}>NO</span>}</td>
                                      <td style={tdStyle}><span style={{ color: t.risk_score > 0.5 ? colors.red : colors.green, fontWeight: "600" }}>{(t.risk_score * 100).toFixed(1)}%</span></td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </>
                        )}
                      </Card>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* ==================== DASHBOARD TAB ==================== */}
          {activeTab === "dashboard" && (
            <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div style={{ display: "flex", gap: "20px", marginBottom: "32px", flexWrap: "wrap" }}>
                {txnData.map((item, i) => (
                  <StatCard key={i} label={item.name} value={item.value}
                    color={item.name === "FRAUD" ? colors.red : item.name === "SUSPICIOUS" ? colors.orange : colors.green}
                    icon={item.name === "FRAUD" ? "🔴" : item.name === "SUSPICIOUS" ? "🟡" : "🟢"} />
                ))}
                {spamSummary && (
                  <>
                    <StatCard label="Scam Messages" value={spamSummary.summary.scam} color={colors.red} icon="📵" />
                    <StatCard label="Suspicious Msgs" value={spamSummary.summary.suspicious} color={colors.purple} icon="⚠️" />
                    <StatCard label="Safe Msgs" value={spamSummary.summary.safe} color={colors.green} icon="✅" />
                  </>
                )}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "32px" }}>
                <Card>
                  <SectionTitle icon="📊">Transaction Fraud Overview</SectionTitle>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={txnData}>
                      <XAxis dataKey="name" stroke={colors.muted} /><YAxis stroke={colors.muted} />
                      <Tooltip contentStyle={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: "8px", color: colors.white }} itemStyle={{ color: colors.white }} labelStyle={{ color: colors.white }} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                      <Bar dataKey="value" radius={[8, 8, 0, 0]}>{txnData.map((_, i) => (<Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />))}</Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
                <Card>
                  <SectionTitle icon="🔍">Spam Detection Summary</SectionTitle>
                  {spamSummary ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie data={[{ name: "Scam", value: spamSummary.summary.scam }, { name: "Suspicious", value: spamSummary.summary.suspicious }, { name: "Safe", value: spamSummary.summary.safe }]}
                          cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                          {SPAM_PIE_COLORS.map((c, i) => (<Cell key={i} fill={c} />))}
                        </Pie>
                        <Tooltip contentStyle={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: "8px", color: colors.white }} itemStyle={{ color: colors.white }} labelStyle={{ color: colors.white }} />
                        <Legend wrapperStyle={{ color: colors.muted, fontSize: "12px" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : <p style={{ color: colors.muted, textAlign: "center", padding: "80px 0" }}>Loading...</p>}
                </Card>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                <Card>
                  <div onClick={() => setShowNetwork(!showNetwork)} style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <SectionTitle icon="🌐">Fraud Network Graph</SectionTitle>
                    <span style={{ color: colors.muted, fontSize: "20px" }}>{showNetwork ? "▼" : "▶"}</span>
                  </div>
                  <AnimatePresence>{showNetwork && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: "hidden" }}>
                      <img src="http://localhost:8000/network" alt="Fraud Network" style={{ width: "100%", maxHeight: "400px", objectFit: "contain", borderRadius: "12px", marginTop: "12px" }} />
                    </motion.div>
                  )}</AnimatePresence>
                </Card>
                <Card>
                  <div onClick={() => setShowShap(!showShap)} style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <SectionTitle icon="📈">Model Explainability (SHAP)</SectionTitle>
                    <span style={{ color: colors.muted, fontSize: "20px" }}>{showShap ? "▼" : "▶"}</span>
                  </div>
                  <AnimatePresence>{showShap && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: "hidden" }}>
                      <img src="http://localhost:8000/shap_summary" alt="SHAP" style={{ width: "100%", maxHeight: "400px", objectFit: "contain", borderRadius: "12px", marginTop: "12px" }} />
                    </motion.div>
                  )}</AnimatePresence>
                </Card>
              </div>
            </motion.div>
          )}

          {/* ==================== ALERTS TAB ==================== */}
          {activeTab === "alerts" && (
            <motion.div key="alerts" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Card style={{ marginBottom: "24px" }}>
                <SectionTitle icon="🚨">Transaction Fraud Alerts</SectionTitle>
                <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
                  {["", "FRAUD", "SUSPICIOUS", "SAFE"].map((f) => (
                    <button key={f} onClick={() => setTxnFilter(f)} style={{ padding: "8px 20px", background: txnFilter === f ? `linear-gradient(135deg, ${colors.accent}, ${colors.purple})` : colors.bg, color: txnFilter === f ? colors.white : colors.muted, border: `1px solid ${txnFilter === f ? "transparent" : colors.border}`, borderRadius: "10px", cursor: "pointer", fontSize: "13px", fontWeight: "600" }}>
                      {f || "ALL"}
                    </button>
                  ))}
                </div>
                <div style={{ maxHeight: "500px", overflowY: "auto", borderRadius: "12px", border: `1px solid ${colors.border}` }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ background: colors.bg, position: "sticky", top: 0 }}>
                        <th style={thStyle}>#</th><th style={thStyle}>Transaction ID</th><th style={thStyle}>Decision</th><th style={thStyle}>Risk Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {txnAlerts.filter((a) => !txnFilter || a.decision === txnFilter).slice(0, 100).map((a, i) => (
                        <tr key={i} style={{ borderBottom: `1px solid ${colors.border}` }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = `${colors.accent}10`)}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                          <td style={tdStyle}>{i + 1}</td>
                          <td style={tdStyle}><span style={{ fontFamily: "monospace" }}>{a.transaction_id}</span></td>
                          <td style={tdStyle}><Badge label={a.decision} type={a.decision} /></td>
                          <td style={tdStyle}><span style={{ fontWeight: "700", color: a.risk_score >= 4 ? colors.red : a.risk_score >= 2 ? colors.orange : colors.green }}>{a.risk_score}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              {spamSummary?.results && (
                <Card>
                  <SectionTitle icon="📵">Sample Scam Message Analysis</SectionTitle>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {spamSummary.results.map((r, i) => (
                      <div key={i} style={{ padding: "16px", background: colors.bg, borderRadius: "12px", borderLeft: `3px solid ${r.decision === "DIGITAL_ARREST_SCAM" ? colors.red : r.decision === "SUSPICIOUS" ? colors.orange : colors.green}` }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                          <Badge label={r.decision} type={r.decision} />
                          <span style={{ fontSize: "14px", fontWeight: "700", color: r.combined_score >= 70 ? colors.red : r.combined_score >= 40 ? colors.orange : colors.green }}>{r.combined_score}% threat</span>
                        </div>
                        <p style={{ color: colors.muted, fontSize: "13px", margin: 0, lineHeight: "1.5" }}>{r.message}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer style={{ textAlign: "center", padding: "24px", color: colors.textSecondary, fontSize: "13px", borderTop: `1px solid ${colors.border}` }}>
        FraudShield — Digital Arrest Detection System | Capstone Project 2026
      </footer>
    </div>
  );
}

const thStyle = { padding: "14px 16px", textAlign: "left", fontSize: "12px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "1px" };
const tdStyle = { padding: "12px 16px", fontSize: "14px", color: "#e2e8f0" };