# AI Skills Concept — Learning & Research

Research and learning materials on Claude Skills, MCP (Model Context Protocol), and AI agent context management.

## What's Here

| File / Dir | Description |
|---|---|
| `Learning_agents_kiro.md` | Comprehensive learning reference covering Skills, MCP, context window mechanics, Kiro CLI communication flow, subagents, and context management strategies |
| `slides/` | Presentation slides (Mermaid-based) for a 5-minute team intro |
| `skills_intro_slides.md` | Original slide outline (text-based) |
| `The-Complete-Guide-to-Building-Skill-for-Claude.pdf` | Anthropic's official guide to building Skills |
| `pdf_copied.txt` | Text extracted from the PDF for reference |
| `kiro-lesson-1.txt` | Raw chat session log from the learning conversation |

## Slides Overview

| Slide | Topic |
|---|---|
| `slide_0` | LLM vs. Agentic AI — what makes an agent an agent |
| `slide_1` | Why context size matters — cost, focus, memory, toolbox |
| `slide_2` | What problem Skills solve — reusability, consistency, context management |
| `slide_3` | Anatomy of a Skill — folder structure, loading levels, sharing |
| `slide_4` | Real cost of context — token pricing, estimation, `/compact` |

Slides use Mermaid diagrams — render in VS Code (Mermaid extension), GitHub, or [mermaid.live](https://mermaid.live).

## Key Topics Covered

- **Context window** — the fixed-size working memory constraint driving all design decisions
- **Claude Skills** — reusable instruction packages with progressive disclosure (3-level loading)
- **MCP** — open protocol for connecting AI to external tools and services
- **Token economics** — how conversation cost snowballs and how to manage it
- **Subagents** — isolated context execution for complex multi-step workflows
