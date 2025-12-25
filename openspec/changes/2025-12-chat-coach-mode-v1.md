# Change Proposal: Chat Coach Mode (Módulo de Treino Conversacional)

**Status:** 📝 Proposal
**Created:** 2025-12-25
**Author:** AI Developer (Claude)
**Target Version:** v1.0.0
**Type:** New Feature (Novo Módulo Aditivo)

---

## Overview

Adicionar um **terceiro módulo de treinamento** ao FillTheWord: **Chat Coach**, um chatbot educacional em tempo real inspirado em FluentChat (spec50.md/spec51.md), que oferece feedback enquanto o usuário digita.

**Diferentemente dos modos Spec4 e Lingvist**, o Chat Coach é:
- **Conversacional:** Chat aberto estilo ChatGPT (não exercícios de fill-in-the-gap)
- **Tempo real:** Feedback a cada tecla ( barra de score 0–100 + análise gramatical)
- **Orientado por objetivos:** "Lesson Frames" definem metas pedagógicas por turno
- **Aditivo:** NÃO substitui nem altera Spec4/Lingvist (coexistem pacificamente)

---

## Goals (Objetivos)

### Primários
1. ✅ **Implementar módulo Chat Coach funcional** com WebSocket + LLM provider (Mock ou llama.cpp)
2. ✅ **Feedback em tempo real:** Score 0–100 + análise gramatical enquanto digita
3. ✅ **Ghost suggestion:** Auto-complete após inatividade (TAB para aceitar)
4. ✅ **Streaming de respostas:** Tokens do assistente chegam progressivamente
5. ✅ **Isolamento total:** Spec4 e Lingvist continuam funcionando sem mudanças

### Secundários
- 🎨 **UX polishing:** Dark mode consistente com resto do app
- 📊 **Telemetria:** Latência p95, tokens/s, uptime
- 🔌 **Pluggable LLM:** Fácil trocar Mock ↔ llama.cpp ↔ OpenAI no futuro

---

## Non-Goals (O que NÃO faremos)

1. ❌ **NÃO vamos mexer** em Spec4 ou Lingvist (cards, gaps, schedulers permanecem iguais)
2. ❌ **NÃO vamos substituir** o sistema de Spaced Repetition existente
3. ❌ **NÃO vamos implementar voz** na Fase 1 (STT/TTS fica para Fase 2)
4. ❌ **NÃO vamos exigir GPU alta:** VRAM ≤ 6GB (Phi-3 Mini Q4)
5. ❌ **NÃO vamos depender de cloud:** Funciona offline-first (LLM local ou Mock)

---

## UX Design (Interface do Usuário)

### Tela Principal do Chat Coach

```
┌─────────────────────────────────────────────────────┐
│  FillTheWord - Chat Coach                          │
│  ┌──────────────────┐  ┌──────────────────────────┐│
│  │ Spec4           │  │ Lingvist                 ││
│  │ Treino Clássico │  │ Treino Lacunas           ││
│  └──────────────────┘  │ Chat Coach ✨ NOVO       ││
│                       └──────────────────────────┘│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Chat History (scrollable)                         │
│  ┌───────────────────────────────────────────────┐ │
│  │ Assistant (12:34):                            │ │
│  │ "Hello! Let's practice past simple today.    │ │
│  │  What did you do last weekend?"               │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ You (12:35):                                  │ │
│  │ "I go to the beach..."                        │ │
│  │         ↑ GHOST SUGGESTION (gray)              │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  [ Draft Input - textarea ]                        │
│  ┌───────────────────────────────────────────────┐ │
│  │ I go to the beach...                          │ │
│  │                                               │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Score: 45/100 ████████░░░░░░░░░░░░░░░        │ │  ← ScoreBar
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Grammar:                                      │ │
│  │ ⚠️ "go" → "went" (past simple)                │ │  ← AnalysisPanel
│  │                                               │ │
│  │ Spelling: ✅ No errors                        │ │
│  │                                               │ │
│  │ Suggestions:                                  │ │
│  │ 💡 "I went to the beach last weekend."       │ │
│  └───────────────────────────────────────────────┘ │
│  [Send button] or [Press Enter]                   │
└─────────────────────────────────────────────────────┘
```

