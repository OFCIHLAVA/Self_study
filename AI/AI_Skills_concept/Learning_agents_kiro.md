# AI Agents, Skills, MCPs & Kiro CLI — Learning Reference

Personal learning notes from hands-on exploration and conversation.

---

## 1. The Context Window — The Fundamental Constraint

Everything in an LLM conversation must fit inside a **context window** — a fixed-size working memory measured in **tokens** (roughly word-pieces; "understanding" ≈ 2-3 tokens).

What lives in the context window:
- System prompt (base instructions)
- All loaded skill instructions
- Full conversation history (every message, both directions)
- Every tool call request and its result
- Every file read, bash output, MCP response
- The model's own responses

**When the window fills up**, older content gets dropped or summarized, and response quality degrades. This is the core constraint that drives the design of skills, MCP, subagents, and everything else.

### Why It Matters
- More context = slower responses, higher cost (API pricing is per-token), worse instruction-following
- LLMs suffer from the "needle in a haystack" problem — too much competing information makes them miss important details
- Every tool call result dumps data into the window, so complex workflows accumulate fast

---

## 2. How Kiro CLI ↔ Claude Communication Works

Claude runs **remotely** on Anthropic's servers. Kiro CLI runs **locally** on your machine. Every interaction is an API call over HTTPS.

### The Basic Flow

```
1. You type a message
2. Kiro CLI sends message + full conversation history → Anthropic API (HTTPS)
3. Claude processes it remotely, generates a response
4. Response streams back → Kiro CLI displays it
```

### When Tools Are Involved (Most Interactions)

```
1. You: "Read foo.py and fix the bug"
2. Kiro CLI → API: sends your message
3. Claude → responds with a tool call (NOT text):
   { "tool": "fs_read", "parameters": {"path": "foo.py"} }
4. Kiro CLI intercepts this, executes fs_read LOCALLY on your machine
5. Kiro CLI → API: sends tool result back (file contents)
6. Claude → processes contents, responds with another tool call:
   { "tool": "fs_write", "parameters": {"path": "foo.py", "content": "..."} }
7. Kiro CLI: permission check → executes write locally
8. Kiro CLI → API: sends confirmation
9. Claude → generates final text response: "Fixed the bug in foo.py"
```

**Key insight**: A single user request can trigger multiple API round-trips. Each tool call = one extra round-trip. Complex tasks with 20 tool calls = 20+ round-trips through your internet connection.

### What Runs Where

| Remote (Anthropic servers) | Local (your machine) |
|---|---|
| All reasoning and decision-making | `fs_read` / `fs_write` (file I/O) |
| Generating tool call requests | `execute_bash` (spawns real shell) |
| Processing tool results | `grep` / `glob` (filesystem search) |
| Generating text responses | MCP server processes |
| | Permission checks (y/n prompts) |
| | Conversation history storage |

### System-Level Execution

Kiro CLI is a **compiled native binary** (ELF 64-bit, likely Rust).

- `execute_bash` → spawns a real child process: `fork()` + `exec("/bin/bash", "-c", "command")`
- `fs_read` / `fs_write` → direct OS syscalls (`open`, `read`, `write`) within the Kiro process, no subprocess
- `grep` / `glob` → in-process filesystem traversal (no subprocess)
- `web_fetch` → in-process HTTPS client

Process tree example:
```
kiro-cli (main)
  └── kiro-cli-chat (chat session)
        └── /bin/bash (spawned by execute_bash tool call)
```

### Internet Dependency

- **Required for**: every message, every response, subagent invocations
- **Not required for**: local tool execution (file I/O, bash, grep) — but the model still needs internet to *decide* to call them
- **No offline mode exists**

---

## 3. Claude Skills

A skill is a **folder of instructions** that teaches Claude how to handle specific tasks or workflows. Instead of re-explaining your preferences every conversation, you teach Claude once.

### Folder Structure

```
my-skill-name/           ← kebab-case, no spaces/capitals
├── SKILL.md             ← Required (exact casing!)
├── scripts/             ← Optional: Python, Bash, etc.
├── references/          ← Optional: docs loaded on demand
└── assets/              ← Optional: templates, icons, etc.
```

### SKILL.md Format

