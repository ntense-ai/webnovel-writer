# Long-Term Memory Papers and Projects: Research Report

## Purpose

This report surveys representative papers, benchmarks, and open-source projects in LLM long-term memory, addressing four questions:

- What problem does long-term memory solve?
- What have been the main technical approaches over the past two years?
- Which projects have strong engineering implementations?
- Which capabilities are most useful for `webnovel-writer`?

Notes:

- Primary sources are original papers, arXiv pages, and official repositories.
- This is an engineering survey for architecture decisions, not an exhaustive literature review.
- The latest material included in the original search was available through March 2026.

## In One Sentence

Three clear approaches have emerged:

1. **External memory + retrieval**: Store historical information externally and retrieve it on demand.
2. **Hierarchical memory + orchestration**: Manage recent context, historical evidence, and long-term summaries in separate layers.
3. **Graph / temporal memory**: Use knowledge or temporal graphs for fact updates, changing relationships, and temporal reasoning.

For this project, the most immediately useful capabilities are not larger context windows but:

- An independent long-term summary layer
- A unified memory-orchestration layer
- State management designed for fact updates

## Why Long-Term Memory Remains a Separate Problem

Representative benchmarks consistently show that:

- Larger context windows alone do not reliably solve long-term memory.
- Models still degrade across sessions, time points, fact updates, and cross-chapter integration.
- Memory involves not just storage but writing, compression, retrieval, updates, and conflict resolution.

These findings recur in:

- `LoCoMo`
- `LongMemEval`
- `BEAM`

## Benchmarks

### 1. LoCoMo

Paper:

- `Evaluating Very Long-Term Conversational Memory of LLM Agents`
- arXiv:2402.17753
- Link: <https://arxiv.org/abs/2402.17753>

Key points:

- Focuses on very long-term conversational memory
- Around `300 turns` per conversation on average
- Around `9K tokens` on average
- Up to `35 sessions`
- Evaluates question answering, event summarization, and multimodal dialogue generation

Value:

- A common comparison benchmark for subsequent memory systems
- Emphasizes multisession continuity rather than single-document retrieval

Source: LoCoMo abstract page <https://arxiv.org/abs/2402.17753>

### 2. LongMemEval

Paper:

- `LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory`
- arXiv:2410.10813
- Link: <https://arxiv.org/abs/2410.10813>

Key points:

- Distinguishes five memory capabilities:
  - Information extraction
  - Multisession reasoning
  - Temporal reasoning
  - Knowledge updates
  - Abstention
- Contains `500` carefully constructed questions
- Reports around a `30%` accuracy decline for commercial assistants and long-context models in sustained interaction

Value:

- Closer to real assistant usage than recall alone
- Particularly useful for measuring fact updates and cross-session reasoning

Source: LongMemEval abstract page <https://arxiv.org/abs/2410.10813>

### 3. BEAM

Paper:

- `Beyond a Million Tokens: Benchmarking and Enhancing Long-Term Memory in LLMs`
- arXiv:2510.27246
- Link: <https://arxiv.org/abs/2510.27246>

Key points:

- Generates coherent conversations up to `10M tokens`
- Includes `100` conversations and `2000` validation questions
- Also introduces the `LIGHT` memory framework
- Reports average LIGHT improvements of `3.5% - 12.69%` over strong baselines

Value:

- Makes the distinction between very long context and long-term memory clearer
- Particularly relevant to long-form writing systems

Source: BEAM/LIGHT abstract page <https://arxiv.org/abs/2510.27246>

## Representative Papers

### A. Early External-Memory Approaches

#### MemoryBank

- Paper: `MemoryBank: Enhancing Large Language Models with Long-Term Memory`
- arXiv:2305.10250
- Link: <https://arxiv.org/abs/2305.10250>

Core ideas:

- Convert conversation history into external memory
- Retrieve relevant memories when answering
- Introduce an update mechanism resembling a forgetting curve
- Emphasize user profiles and long-term companionship

Significance:

- Early recognition that memory requires updating and forgetting, not mere archiving
- Suitable for personalized, persona-driven, and companion applications

Limitations:

- Oriented toward conversational companionship
- Relatively early engineering structure with less refined abstractions

#### LongMem

- Paper: `Augmenting Language Models with Long-Term Memory`
- arXiv:2306.07174
- Link: <https://arxiv.org/abs/2306.07174>

Core ideas:

- Freeze the backbone LLM as a memory encoder
- Add a retriever/reader side-network
- Cache long-term context as external memory