### Fluxos Principais

#### 1. Digitando (Realtime Feedback)
```
User digita: "I go..."
  ↓ (WebSocket: draft_update)
Backend analyzers: spelling ✅, grammar ⚠️, syntax ✅
  ↓ (WebSocket: draft_feedback)
Frontend: atualiza ScoreBar + AnalysisPanel
```

#### 2. Inatividade (Ghost Suggestion)
```
User para de digitar por 1.2s (idle_soft)
  ↓ (WebSocket: request_autocomplete)
Backend LLM: "went to" (1-2 palavras)
  ↓ (WebSocket: draft_feedback com ghost_suggestion)
Frontend: mostra texto cinza após cursor
User pressiona TAB → aceita sugestão
```

#### 3. Envio de Mensagem
```
User clica Send (ou Enter)
  ↓ (WebSocket: user_message)
Backend: persiste mensagem → chama LLM chat_stream
  ↓ (WebSocket: assistant_stream_token * N)
Frontend: renderiza tokens progressivamente ("That's gr..." → "That's great...")
  ↓ (WebSocket: assistant_done)
Backend: persiste resposta + atualiza lesson_frame + session_summary
```

---

## Protocolo WebSocket

### Eventos Cliente → Servidor (IN)

| Event | Payload | Quando Disparado |
|-------|---------|------------------|
| `draft_update` | `{text, cursor, ts}` | A cada tecla (throttled ~50ms no frontend) |
| `user_message` | `{content, ts}` | Ao enviar mensagem (Enter/Click) |
| `request_autocomplete` | `{draft_text, mode}` | Após idle_soft (1.2s) ou idle_hard (2.5s) |
| `ping` | `{ts}` | Heartbeat (cada 30s) |

### Eventos Servidor → Cliente (OUT)

| Event | Payload | Quando Disparado |
|-------|---------|------------------|
| `draft_feedback` | `{bar_score, issues, ghost_suggestion}` | Após processar draft_update |
| `assistant_stream_token` | `{token}` | A cada token gerado pelo LLM |
| `assistant_done` | `{full_content, lesson_frame, summary}` | Ao finalizar streaming |
| `error` | `{message, code}` | Erro de validação ou sistema |
| `pong` | `{ts}` | Resposta ao ping |
| `telemetry` | `{latency_ms, tokens_per_sec}` | Métricas periódicas |

### Throttling & Rate Limiting

**Frontend:**
- Enviar `draft_update` no máximo a cada 50ms (debounce)

**Backend:**
- Executar `micro_eval` (LLM) apenas se `now - last_micro_eval >= CHAT_MICRO_EVAL_MIN_INTERVAL_MS` (default: 100ms)
- Analyzers rápidos (spelling/grammar) rodam sempre (CPU, baratos)
- Idle tracking: bloquear `request_autocomplete` se usuário estiver ativo

---

## Data Model (PostgreSQL + Alembic)

### Novas Tabelas

#### `chat_conversations`
```sql
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT DEFAULT 'New Chat',
    student_profile_json JSONB DEFAULT '{}',
    lesson_frame_json JSONB DEFAULT '{}',
    session_summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX idx_chat_conversations_created_at ON chat_conversations(created_at DESC);
```

**Campos importantes:**
- `student_profile_json`: `{cefr_level: "A2", common_errors: ["past_simple", "articles"]}`
- `lesson_frame_json`: (ver schema abaixo)
- `session_summary`: Resumo incremental do que aconteceu na conversa

#### `chat_messages`
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
    content TEXT NOT NULL,
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at ASC);
```

**Observação:**
- `draft_update` **NÃO** é persistido (só mensagens finais)
- `metadata_json` pode armazenar: `{lesson_frame_snapshot, scores, tokens}`

#### `chat_lesson_history` (Opcional, Fase 2)
```sql
CREATE TABLE chat_lesson_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id),
    lesson_frame_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Schema JSON: Lesson Frame

