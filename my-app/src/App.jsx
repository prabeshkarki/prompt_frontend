import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8000";
const STORAGE_KEY = "chatbot_session_v1";

function Message({ role, children }) {
  const isUser = role === "user";
  return (
    <div
      style={{
        marginBottom: "8px",
        textAlign: isUser ? "right" : "left",
        whiteSpace: "pre-line",
        wordBreak: "break-word",
      }}
    >
      <strong>{isUser ? "You" : "Bot"}:</strong>
      {"\n"}
      {children}
    </div>
  );
}

function loadSavedState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveState(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignore
  }
}

function clearSavedState() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [productId, setProductId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [isSending, setIsSending] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isStoppingSession, setIsStoppingSession] = useState(false);

  // ✅ Only true when we restored a sessionId from localStorage
  const [restoredFromStorage, setRestoredFromStorage] = useState(false);

  const chatRef = useRef(null);

  // 1) Restore from localStorage once on first load
  useEffect(() => {
    const saved = loadSavedState();
    if (saved?.sessionId) {
      setSessionId(saved.sessionId);
      setMessages(Array.isArray(saved.messages) ? saved.messages : []);
      setProductId(saved.productId ?? null);
      setRestoredFromStorage(true);
    } else {
      setRestoredFromStorage(false);
    }
  }, []);

  // 2) Persist to localStorage whenever state changes (while session is active)
  useEffect(() => {
    if (!sessionId) return;

    saveState({
      sessionId,
      productId,
      messages,
    });
  }, [sessionId, productId, messages]);

  // 3) Fetch history ONLY when session was restored (not when newly created)
  useEffect(() => {
    if (!sessionId) return;

    // ✅ do not fetch history for brand-new sessions
    if (!restoredFromStorage) return;

    // ✅ if we already have messages from localStorage, don't fetch
    if (messages.length > 0) return;

    (async () => {
      try {
        const res = await fetch(`${API_URL}/history/${sessionId}`);
        if (!res.ok) return;

        const data = await res.json();
        const restored = Array.isArray(data)
          ? data.map((x) => ({ role: x.role, message: x.message }))
          : [];

        setMessages(restored);
      } catch {
        // ignore
      }
    })();
  }, [sessionId, restoredFromStorage, messages.length]);

  // Auto-scroll
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const createSession = async () => {
    if (isCreatingSession) return;

    try {
      setIsCreatingSession(true);

      // new session => new chat
      setMessages([]);
      setProductId(null);
      setSessionId(null);

      // ✅ important: this session is NOT restored, so no /history fetch
      setRestoredFromStorage(false);

      clearSavedState();

      const res = await fetch(`${API_URL}/create_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!res.ok) throw new Error("Failed to create session");

      const data = await res.json();
      setSessionId(data.session_id);
      setInput("");
    } catch (error) {
      console.error("Session error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "Could not start a new session. Please try again.",
        },
      ]);
    } finally {
      setIsCreatingSession(false);
    }
  };

  // ✅ Stop session = UI-only (NO DELETE/GET request to /session/:id)
  const stopSession = () => {
    if (!sessionId || isStoppingSession) return;

    setIsStoppingSession(true);

    setSessionId(null);
    setMessages([]);
    setProductId(null);
    setInput("");
    clearSavedState();
    setRestoredFromStorage(false);

    setIsStoppingSession(false);
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || !sessionId || isSending || isStoppingSession) return;

    const userMessage = trimmed;
    setMessages((prev) => [...prev, { role: "user", message: userMessage }]);
    setInput("");
    setIsSending(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: userMessage }),
      });

      let botReply = "Error: No response from server.";

      if (res.ok) {
        const data = await res.json();
        botReply = data.bot_message || botReply;

        if (data.product_id) setProductId(data.product_id);
      } else {
        const errorData = await res.json().catch(() => null);
        botReply =
          (errorData && errorData.detail) ||
          "Error: Failed to get a response from the server.";
      }

      setMessages((prev) => [...prev, { role: "assistant", message: botReply }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: "Error: Failed to connect to server." },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleEnter = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto" }}>
      <h3>Simple Product Chatbot</h3>

      {sessionId && (
        <div style={{ marginBottom: "10px", fontSize: "12px", color: "#555" }}>
          <div>
            <strong>Session ID:</strong> {sessionId}
          </div>
          <div>
            <strong>Product ID:</strong> {productId ?? "—"}
          </div>
        </div>
      )}

      {!sessionId ? (
        <button
          onClick={createSession}
          disabled={isCreatingSession}
          style={{ padding: "5px 10px", marginBottom: "10px" }}
        >
          {isCreatingSession ? "Starting..." : "Start Session"}
        </button>
      ) : (
        <button
          onClick={stopSession}
          disabled={isSending || isStoppingSession}
          style={{ padding: "5px 10px", marginBottom: "10px" }}
        >
          {isStoppingSession ? "Stopping..." : "Stop Session"}
        </button>
      )}

      <div
        ref={chatRef}
        style={{
          border: "1px solid #ccc",
          borderRadius: "4px",
          height: "300px",
          padding: "10px",
          overflowY: "auto",
          backgroundColor: "#fafafa",
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#777" }}>
            {!sessionId
              ? "No session active. Click 'Start Session' to begin."
              : "No messages yet. Say hi!"}
          </div>
        )}

        {messages.map((m, i) => (
          <Message key={i} role={m.role}>
            {m.message}
          </Message>
        ))}
      </div>

      <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
        <input
          style={{ flex: 1, padding: "5px" }}
          placeholder={
            !sessionId
              ? "Click 'Start Session' to begin..."
              : "Type your message..."
          }
          value={input}
          disabled={!sessionId || isSending || isStoppingSession}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleEnter}
        />
        <button
          onClick={sendMessage}
          disabled={!sessionId || isSending || isStoppingSession}
          style={{ padding: "5px 10px" }}
        >
          {isSending ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}