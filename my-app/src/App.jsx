import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const chatRef = useRef(null);

    // Auto-scroll to latest message
    useEffect(() => {
        if (chatRef.current) {
            chatRef.current.scrollTop = chatRef.current.scrollHeight;
        }
    }, [messages]);

    // Create session on load
    
    const createSession = async () => {
        try {
            const res = await fetch(`${API_URL}/create_session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}), // Required for some FastAPI setups
        });

            const data = await res.json();
            setSessionId(data.session_id);
            setMessages([]);
            setInput("");
            console.log("New session started:", data.session_id)
        } catch (error) {
            console.log("Session error:", error);
        }
    };
    

    const sendMessage = async () => {
        if (!input.trim()) return;

        if (!sessionId) {
            alert("Session not created yet. Please wait 1 second.");
            return;
        }

        const userMessage = input;
        setMessages((prev) => [...prev, { role: "user", message: userMessage }]);
        setInput("");

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: userMessage,
                }),
            });

            const data = await res.json();

            // Fallback safety check
            const botReply = data.bot_message || "Error: No response from server.";

            setMessages((prev) => [
                ...prev,
                { role: "assistant", message: botReply },
            ]);
        } catch (error) {
            console.error("Chat error:", error);

            setMessages((prev) => [
                ...prev,
                { role: "assistant", message: "Error: Failed to connect to server." },
            ]);
        }
    };

    const handleEnter = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div>
            <h3>Simple Chatbot</h3>
            {/* Start Session Button */}
            
                <button
                    onClick={createSession}
                    style={{ padding: "5px 10px", marginBottom: "10px" }}
                >
                    Start New Session
                </button>
            

            <div
                ref={chatRef}
                style={{
                    border: "1px solid black",
                    width: "100%",
                    height: "300px",
                    overflowY: "auto",
                    padding: "10px",
                }}
            >
                {messages.map((m, i) => (
                    <div key={i}>
                        <strong>{m.role}:</strong> {m.message}
                    </div>
                ))}
            </div>

            <div style={{ marginTop: "10px" }}>
                <input
                    style={{ width: "80%", padding: "5px" }}
                    placeholder={
                        !sessionId
                            ? "Waiting for session..."
                            : "Type message..."
                    }
                    value={input}
                    disabled={!sessionId}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleEnter}
                />
                <button
                    onClick={sendMessage}
                    disabled={!sessionId}
                    style={{ padding: "5px 10px", marginLeft: "10px" }}
                >
                    Send
                </button>
            </div>
        </div>
    );
}
