import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signInWithPopup 
} from 'firebase/auth';
import { auth, googleProvider } from './firebase';

const colors = {
  bg: "#0B0E14",
  panel: "#151A23",
  accent: "#3B82F6",
  purple: "#8B5CF6",
  textPrimary: "#FFFFFF",
  textSecondary: "#9CA3AF",
  border: "#2A3241",
  red: "#EF4444",
};

const AuthPage = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [contact, setContact] = useState(''); // Email or Phone
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Helper to format phone number into our dummy masked email
  const getAuthEmail = (input) => {
    // If it literally looks like an email, return as-is
    if (input.includes('@')) {
      return input.trim();
    }
    // Otherwise, treat as phone number and append the alias domain
    const cleanPhone = input.replace(/\D/g, ''); // strip non-digits
    return `${cleanPhone}@capstone.user`;
  };

  const handleEmailPasswordAuth = async (e) => {
    e.preventDefault();
    if (!contact || !password) {
      setError("Please fill out all fields.");
      return;
    }

    setLoading(true);
    setError('');

    const authEmail = getAuthEmail(contact);

    try {
      let userCredential;
      if (isLogin) {
        userCredential = await signInWithEmailAndPassword(auth, authEmail, password);
      } else {
        userCredential = await createUserWithEmailAndPassword(auth, authEmail, password);
      }
      // Assuming App.js handles the global onAuthStateChanged,
      // but we can also trigger a manual callback if wanted.
      if (onAuthSuccess) onAuthSuccess(userCredential.user);
      
    } catch (err) {
      console.error(err);
      switch (err.code) {
        case 'auth/user-not-found':
        case 'auth/wrong-password':
        case 'auth/invalid-credential':
          setError("Invalid login credentials.");
          break;
        case 'auth/email-already-in-use':
          setError("An account with this email/phone already exists.");
          break;
        case 'auth/weak-password':
          setError("Password should be at least 6 characters.");
          break;
        default:
          setError("Authentication failed. " + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    setLoading(true);
    setError('');
    try {
      const userCred = await signInWithPopup(auth, googleProvider);
      if (onAuthSuccess) onAuthSuccess(userCred.user);
    } catch (err) {
      console.error(err);
      setError("Google Sign-In failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: colors.bg,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      fontFamily: "'Inter', sans-serif",
      color: colors.textPrimary,
      padding: "20px"
    }}>
      <motion.div 
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={{
          width: "100%",
          maxWidth: "400px",
          background: colors.panel,
          border: `1px solid ${colors.border}`,
          borderRadius: "16px",
          padding: "40px 32px",
          boxShadow: `0 20px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)`
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <img 
            src="/logo192.png" 
            alt="FraudShield" 
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "18px",
              margin: "0 auto 12px",
              display: "block",
              boxShadow: `0 8px 24px ${colors.accent}40`
            }}
          />
          <h1 style={{ margin: "0 0 4px", fontSize: "28px", fontWeight: "800", background: `linear-gradient(135deg, ${colors.accent}, ${colors.purple})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            FraudShield
          </h1>
          <h2 style={{ margin: 0, fontSize: "18px", fontWeight: "600", color: colors.textPrimary }}>
            {isLogin ? "Welcome Back" : "Create Account"}
          </h2>
          <p style={{ margin: "8px 0 0", color: colors.textSecondary, fontSize: "13px" }}>
            AI-powered digital arrest detection & fraud investigation
          </p>
        </div>

        <form onSubmit={handleEmailPasswordAuth} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "13px", color: colors.textSecondary, marginBottom: "6px" }}>
              Email address or Phone number
            </label>
            <input 
              type="text" 
              placeholder="user@example.com or 9876543210"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              style={{
                width: "100%",
                padding: "12px 14px",
                background: "rgba(0,0,0,0.2)",
                border: `1px solid ${colors.border}`,
                borderRadius: "10px",
                color: colors.textPrimary,
                fontSize: "14px",
                outline: "none",
                transition: "border-color 0.2s"
              }}
              onFocus={(e) => e.target.style.borderColor = colors.accent}
              onBlur={(e) => e.target.style.borderColor = colors.border}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", color: colors.textSecondary, marginBottom: "6px" }}>
              Password
            </label>
            <input 
              type="password" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "12px 14px",
                background: "rgba(0,0,0,0.2)",
                border: `1px solid ${colors.border}`,
                borderRadius: "10px",
                color: colors.textPrimary,
                fontSize: "14px",
                outline: "none",
                transition: "border-color 0.2s"
              }}
              onFocus={(e) => e.target.style.borderColor = colors.accent}
              onBlur={(e) => e.target.style.borderColor = colors.border}
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: "auto" }} 
                exit={{ opacity: 0, height: 0 }}
                style={{ color: colors.red, fontSize: "13px", textAlign: "center", margin: "4px 0" }}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <button 
            type="submit" 
            disabled={loading}
            style={{
              width: "100%",
              padding: "14px",
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.purple})`,
              color: "#FFF",
              border: "none",
              borderRadius: "10px",
              fontSize: "15px",
              fontWeight: "600",
              cursor: loading ? "wait" : "pointer",
              marginTop: "8px",
              opacity: loading ? 0.7 : 1,
              transition: "opacity 0.2s"
            }}
          >
            {loading ? "Please wait..." : (isLogin ? "Sign In" : "Sign Up")}
          </button>
        </form>

        <div style={{ display: "flex", alignItems: "center", margin: "24px 0" }}>
          <div style={{ flex: 1, height: "1px", background: colors.border }}></div>
          <div style={{ padding: "0 12px", color: colors.textSecondary, fontSize: "12px", textTransform: "uppercase" }}>Or continue with</div>
          <div style={{ flex: 1, height: "1px", background: colors.border }}></div>
        </div>

        <button 
          onClick={handleGoogleAuth}
          disabled={loading}
          style={{
            width: "100%",
            padding: "12px",
            background: "transparent",
            color: colors.textPrimary,
            border: `1px solid ${colors.border}`,
            borderRadius: "10px",
            fontSize: "14px",
            fontWeight: "500",
            cursor: loading ? "wait" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            transition: "background 0.2s"
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
          onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Sign in with Google
        </button>

        <div style={{ textAlign: "center", marginTop: "24px", fontSize: "14px", color: colors.textSecondary }}>
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button 
            onClick={() => setIsLogin(!isLogin)}
            style={{
              background: "none",
              border: "none",
              color: colors.accent,
              fontWeight: "600",
              cursor: "pointer",
              marginLeft: "6px"
            }}
          >
            {isLogin ? "Sign Up" : "Log In"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default AuthPage;