```typescript
interface LessonFrame {
  cefr_target: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  learning_goal: string;        // ex: "past_simple_regular_verbs"
  expected_intent: string;       // ex: "describe_recent_activity"
  topic: string;                 // ex: "weekend plans"
  rubric: {
    grammar: string[];           // ex: ["past tense consistency"]
    vocab: string[];             // ex: ["yesterday", "last weekend"]
    style: string[];             // ex: ["short clear sentences"]
  };
  scoring_hints: {
    avoid: string[];             // ex: ["present continuous for past events"]
    encourage: string[];         // ex: ["time markers", "regular -ed"]
  };
}
```

---

## Arquitetura Backend (FastAPI)

### Componentes Principais

#### 1. **LLM Provider Pattern** (`api/app/llm/`)
```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat_stream(self, messages, system_prompt, config):
        """Yield tokens progressivamente"""

    @abstractmethod
    async def micro_eval(self, context, lesson_frame, draft):
        """Retorna scores + issues em JSON"""

    @abstractmethod
    async def autocomplete(self, context, lesson_frame, draft):
        """Retorna ghost_suggestion (1-6 palavras)"""

class MockLLMProvider(LLMProvider):
    """Implementação stub para desenvolvimento sem GPU"""

class LlamaCppProvider(LLMProvider):
    """Chama llama.cpp server via HTTP (local)"""
```

#### 2. **Analyzers** (`api/app/analyzers/`)
```python
class SpellingAnalyzer:
    def analyze(self, text): return score, issues

class GrammarAnalyzer:
    """Pode usar LanguageTool local ou heurísticas"""
    def analyze(self, text): return score, issues

class SyntaxAnalyzer:
    """Pode usar spaCy ou heurísticas simples"""
    def analyze(self, text): return score, issues

class ScoreAggregator:
    def aggregate(self, spelling, grammar, syntax, lesson_alignment, naturalness):
        """Retorna bar_score_raw (0-100) ponderado"""
```

#### 3. **WebSocket Handler** (`api/app/ws/`)
```python
@app.websocket("/api/v1/chat/ws/{conversation_id}")
async def chat websocket(websocket, conversation_id):
    async for message in websocket:
        if message.type == "draft_update":
            # 1. Run fast analyzers (sempre)
            # 2. Run micro_eval se passou min_interval_ms
            # 3. Aggregate scores
            # 4. Send draft_feedback

        elif message.type == "user_message":
            # 1. Persist message
            # 2. Stream LLM response
            # 3. Persist assistant response
            # 4. Update lesson_frame + session_summary
            # 5. Send assistant_done
```

#### 4. **REST Endpoints** (Mínimos)
```python
POST   /api/v1/chat/conversations      # Criar nova conversa
GET    /api/v1/chat/conversations      # Listar conversas do user
GET    /api/v1/chat/conversations/{id} # Detalhes da conversa
GET    /api/v1/chat/conversations/{id}/messages # Mensagens da conversa
DELETE /api/v1/chat/conversations/{id} # Apagar conversa
```

---

## Frontend (React + TypeScript)

### Novos Componentes

#### `ChatCoachSession.tsx`
Componente principal do Chat Coach (equivalente a `StudySession.tsx`).

**Responsabilidades:**
- Gerenciar estado da conversa (messages, draftText, scores)
- Conectar WebSocket (auto-reconnect)
- Renderizar `ChatHistory`, `DraftInput`, `ScoreBar`, `AnalysisPanel`

#### `ChatHistory.tsx`
Lista de mensagens em scroll (user + assistant).

#### `DraftInput.tsx`
Textarea que:
- Envia `draft_update` a cada tecla (throttled)
- Detecta idle time para solicitar autocomplete
- Envia `user_message` ao pressionar Enter
- Mostra ghost suggestion ( TAB para aceitar )

