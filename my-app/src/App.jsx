import { useEffect, useMemo, useRef, useState } from "react";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  Container,
  Divider,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  Paper,
  Stack,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import StopCircleRoundedIcon from "@mui/icons-material/StopCircleRounded";
import ContentCopyRoundedIcon from "@mui/icons-material/ContentCopyRounded";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import PsychologyRoundedIcon from "@mui/icons-material/PsychologyRounded";

const API_BASES = ["http://127.0.0.1:8000", "http://localhost:8000"];
const API_BASE_KEY = "chatbot_api_base_v1";

const STORAGE_KEY = "chatbot_session_v3";

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
  } catch {}
}

function clearSavedState() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
}

function clamp01(x) {
  if (typeof x !== "number" || Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(1, x));
}

function confidenceColor(conf) {
  if (conf >= 0.75) return "success";
  if (conf >= 0.45) return "warning";
  return "error";
}

function MessageBubble({ role, message }) {
  const isUser = role === "user";

  const bubbleBg = isUser ? "primary.main" : "grey.100";
  const bubbleFg = isUser ? "primary.contrastText" : "text.primary";
  const border = isUser ? "none" : "1px solid";
  const borderColor = isUser ? "transparent" : "grey.300";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        gap: 1.25,
        px: 1,
        py: 0.5,
      }}
    >
      {!isUser && (
        <Avatar sx={{ width: 32, height: 32, bgcolor: "grey.900" }}>
          <PsychologyRoundedIcon fontSize="small" />
        </Avatar>
      )}

      <Box
        sx={{
          maxWidth: "78%",
          bgcolor: bubbleBg,
          color: bubbleFg,
          border,
          borderColor,
          borderRadius: 2.5,
          px: 1.5,
          py: 1.0,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          boxShadow: isUser ? 1 : 0,
        }}
      >
        <Typography variant="body2" sx={{ lineHeight: 1.45 }}>
          {message}
        </Typography>
      </Box>

      {isUser && (
        <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.dark" }}>U</Avatar>
      )}
    </Box>
  );
}

function normalizeBase(base) {
  return String(base || "").replace(/\/+$/, "");
}

