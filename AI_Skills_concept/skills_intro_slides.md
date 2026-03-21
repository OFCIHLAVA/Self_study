# Claude Skills — 5-Minute Team Intro

---

## Slide 1: How AI Agents Actually Work

```
You type a message
    → Sent over internet to AI model (cloud)
    → Model "thinks", decides what to do
    → Sends back: text OR a tool call
    → Tool runs LOCALLY on your machine
    → Result sent back to model
    → Model continues...
```

- The AI model is remote — it never touches your machine directly
- It can only REQUEST actions (read file, run command, call API)
- A local client (Kiro CLI, Claude Desktop, etc.) executes them

**Key point**: Every message, every tool call, every result — all goes through a shared "conversation memory."

---

## Slide 2: The Context Window Problem

The AI's working memory for a conversation = **context window**

Everything must fit inside it:

| What | Tokens consumed |
|------|----------------|
| System instructions | ~1,000 |
| Tool definitions (MCP, etc.) | ~1,000+ per server |
| Your messages | Grows over time |
| AI responses | Grows over time |
| Every file read, command output, API response | Can be huge |

⚠️ **Fixed size. When it fills up:**
- Older content gets dropped
- Quality degrades (AI loses track of instructions)
- Responses slow down, cost increases

---

## Slide 3: What Are Claude Skills?

A **skill** = a folder with instructions that teaches the AI how to handle specific tasks.

```
my-skill/
├── SKILL.md        ← Instructions (required)
├── scripts/        ← Code to run (optional)
├── references/     ← Docs loaded on demand (optional)
└── assets/         ← Templates, etc. (optional)
```

Instead of re-explaining your workflow every conversation → **teach once, benefit every time.**

Examples:
- "Generate frontend designs following our style guide"
- "Review PRs with our team's checklist"
- "Create CloudFormation templates using our conventions"

---

## Slide 4: How Skills Solve the Context Problem

**Progressive disclosure** — load only what's needed, when it's needed:

```
Level 1: Name + description          ← Always loaded (~50 tokens)
         "This skill does X, use when Y"

Level 2: Full instructions           ← Loaded only when relevant
         Step-by-step workflow

Level 3: Reference docs, scripts     ← Loaded only when actively needed
         Detailed documentation
```

**20 skills loaded naively**: ~60,000 tokens (context destroyed)

**20 skills with progressive disclosure**: ~2,000 tokens idle + ~2,000 when one activates

---

## Slide 5: Skills + MCP = The Full Picture

```
┌─────────────────────────────────────────────┐
│                                             │
│   MCP = the tools     Skills = the recipes  │
│   (what AI CAN do)    (how AI SHOULD do it) │
│                                             │
│   "Here's a hammer"   "Here's how to        │
│                        build a house"        │
│                                             │
└─────────────────────────────────────────────┘
```

- **MCP** connects AI to services (Jira, GitHub, databases, etc.)
- **Skills** encode your team's workflows and best practices on top
- Together: consistent, reliable, repeatable results

---

## Slide 6: Key Takeaways

1. **Context is finite** — everything in a conversation eats from the same budget
2. **Skills are reusable instructions** — teach the AI once, not every conversation
3. **Progressive disclosure** keeps context lean — only load what's needed
4. **MCP + Skills complement each other** — tools + knowledge = reliable workflows
5. **You can build your own** — a SKILL.md file is all you need to start

---

*Further reading: `/home/Repos-linux/aws_training/ai_learning/Learning_agents_kiro.md`*
