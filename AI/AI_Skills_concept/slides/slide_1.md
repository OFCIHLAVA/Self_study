# Why Context Size Matters

```mermaid
graph TB
    CTX["🧠 Context Window<br/><i>Fixed-size working memory per conversation</i>"]

    CTX --> COST["💰 Cost<br/>More tokens = higher API bill<br/>Every message, tool call, response counts"]
    CTX --> FOCUS["🎯 Conversation Focus<br/>Too much noise = AI loses track<br/>Instructions get buried, quality drops"]
    CTX --> MEMORY["📝 AI Memory<br/>No persistent memory between calls<br/>Entire conversation re-sent every time"]
    CTX --> TOOLS["🔧 AI Toolbox<br/>Every tool definition eats context<br/>More tools loaded = less room for actual work"]
```

- **Cost** — you pay per token, input and output. Bloated context = wasted money on every request
- **Conversation Focus** — the more stuff in context, the worse AI follows instructions ("needle in a haystack")
- **AI Memory** — there is no memory; the full conversation is re-sent with every message. It grows fast.
- **AI Toolbox** — every MCP server, every skill loaded takes space away from your actual task

```mermaid
sequenceDiagram
    participant CLI as Kiro CLI (local)
    participant M as 🧠 Model (stateless)

    Note over CLI: Turn 1
    CLI->>M: [system prompt] + [your msg 1]<br/>💰 ~100 input tokens
    M->>CLI: response 1<br/>💰 ~500 output tokens

    Note over CLI: Turn 2 — history re-sent!
    CLI->>M: [system prompt] + [your msg 1] + [response 1] + [your msg 2]<br/>💰 ~700 input tokens
    M->>CLI: response 2<br/>💰 ~400 output tokens

    Note over CLI: Turn 3 — history keeps growing!
    CLI->>M: [system prompt] + [msg 1] + [resp 1] + [msg 2] + [resp 2] + [msg 3]<br/>💰 ~1,200 input tokens
    M->>CLI: response 3<br/>💰 ~600 output tokens
```

⚠️ The model is stateless — full conversation is re-sent every turn. Input cost snowballs, output stays proportional to each response.

```
Every turn you send:
├── System prompt (fixed)
│   ├── Base instructions
│   ├── Skill frontmatters (Level 1, all skills)
│   └── MCP tool definitions (all connected servers)
│
├── Conversation history (grows!)
│   ├── Your messages
│   ├── Claude's responses
│   ├── Tool calls + results (MCP responses, file reads, etc.)
│   └── Skill Level 2/3 content (when loaded)
```