async function apiFetch(path, init = {}) {
  const savedBase = localStorage.getItem(API_BASE_KEY);
  const bases = [
    ...(savedBase ? [savedBase] : []),
    ...API_BASES.filter((b) => b !== savedBase),
  ].map(normalizeBase);

  let lastErr = null;

  for (const base of bases) {
    try {
      const res = await fetch(`${base}${path}`, init);
      localStorage.setItem(API_BASE_KEY, base);
      return res;
    } catch (e) {
      lastErr = e;
    }
  }

  throw lastErr || new Error("All API bases failed");
}

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [confidence, setConfidence] = useState(null);
  const [retrievedIds, setRetrievedIds] = useState([]);

  const [isSending, setIsSending] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const [restoredFromStorage, setRestoredFromStorage] = useState(false);

  const listRef = useRef(null);

  const canChat = !!sessionId && !isCreatingSession;

  const conf = useMemo(() => {
    if (confidence == null) return null;
    return clamp01(confidence);
  }, [confidence]);

  useEffect(() => {
    const saved = loadSavedState();
    if (saved?.sessionId) {
      setSessionId(saved.sessionId);
      setMessages(Array.isArray(saved.messages) ? saved.messages : []);
      setConfidence(typeof saved.confidence === "number" ? saved.confidence : null);
      setRetrievedIds(Array.isArray(saved.retrievedIds) ? saved.retrievedIds : []);
      setRestoredFromStorage(true);
    } else {
      setRestoredFromStorage(false);
    }
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    saveState({ sessionId, messages, confidence, retrievedIds });
  }, [sessionId, messages, confidence, retrievedIds]);

  useEffect(() => {
    if (!sessionId) return;
    if (!restoredFromStorage) return;
    if (messages.length > 0) return;

    (async () => {
      try {
        const res = await apiFetch(`/history/${sessionId}`);
        if (!res.ok) return;
        const data = await res.json();
        const restored = Array.isArray(data)
          ? data.map((x) => ({ role: x.role, message: x.message }))
          : [];
        setMessages(restored);
      } catch {}
    })();
  }, [sessionId, restoredFromStorage, messages.length]);

  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, isSending]);

  const copySessionId = async () => {
    if (!sessionId) return;
    try {
      await navigator.clipboard.writeText(sessionId);
    } catch {}
  };

  const createSession = async () => {
    if (isCreatingSession) return;

    setIsCreatingSession(true);
    setMessages([]);
    setSessionId(null);
    setInput("");
    setConfidence(null);
    setRetrievedIds([]);
    setRestoredFromStorage(false);
    clearSavedState();

    try {
      const res = await apiFetch(`/create_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });

      if (!res.ok) throw new Error("create_session failed");
      const data = await res.json();
      setSessionId(data.session_id);
    } catch {
      setMessages([{ role: "assistant", message: "Session creation failed." }]);
    } finally {
      setIsCreatingSession(false);
    }
  };

  const stopSession = () => {
    setSessionId(null);
    setMessages([]);
    setInput("");
    setConfidence(null);
    setRetrievedIds([]);
    setRestoredFromStorage(false);
    clearSavedState();
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    if (!sessionId) return;
    if (isSending) return;

    setIsSending(true);
    setMessages((prev) => [...prev, { role: "user", message: trimmed }]);
    setInput("");

    try {
      const res = await apiFetch(`/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: trimmed }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", message: (err && err.detail) || "Server error." },
        ]);
        return;
      }

      const data = await res.json();
      setConfidence(typeof data.confidence === "number" ? data.confidence : null);
      setRetrievedIds(Array.isArray(data.retrieved_product_ids) ? data.retrieved_product_ids : []);
      setMessages((prev) => [...prev, { role: "assistant", message: data.bot_message || "" }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", message: "Network error." }]);
    } finally {
      setIsSending(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "grey.50" }}>
      <AppBar position="sticky" elevation={1} sx={{ bgcolor: "common.white", color: "text.primary" }}>
        <Toolbar sx={{ gap: 1.5 }}>
          <Inventory2RoundedIcon />
          <Typography variant="h6" sx={{ flex: 1 }}>
            Product Chatbot
          </Typography>

          {!sessionId ? (
            <Button
              startIcon={<AddRoundedIcon />}
              variant="contained"
              onClick={createSession}
              disabled={isCreatingSession}
            >
              Start
            </Button>
          ) : (
            <Button
              startIcon={<StopCircleRoundedIcon />}
              variant="outlined"
              color="error"
              onClick={stopSession}
              disabled={isSending}
            >
              Stop
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 2.5 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={2.0} alignItems="stretch">
          <Paper
            elevation={1}
            sx={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              borderRadius: 3,
              minHeight: { xs: 520, md: 640 },
            }}
          >
            <Box sx={{ px: 2, py: 1.5, bgcolor: "common.white" }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Chip
                  size="small"
                  label={sessionId ? "Session active" : "No session"}
                  color={sessionId ? "success" : "default"}
                  variant={sessionId ? "filled" : "outlined"}
                />

                {sessionId && (
                  <>
                    <Chip size="small" variant="outlined" label={`ID: ${sessionId.slice(0, 8)}…`} />
                    <Tooltip title="Copy session id">
                      <IconButton size="small" onClick={copySessionId}>
                        <ContentCopyRoundedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </>
                )}

                <Box sx={{ flex: 1 }} />

                {conf != null && (
                  <Chip
                    size="small"
                    color={confidenceColor(conf)}
                    label={`Confidence: ${(conf * 100).toFixed(0)}%`}
                  />
                )}
              </Stack>

              {conf != null && (
                <Box sx={{ mt: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={conf * 100}
                    color={confidenceColor(conf)}
                    sx={{ height: 7, borderRadius: 999 }}
                  />
                </Box>
              )}
            </Box>

            <Divider />

            <Box
              ref={listRef}
              sx={{
                flex: 1,
                overflowY: "auto",
                py: 1.0,
                bgcolor: "grey.50",
              }}
            >
              {messages.length === 0 && (
                <Box sx={{ px: 2, py: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    {sessionId ? "No messages yet." : "Start a session."}
                  </Typography>
                </Box>
              )}

              <List disablePadding>
                {messages.map((m, i) => (
                  <ListItem key={i} disableGutters sx={{ display: "block", p: 0 }}>
                    <MessageBubble role={m.role} message={m.message} />
                  </ListItem>
                ))}

                {isSending && (
                  <ListItem disableGutters sx={{ display: "block", p: 0 }}>
                    <MessageBubble role="assistant" message="Thinking…" />
                  </ListItem>
                )}
              </List>
            </Box>

            <Divider />

            <Box sx={{ p: 1.5, bgcolor: "common.white" }}>
              <Stack direction="row" spacing={1.25} alignItems="flex-end">
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder={canChat ? "Type a message…" : "Start a session to chat…"}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  disabled={!canChat || isSending}
                />
                <IconButton
                  color="primary"
                  onClick={sendMessage}
                  disabled={!canChat || isSending || !input.trim()}
                  sx={{ width: 48, height: 48, borderRadius: 2 }}
                >
                  <SendRoundedIcon />
                </IconButton>
              </Stack>

              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
                Enter: send · Shift+Enter: newline
              </Typography>
            </Box>
          </Paper>

          <Paper
            elevation={1}
            sx={{
              width: { xs: "100%", md: 300 },
              borderRadius: 3,
              overflow: "hidden",
              height: "fit-content",
            }}
          >
            <Box sx={{ px: 2, py: 1.5, bgcolor: "common.white" }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                Retrieval
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Vector search results used for the answer
              </Typography>
            </Box>

            <Divider />

            <Box sx={{ p: 2 }}>
              <Stack spacing={1.25}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Retrieved product IDs
                  </Typography>
                  <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                    {(retrievedIds || []).length ? (
                      retrievedIds.slice(0, 20).map((id) => (
                        <Chip key={id} size="small" label={`#${id}`} variant="outlined" />
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        —
                      </Typography>
                    )}
                  </Box>
                </Box>

                <Divider />

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Confidence
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 0.5 }}>
                    {conf == null ? "—" : `${(conf * 100).toFixed(0)}%`}
                  </Typography>
                  {conf != null && (
                    <LinearProgress
                      variant="determinate"
                      value={conf * 100}
                      color={confidenceColor(conf)}
                      sx={{ height: 7, borderRadius: 999 }}
                    />
                  )}
                </Box>

                <Divider />

                <Typography variant="body2" color="text.secondary">
                  UI is decoupled from response formatting. Backend controls content.
                </Typography>
              </Stack>
            </Box>
          </Paper>
        </Stack>
      </Container>
    </Box>
  );
}