```yaml
---
name: my-skill-name
description: What it does. Use when user asks to "do X", "help with Y", or mentions Z.
---

# My Skill Name

## Instructions

## Step 1: ...
(detailed instructions in Markdown)
```

### Progressive Disclosure (How Skills Manage Context)

This is the key design pattern that addresses the context window problem:

| Level | What | When Loaded | Token Cost |
|-------|------|-------------|------------|
| Level 1 | YAML frontmatter (name + description) | Always in system prompt | ~50-100 tokens per skill |
| Level 2 | SKILL.md body (full instructions) | Only when Claude thinks skill is relevant | ~1,000-3,000 tokens |
| Level 3 | references/, scripts/, assets/ | Only when actively needed during execution | Varies |

**Impact**: 20 skills with progressive disclosure ≈ 4,000 tokens vs. 60,000 tokens if everything loaded upfront.

### Three Skill Categories

1. **Document & Asset Creation** — consistent output generation (reports, designs, code) using embedded style guides and templates. No external tools needed.
2. **Workflow Automation** — multi-step processes with validation gates, templates, and iterative refinement loops.
3. **MCP Enhancement** — workflow guidance layered on top of MCP tool access. Turns raw tool access into reliable, optimized workflows.

### Key Rules
- `SKILL.md` must be exactly that casing (not `skill.md`, not `SKILL.MD`)
- Folder names: kebab-case only (`my-cool-skill` ✅, `My Cool Skill` ❌)
- No `README.md` inside the skill folder
- No XML angle brackets (`< >`) in frontmatter
- Description must include WHAT it does AND WHEN to use it (trigger phrases)
- Keep SKILL.md under 5,000 words; move details to `references/`

### Installation
- Claude.ai: Settings > Capabilities > Skills > Upload (zipped folder)
- Claude Code: place in skills directory
- API: `/v1/skills` endpoint

---

## 4. MCP (Model Context Protocol)

An open standard that defines how AI assistants communicate with external tools and services. Like USB for AI tool access — build one server, works with any MCP-compatible client.

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  AI Client   │────▶│  MCP Server  │────▶│  External Service │
│  (Kiro CLI)  │◀────│  (local proc)│◀────│  (API, DB, etc.) │
└──────────────┘     └──────────────┘     └──────────────────┘
   MCP Protocol         Your code          Whatever API
   (JSON-RPC)                              the service uses
```

- **MCP Client**: Kiro CLI, Claude Desktop, Cursor, etc.
- **MCP Server**: a program that exposes tools/resources/prompts. Runs locally.
- **Transport**: stdio (stdin/stdout, used by Kiro CLI) or HTTP (SSE / Streamable HTTP)

### What an MCP Server Exposes

1. **Tools** — functions the AI can call (`create_issue`, `query_database`)
2. **Resources** — data the AI can read (schemas, docs)
3. **Prompts** — pre-built prompt templates

### How It Works in Kiro

1. Kiro CLI starts the MCP server as a child process
2. Server announces its tools (names, descriptions, parameter schemas)
3. Tool definitions get loaded into Claude's context
4. When Claude calls a tool → Kiro CLI forwards it to the MCP server via JSON-RPC over stdio
5. MCP server executes it (calls real APIs, queries DBs, etc.)
6. Result flows back: MCP server → Kiro CLI → Anthropic API → Claude

### Context Impact

The MCP server runs **outside** the context window, but all communication flows **through** it:
- Tool definitions: loaded into context (~tokens per tool)
- Each tool call request: added to context
- Each tool response: added to context (can be large — e.g., 50 projects with full metadata)

### Configuration

Global (`~/.kiro/mcp.json`) or per-project (`.kiro/mcp.json`):

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

### Building Your Own (Minimal Python Example)

```bash
pip install mcp
```

```python
# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

Available SDKs: Python (`mcp`), TypeScript (`@modelcontextprotocol/sdk`), Rust, Go, Java, C#.

### MCP vs. Skills

| MCP | Skills |
|-----|--------|
| **What** Claude can do | **How** Claude should do it |
| Provides tool access | Provides workflow knowledge |
| "Here's a hammer" | "Here's how to build a house" |
| Connects to services | Captures best practices |