#### `ScoreBar.tsx`
Barra de progresso 0–100 com:
- EMA (exponential moving average) para suavização
- Cores dinâmicas (vermelho < 40, amarelo < 70, verde ≥ 70)
- Animações suaves

#### `AnalysisPanel.tsx`
Cards de feedback por categoria:
- Spelling (erros + sugestões)
- Grammar (regras quebradas + explicação)
- Syntax (estrutura da frase)
- Alternativas (reescritas sugeridas)

#### `WebSocketClient.tsx` (hook customizado)
Hook `useChatWebSocket` que:
- Gerencia conexão WS + reconexão automática
- Roteia mensagens por tipo (draft_feedback, assistant_stream_token, etc.)
- Fornece callbacks (`onDraftFeedback`, `onToken`, `onDone`, `onError`)

---

## Feature Flags (Environment Variables)

```bash
# LLM Provider
CHAT_LLM_PROVIDER=mock          # mock | llamacpp | openai | anthropic
CHAT_LLM_BASE_URL=http://llm:8080  # URL do llama.cpp server

# Realtime Feedback
CHAT_MICRO_EVAL_MIN_INTERVAL_MS=100  # Throttle LLM calls (10 Hz max)
CHAT_IDLE_SOFT_MS=1200               # Tempo para 1ª sugestão
CHAT_IDLE_HARD_MS=2500               # Tempo para 2ª sugestão

# UI Smoothing
CHAT_EMA_ALPHA=0.4                   # Alpha para EMA (0-1)

# Concurrency
CHAT_MAX_CONCURRENT_DRAFT_UPDATES=5  # Max updates em paralelo por user
```

---

## Security & Privacy

1. **Offline-first por padrão:**
   - Dados ficam no PostgreSQL local (Docker volume)
   - LLM roda em container local (llama.cpp)
   - NENHUM dado é enviado para cloud (a menos que usuário configure provider externo)

2. **Se provider externo for habilitado:**
   - Documentar claramente o que é enviado (mensagens + profile)
   - Oferecer opção de desabilitar
   - Log de requisições (audit trail)

3. **Autenticação:**
   - Reutilizar sistema existente (user_id já usado em Spec4/Lingvist)
   - WebSocket valida `user_id` antes de aceitar conexão

---

## Acceptance Criteria

### Backend (FastAPI)
- [ ] Endpoint WebSocket `/api/v1/chat/ws/{conversation_id}` funcional
- [ ] `MockLLMProvider` retorna scores estáveis + 1-3 issues
- [ ] `LlamaCppProvider` (opcional) chama llama.cpp via HTTP
- [ ] Analyzers (spelling/grammar/syntax) executam sem travar
- [ ] REST endpoints criam/listam conversas e mensagens
- [ ] Migração Alembic cria tabelas `chat_*` sem quebrar tabelas existentes

### Frontend (React)
- [ ] Nova opção "Chat Coach" aparece em UserSelection
- [ ] `ChatCoachSession` conecta WS e recebe `draft_feedback`
- [ ] Digitando envia `draft_update` e atualiza ScoreBar + AnalysisPanel
- [ ] Inatividade mostra ghost suggestion ( TAB aceita)
- [ ] Enviar mensagem dispara streaming de resposta do assistente
- [ ] Spec4 e Lingvist ainda funcionam (regression test)

### E2E (Playwright)
- [ ] Test smoke: abrir Chat Coach, criar conversa, digitar e receber feedback
- [ ] Test inatividade: parar de digitar, verificar ghost suggestion
- [ ] Test streaming: enviar mensagem, verificar tokens chegando
- [ ] Test regressão: Spec4 e Lingvist continuam funcionando

---

## Implementation Plan (Fases)

### Fase 1: Foundation (Backend)
1. Criar modelos SQLAlchemy (`chat_conversations`, `chat_messages`)
2. Criar migration Alembic
3. Implementar `MockLLMProvider` (com respostas fake)
4. Implementar analyzers stubs (spelling simples + grammar stub)
5. Criar WebSocket endpoint básico (draft_feedback)
6. REST endpoints (criar/listar conversas)

