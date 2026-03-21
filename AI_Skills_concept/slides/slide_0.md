# LLM vs. Agentic AI

```mermaid
graph LR
    subgraph LLM ["💬 LLM (Claude etc.)"]
        direction LR
        U1["You"] -->|"message"| L["Model"] -->|"message"| U1
    end
```

- Text in, text out — that's it
- Cannot take actions in the real world
- Cannot read your files, run commands, or call APIs

```mermaid
sequenceDiagram
    participant You
    participant CLI as Client (Kiro CLI)
    participant M as Model (same LLM)

    CLI->>M: message + tools: [fs_read, bash, ...]
    Note right of M: Model sees tools are available

    alt Response type = "text"
        M->>CLI: 💬 text response
        CLI->>You: display message
    else Response type = "tool_use"
        M->>CLI: 🔧 tool call request (structured JSON)
        CLI->>CLI: execute tool locally
        CLI->>M: tool result
        M->>CLI: 💬 text response (using result)
        CLI->>You: display message
    end
```

- Same model, but the client declares available tools in the API request
- Model responds with either **text** or a **tool call request** — the client decides what to do
- No tools declared = text only (basic LLM). Tools declared = agentic.

**Key difference**: LLM = can only talk. Agentic = can talk AND act.