They complement each other: MCP gives the ability to call `create_task`, a skill teaches the optimal workflow that uses `create_task` correctly.

---

## 5. Subagents & Orchestration

### The Context Bloat Problem

A 10-step workflow in a single conversation accumulates all tool calls, file reads, and MCP responses in one context window. It fills up fast.

### Subagents as the Solution

Subagents run in **isolated contexts**. Each one:
- Gets a fresh context window
- Has its own set of tools
- Has NO access to the parent conversation history
- Has NO access to other parallel subagents
- Returns only a compact summary to the parent

```
Main conversation (parent agent)
│
├── Subagent A (isolated context) → returns summary
├── Subagent B (isolated context) → returns summary
└── Subagent C (isolated context) → returns summary
```

**Natural garbage collection**: A subagent might internally read 10 files and make 20 tool calls (thousands of tokens), but the parent only receives the final summary (~few hundred tokens). All internal chatter is discarded.

### Invocation

```json
{
  "command": "InvokeSubagents",
  "content": {
    "subagents": [
      {
        "agent_name": "python-coder",
        "query": "Create a FastAPI health endpoint",
        "relevant_context": "Using Python 3.12, pydantic v2"
      }
    ]
  }
}
```

- `query`: the task (required)
- `agent_name`: which agent (optional, defaults to general-purpose)
- `relevant_context`: background info the agent needs (optional) — this is how you pass data between steps

### Constraints
- Max 4 parallel subagents
- Parallel subagents can't communicate with each other
- Synchronous (blocking) — parent waits for all to finish
- No memory between invocations — if you call the same agent twice, the second call has zero knowledge of the first

### `use_subagent` vs. `delegate`

| | `use_subagent` | `delegate` |
|---|---|---|
| Execution | Synchronous (blocking) | Asynchronous (non-blocking) |
| Parent waits? | Yes | No, continues immediately |
| Results | Automatic on completion | Manual status check |
| Parallel | Up to 4 | One task per agent |
| Status | Experimental (needs `chat.enableDelegate true`) | — |

### Agent Configuration

Control which agents can be used as subagents:

```json
{
  "toolsSettings": {
    "subagent": {
      "availableAgents": ["python-coder", "python-reviewer", "test-*"],
      "trustedAgents": ["python-coder"]
    }
  }
}
```

- `availableAgents`: which agents can be spawned (supports glob patterns)
- `trustedAgents`: which ones skip the y/n approval prompt

---

## 6. Context Management Strategies

Since there's no explicit "garbage collection" for the context window, here are practical approaches:

| Strategy | How It Works | Tradeoff |
|----------|-------------|----------|
| **Separate conversations** | Each task gets a fresh session. Pass only compact outputs between them. | Cleanest, but manual |
| **Subagents** | Each subtask runs in isolated context, returns compact result | Automated, but subagents have no continuity |
| **Summarize & compact** | Periodically summarize conversation, start fresh context with summary | Lossy — details get dropped |
| **API-level control** | Manually construct each request's context, strip old tool results | Full control, but requires custom code |
| **Progressive disclosure (Skills)** | Only load what's needed when it's needed | Built-in, but only applies to skill content |

Kiro CLI has a `/compact` command that summarizes the conversation to free up context space. There's also `chat.disableAutoCompaction` setting that controls automatic summarization.

---

## 7. Quick Reference

### Key File Locations (Kiro CLI)

| Path | Purpose |
|------|---------|
| `~/.kiro/agents/*.json` | Global agent configurations |
| `.kiro/agents/*.json` | Per-project agent configurations |
| `~/.kiro/mcp.json` | Global MCP server config |
| `.kiro/mcp.json` | Per-project MCP server config |
| `~/.kiro/settings/cli.json` | CLI settings |
| `.kiro/settings/lsp.json` | LSP/code intelligence config |

### Useful Commands

| Command | What It Does |
|---------|-------------|
| `/compact` | Summarize conversation to free context |
| `/context` | View context window usage |
| `/agent` | Manage agents |
| `/mcp` | See loaded MCP servers |
| `/model` | See/change current model |
| `/code init` | Initialize LSP code intelligence |
| `/plan` or `Shift+Tab` | Switch to planning agent |
| `/tools` | View available tools and permissions |