### Fase 2: Frontend Skeleton
1. Adicionar "Chat Coach" em UserSelection
2. `ChatCoachSession` com WebSocket client básico
3. `DraftInput` + `ScoreBar` + `AnalysisPanel` placeholders
4. Renderizar messages em chat

### Fase 3: Realtime Feedback
1. Implementar `draft_update` → `draft_feedback` no backend
2. Conectar analyzers + ScoreAggregator
3. Frontend: EMA na barra + cards de análise
4. Throttle no backend (min_interval_ms)

### Fase 4: Ghost Suggestion
1. Backend: `request_autocomplete` endpoint
2. Frontend: idle tracker + TAB para aceitar
3. Mock LLM retorna sugestões estáticas

### Fase 5: Streaming + Lesson Frames
1. Backend: `user_message` → `chat_stream`
2. Frontend: renderizar tokens progressivamente
3. Backend: gerar Lesson Frame por turno
4. Backend: atualizar session_summary

### Fase 6: LlamaCpp Integration (Opcional)
1. Subir container llama.cpp em docker-compose
2. Implementar `LlamaCppProvider`
3. Configurar prompts (teacher, micro-eval, autocomplete)
4. Testar com modelo real Phi-3 Mini

---

## Dependencies (Pacotes)

### Backend (adicionar ao `pyproject.toml`)
```toml
[tool.poetry.dependencies]
websockets = "12.0"         # WebSocket (FastAPI já inclui)
httpx = "0.25.0"            # Async HTTP client para LLM
```

### Frontend (adicionar ao `package.json`)
```json
{
  "dependencies": {
    // Nada novo além do que já existe (WebSocket API nativa)
  }
}
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM local pode ficar lento | Alta latência no feedback | Implementar throttle + timeout; fallback para Mock |
| Esquentar GPU | Crashes / OOM | Limitar threads + contexto; monitorar VRAM |
| WebSocket desconecta | Usuário perde sessão | Auto-reconnect no frontend; buffering de mensagens |
| Analyzers podem demorar | UI trava | Executar analyzers em background; timeout |
| Spec4/Lingvist quebrar | Regressão | Testes E2E antes de merge; isolamento de código |

---

## Success Metrics

### Funcional
- ✅ Chat Coach abre e conecta WS sem erros
- ✅ `draft_update` → `draft_feedback` em <200ms p95
- ✅ Ghost suggestion aparece em <1.5s após idle
- ✅ Streaming de resposta começa em <500ms

### Não-Funcional
- ✅ Backend mantém 10–15 Hz de micro_eval (sem travar)
- ✅ VRAM GPU ≤ 6GB (se usando llama.cpp)
- ✅ Zero regressões em Spec4/Lingvist

---

## Open Source References

Este módulo é fortemente inspirado em:
- **spec50.md**: FluentChat design (arquitetura, protocolo WS, analyzers)
- **spec51.md**: Documentação detalhada do FluentChat (schemas, prompts)

**Diferenças-chave:**
- FluentChat é um app standalone; Chat Coach é um **módulo dentro de FillTheWord**
- Chat Coach **reutiliza** users, auth, e infraestrutura existentes
- Chat Coach usa PostgreSQL (em vez de SQLite) para consistência com resto do app

---

## Next Steps (Após Aprovação)

1. ✅ Criar branch `feature/chat-coach-v1` (JÁ CRIADA)
2. 📝 Implementar Fase 1 (Foundation Backend)
3. 🎨 Implementar Fase 2 (Frontend Skeleton)
4. ✅ Executar testes E2E
5. 📋 Documentar em SPEC.md, API.md, DOMAINS.md
6. 🚀 Merge para main + arquivar change proposal

---

**Status do Documento:** 📝 Ready for Review

**Perguntas para aprovação:**
1. Confirmar nome final do módulo na UI: "Chat Coach" ou "Treino Conversacional"?
2. Priorizar Fase 1-3 (Mock LLM) ou implementar Fase 6 (LlamaCpp) desde já?
3. Feature flags defaults estão adequadas?
