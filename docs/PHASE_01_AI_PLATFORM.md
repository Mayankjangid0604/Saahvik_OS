# Phase 01 — AI Platform

## Objective

Transform EnterpriseOS from a standalone executive architecture into an AI-powered executive system.

The CEO must remain completely independent of any specific model provider.

No domain layer may depend on Ollama, OpenAI, Anthropic, Gemini, or any concrete implementation.

The AI Platform becomes infrastructure.

---

# Philosophy

The CEO never talks to models.

The CEO requests capabilities.

The AI Platform decides:

- which provider
- which model
- retries
- fallbacks
- health
- routing

The CEO should never know what model generated an answer.

---

# Current Providers

Implement:

✓ Ollama Provider

Future providers must be supported without modifying the CEO.

Examples:

- OpenAI
- Anthropic
- Gemini
- Azure OpenAI
- OpenRouter
- LM Studio
- vLLM
- Local HTTP providers

---

# Current Local Models

Support every installed model.

Detected:

- deepseek-r1
- llama3.1
- phi4
- qwen2.5
- qwen2.5-coder
- gemma2
- nomic-embed-text

The system must discover available models dynamically.

Never hardcode installed models.

---

# Architecture

src/

providers/

    ai/

        provider.py
        registry.py
        router.py
        ollama_provider.py
        ollama_client.py
        discovery.py

        request.py
        response.py

        capability.py
        model.py

        exceptions.py

        health.py

        config.py

        cache.py

        metrics.py

        conversation.py

---

# AI Provider Interface

Create AIProvider.

Supports:

- chat()
- generate()
- analyse()
- summarise()
- embed()
- health()

Every provider implements this interface.

---

# AI Request

Create AIRequest.

Contains:

- prompt
- system_prompt
- messages
- capability
- temperature
- max_tokens
- top_p
- stop
- json_mode
- attachments
- metadata

Immutable.

---

# AI Response

Create AIResponse.

Contains:

- text
- provider
- model
- capability
- finish_reason
- duration
- prompt_tokens
- completion_tokens
- total_tokens
- metadata

Immutable.

---

# Capability Model

Create Capability enum.

Examples:

GENERAL_CHAT

REASONING

DEEP_REASONING

CODING

DEBUGGING

PLANNING

ARCHITECTURE

RESEARCH

SUMMARISATION

EXTRACTION

CLASSIFICATION

EMBEDDING

TOOL_SELECTION

---

# Model Metadata

Create AIModel.

Contains:

- name
- provider
- context_window
- supports_tools
- supports_json
- supports_embeddings
- supports_vision
- supports_streaming
- capabilities
- health

---

# Model Discovery

Automatically discover models from Ollama.

Never hardcode.

Must detect:

- installed models
- removed models
- unavailable models

---

# Registry

Create ModelRegistry.

Responsible for:

- model discovery
- provider registration
- lookup
- availability
- capabilities

---

# AI Router

Create AIRouter.

The router selects the best model.

Selection considers:

- requested capability
- health
- availability
- model features
- user preferences
- fallback rules

Never hardcode routing.

Routing must be configurable.

---

# Ollama Client

Implement HTTP client.

Supports:

- chat
- generate
- embeddings
- model list
- health

No CEO logic.

---

# Ollama Provider

Implement AIProvider.

Uses OllamaClient.

Converts:

AIRequest

↓

Ollama

↓

AIResponse

---

# Conversation

Create Conversation.

Supports:

- system messages
- user messages
- assistant messages

Context management only.

No memory.

---

# Cache

Optional response cache.

Cache key:

provider

model

prompt hash

parameters

TTL configurable.

---

# Metrics

Collect:

- latency
- failures
- retries
- token usage
- model usage

Provider independent.

---

# Health

Health monitor.

Tracks:

- provider online
- model availability
- failures
- degraded state

---

# Configuration

Support configuration:

preferred_models

fallback_models

routing rules

timeouts

retry policy

cache policy

streaming

JSON mode

temperature defaults

No hardcoded values.

---

# Logging

Create:

logs/ai.log

Every request logs:

provider

model

capability

duration

status

No prompt logging unless enabled.

---

# CEO Integration

Modify the CEO only through interfaces.

CEO requests:

Capability.REASONING

Capability.CODING

Capability.PLANNING

Capability.RESEARCH

The router selects the provider.

The CEO never imports Ollama.

---

# Safety

Never execute prompts.

Never execute code.

Never execute shell commands.

Never expose secrets.

Never bypass approval rules.

No autonomous behaviour.

---

# Tests

Test:

✓ Model discovery

✓ Registry

✓ Router

✓ Capability routing

✓ Ollama provider

✓ Client

✓ Health

✓ Metrics

✓ Cache

✓ Logging

✓ CEO integration

✓ Provider abstraction

✓ Configuration

Mock Ollama.

No internet dependency.

---

# Acceptance Criteria

Complete only when:

✓ CEO can request AI capabilities

✓ Router automatically selects models

✓ All local Ollama models discovered

✓ Provider abstraction complete

✓ Registry works

✓ Health monitoring works

✓ Metrics collected

✓ Configuration works

✓ Logging works

✓ Tests pass

✓ CEO never depends on Ollama

✓ Future providers require only new provider implementations

✓ Clean Architecture preserved