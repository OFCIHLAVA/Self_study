# Anatomy of a Skill

```mermaid
graph TD
    subgraph Skill ["📁 my-skill-name/"]
        SM["📄 SKILL.md<br/><i>(required)</i>"]
        SC["📁 scripts/<br/><i>(optional)</i>"]
        RF["📁 references/<br/><i>(optional)</i>"]
        AS["📁 assets/<br/><i>(optional)</i>"]
    end

    SM --> L1["⚡ Level 1: YAML frontmatter<br/><b>Always loaded</b><br/>name + description + triggers<br/>~50 tokens"]
    SM --> L2["📖 Level 2: Markdown body<br/><b>Loaded when skill is relevant</b><br/>step-by-step instructions<br/>~1,000–3,000 tokens"]
    SC --> L3["🔧 Level 3: Loaded on demand"]
    RF --> L3
    AS --> L3
    L3 --> L3D["Scripts, docs, templates<br/><b>Only when actively needed</b><br/>varies"]
```

## SKILL.md Structure

```yaml
---
name: my-skill-name          # kebab-case, must match folder name
description: >
  What it does. Use when user asks
  to "do X" or mentions "Y".     # WHAT + WHEN (trigger phrases)
---

# My Skill Name

## Step 1: ...
(detailed instructions in Markdown)
```

## Sharing a Skill

```mermaid
graph LR
    F["📁 my-skill-name/"] -->|"drop into"| L1["~/.kiro/skills/<br/><i>available in all projects</i>"]
    F -->|"or"| L2[".kiro/skills/<br/><i>available in this project only</i>"]
    F -->|"or"| L3["Zip & upload to Claude.ai<br/><i>Settings > Skills</i>"]
```

- A skill is just a folder — share it via Git, zip, copy/paste
- Team-wide: drop into a shared repo, everyone clones to `~/.kiro/skills/`
