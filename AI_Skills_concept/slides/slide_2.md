# What Problem Do Skills Solve?

## 1. Reusability & Output Consistency

```mermaid
graph TD
    subgraph Without ["❌ Without Skills"]
        U1["Monday: You explain your workflow"] --> R1["Result A"]
        U2["Wednesday: You explain it again, slightly differently"] --> R2["Result B ≠ A"]
        U3["New teammate: Explains it their own way"] --> R3["Result C ≠ A ≠ B"]
    end

    subgraph With ["✅ With Skills"]
        S["Skill: workflow defined once"] --> R4["Result A"]
        S --> R5["Result A"]
        S --> R6["Result A"]
    end
```

- Without skills: every person, every session prompts differently → inconsistent results
- With skills: workflow defined once → same quality, same structure, every time, for everyone

## 2. Context Management

```mermaid
graph LR
    subgraph Without ["❌ Without Skills"]
        direction TB
        W1["Skill A: 3,000 tokens"] --> WC["Context Window"]
        W2["Skill B: 3,000 tokens"] --> WC
        W3["Skill C: 3,000 tokens"] --> WC
        WC --> WT["⚠️ 9,000 tokens used<br/>before you even say hello"]
    end

    subgraph With ["✅ With Skills ('Lazy load')"]
        direction TB
        S1["Skill A: ~50 tokens (name + description)"] --> SC["Context Window"]
        S2["Skill B: ~50 tokens (name + description)"] --> SC
        S3["Skill C: ~50 tokens (name + description)"] --> SC
        SC --> ST["✅ ~150 tokens idle<br/>full instructions load only when needed"]
    end
```

- Only a tiny summary is always loaded — the AI knows skills exist, but doesn't load details until needed
- 20 skills naively: ~60,000 tokens. With progressive disclosure: ~2,000 tokens.