Significance:

- Represents model-architecture-level long-term memory
- Explicit memory modules, not merely prompt engineering

Limitations:

- Less reusable than external-storage approaches for a plugin-based engineering system like this project

### B. Hierarchical Memory and Virtual Context

#### MemGPT

- Paper: `MemGPT: Towards LLMs as Operating Systems`
- arXiv:2310.08560
- Link: <https://arxiv.org/abs/2310.08560>

Core ideas:

- Treat the LLM as the application layer
- Use OS-like virtual-memory management to move memory tiers between context and external storage
- Manage history beyond the context window with memory tiers and control flow

Significance:

- A key example of hierarchical memory orchestration
- Emphasizes paging, tiered storage, and self-management

Limitations:

- Oriented toward agent runtimes
- Direct adoption would be costly for a novel-writing system

#### LIGHT

- Paper: `Beyond a Million Tokens: Benchmarking and Enhancing Long-Term Memory in LLMs`
- arXiv:2510.27246
- Link: <https://arxiv.org/abs/2510.27246>

Core ideas:

- Three explicit layers:
  - `episodic memory`
  - `working memory`
  - `scratchpad`
- A unified orchestrator combines them

Significance:

- Closest to this project's current refactoring direction
- Well suited to long-term writing context

Limitations:

- Relatively recent research
- More an engineering prototype than a ready-made platform

### C. Production-Oriented Memory Layers

#### Mem0

- Paper: `Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory`
- arXiv:2504.19413
- Link: <https://arxiv.org/abs/2504.19413>
- Official repository: <https://github.com/mem0ai/mem0>

Core ideas:

- Dynamically extract salient conversational information
- Consolidate memories
- Retrieve refined memory rather than full history
- Include a graph-based variant

Official claims:

- `+26%` improvement over OpenAI Memory on LoCoMo
- Lower latency and token cost than full-context approaches

Engineering value:

- Strong focus on production metrics: latency, tokens, SDK integration
- Representative of memory-layer productization

Limitations:

- Better suited to general agents/assistants
- Structured novel-plot state still requires customization

Sources:

- Paper abstract: <https://arxiv.org/abs/2504.19413>
- Official README: <https://github.com/mem0ai/mem0>

#### Zep

- Paper: `Zep: A Temporal Knowledge Graph Architecture for Agent Memory`
- arXiv:2501.13956
- Link: <https://arxiv.org/abs/2501.13956>

Core ideas:

- Use `Graphiti` as a temporal knowledge-graph engine
- Combine conversations and business data in a graph that tracks history
- Emphasize dynamic knowledge integration, historical relationships, and low-latency retrieval

Reported results:

- Outperforms MemGPT on DMR
- Up to `18.5%` improvement on LongMemEval
- `90%` lower latency than the baseline

Engineering value:

- Well suited to changing facts, relationships, and semantically important time
- Relevant to character relationships, faction changes, and setting revisions in fiction

Source: Zep abstract page <https://arxiv.org/abs/2501.13956>

#### MIRIX

- Paper: `MIRIX: Multi-Agent Memory System for LLM-Based Agents`
- arXiv:2507.07957
- Link: <https://arxiv.org/abs/2507.07957>

Core ideas:

- Six memory types:
  - Core
  - Episodic
  - Semantic
  - Procedural
  - Resource Memory
  - Knowledge Vault
- Multiple agents coordinate updates and retrieval
- Extends to multimodal memory

Significance:

- Shows increasingly specialized memory responsibilities
- Demonstrates that future memory systems need not stop at three layers

Limitations:

- More complex architecture
- Useful as a reference, but unsuitable for direct first-stage adoption here

Source: MIRIX abstract page <https://arxiv.org/abs/2507.07957>

## Representative Open-Source Projects

### 1. Letta

- Repository: <https://github.com/letta-ai/letta>
- The original MemGPT project has become part of Letta

Official positioning:

- `stateful agents`
- Persistent agents that learn and improve across sessions

Notable aspects:

- Long-lived agents
- Memory blocks
- Persistent agent runtime

Lessons for this project:

- Useful reference for long-lived creative agents
- A full agent platform, not a natural direct fit for the current plugin architecture

Sources:

- Repository README: <https://github.com/letta-ai/letta>
- Official explanation: <https://www.letta.com/blog/memgpt-and-letta>

### 2. Mem0

- Repository: <https://github.com/mem0ai/mem0>

Official positioning:

- `Universal memory layer for AI Agents`

Notable aspects:

- Mature SDK approach
- Self-hosted and managed options
- Emphasis on multiple memory layers, user preferences, sessions, and agent state

Lessons:

- Strong engineering reference for an independent memory layer
- Especially useful for API design, integration, and memory extraction

Source: Official README <https://github.com/mem0ai/mem0>

### 3. Graphiti

- Repository: <https://github.com/getzep/graphiti>

Official positioning:

- `Build Real-Time Knowledge Graphs for AI Agents`

Characteristics:

- Temporal knowledge graph
- Entities, factual relationships, raw episodes, and ontology
- Agent memory in dynamic environments

Lessons:

- Well suited to character relationships, faction structures, and event timelines
- Graphiti/Zep is a leading category to study for a future plot knowledge graph

Source: Official README <https://github.com/getzep/graphiti>

## Research Trends

### Trend 1: From Long Context to Memory Systems

The clearest conclusions over the past two years:

- Long context is not long-term memory
- Effective approaches use external memory, structured extraction, and hierarchical orchestration

### Trend 2: From Retrieving Snippets to Writing and Updating Memory

Early emphasis:

- How to retrieve history

Recent emphasis:

- What to write into memory
- When to merge it
- When to mark it outdated
- How to resolve conflicts

### Trend 3: From Flat Vector Stores to Graph and Temporal Structures

Beyond vector retrieval, more systems emphasize:

- entity / relation
- temporal validity
- provenance
- update / invalidation

These are crucial whenever facts change.

### Trend 4: Production Cost and Latency

Projects such as Mem0 and Zep discuss not only accuracy but also:

- p95 latency
- Token cost
- Developer integration cost
- Hosting and observability

## Most Useful Conclusions for This Project

### Adopt Capabilities, Not Just a Particular Project

#### 1. LIGHT's Layering

The best-fitting abstractions remain:

- `working memory`
- `episodic memory`
- `scratchpad`

Reasons:

- The project already has working/episodic foundations
- The main missing piece at the time of this research is the scratchpad

#### 2. Zep/Graphiti's Temporal Facts

A novel system must account for:

- Changing character states
- Evolving relationships
- Revised settings

Vector retrieval alone is insufficient; facts need state and temporal semantics.

#### 3. Mem0's Engineering Approach

Useful lessons:

- Independent memory layer
- Clear SDK/interfaces
- Production attention to latency and token cost

These help turn long-term memory into an independent module.

## Mapping to `webnovel-writer`

### Directly Applicable

- LIGHT: Three-layer memory structure
- Mem0: Independent memory-layer design
- Zep/Graphiti: Relationship and timeline modeling

### Not Recommended for Direct Adoption Yet

- Letta: Full stateful-agent platform, too large
- MIRIX: Too many categories for a lightweight first stage
- LongMem: Model-architecture changes do not fit the current plugin engineering model

## Recommended Priority

Ranked by expected project benefit versus implementation cost:

1. `LIGHT`
2. `Mem0`
3. `Zep / Graphiti`
4. `MemGPT / Letta`
5. `MIRIX`
6. `MemoryBank`
7. `LongMem`

## Conclusion

The direction is clear:

- Context windows are infrastructure, not the final answer
- Effective memory combines layering, continuous writes, intelligent retrieval, and conflict management

The practical path is not to build a general agent platform, but to:

- Retain `state.json / index.db / vectors.db`
- Add a `scratchpad` long-term summary layer
- Add a unified `memory orchestrator`

This aligns with recent research and the existing system foundation.

## References

- MemoryBank: <https://arxiv.org/abs/2305.10250>
- LongMem: <https://arxiv.org/abs/2306.07174>
- MemGPT: <https://arxiv.org/abs/2310.08560>
- LoCoMo: <https://arxiv.org/abs/2402.17753>
- LongMemEval: <https://arxiv.org/abs/2410.10813>
- Zep: <https://arxiv.org/abs/2501.13956>
- Mem0 paper: <https://arxiv.org/abs/2504.19413>
- Mem0 repository: <https://github.com/mem0ai/mem0>
- MIRIX: <https://arxiv.org/abs/2507.07957>
- Graphiti repository: <https://github.com/getzep/graphiti>
- Letta repository: <https://github.com/letta-ai/letta>
- Letta / MemGPT transition: <https://www.letta.com/blog/memgpt-and-letta>
- LIGHT / BEAM: <https://arxiv.org/abs/2510.27246>
