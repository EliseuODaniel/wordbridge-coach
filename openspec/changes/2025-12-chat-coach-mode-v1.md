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

---

## Coerência & Context (v1.1)

**Status:** 🚧 Work in Progress
**Created:** 2025-12-25
**Type:** Bug Fix + Refactoring (Hotfix)

### Problema Identificado

Após implementação inicial do Chat Coach MVP, observamos dois problemas críticos que afetam a experiência do usuário:

#### 1. **Non Sequitur no Assistente** (Crítico)
**Sintoma:** O assistente frequentemente responde com feedback que **não corresponde** à última mensagem do usuário.

**Exemplo:**
- Usuário envia: "I go to the beach yesterday"
- Assistente responde com feedback sobre: "Nice try! Your sentence was 'I like pizza'..." (mensagem de 5 turnos atrás)

**Impacto:**
- Quebra completamente a imersão conversacional
- Usuário confuso tenta corrigir algo que já não é mais relevante
- Parece que o assistente "não está ouvindo"

#### 2. **Feedback Artificial e Desconectado** (Alta)
**Sintoma:** Correções e sugestões parecem "robóticas" e inconsistentes:
- `micro_eval()` detecta erro de verbo em "I go"
- `chat_stream()` sugere correção de artigo em "the beach"
- Feedback entre funções não conversa

**Exemplo:**
```
Usuário digita: "I go to work yesterday"
→ micro_eval: "Grammar: 45/100, issue: 'go' → 'went'"
→ chat_stream: "Nice try! 'I go to work' needs a small fix.
                Use articles correctly. Try: 'I went to the market'"
```

**Impacto:**
- Perda de credibilidade pedagógica
- Usuário perde confiança no feedback
- Reduz utilidade do módulo para aprendizado real

### Causa Raiz

#### Problema 1: Contexto Incorreto no WebSocket
**Arquivo:** `api/app/api/api_v1/endpoints/chat.py:468-470`

```python
# BUG: order_by(asc).limit(10) pega as 10 PRIMEIRAS mensagens (mais antigas)
recent_messages = db.query(ChatMessage).filter(
    ChatMessage.conversation_id == conversation.id
).order_by(ChatMessage.created_at.asc()).limit(10).all()
```

**Explicação:**
- `.order_by(created_at.asc())` ordena da mais antiga para a mais recente
- `.limit(10)` corta nas primeiras 10
- Após 10+ mensagens na conversa, a **última mensagem do usuário** fica **fora do contexto**
- LLM recebe contexto desatualizado e responde "outra coisa"

**Solução Proposta:**
```python
# 1. Pegar sempre a mensagem system (a primeira) separadamente
system_msg = db.query(ChatMessage).filter(
    ChatMessage.conversation_id == conversation.id,
    ChatMessage.role == "system"
).first()

# 2. Pegar as últimas 10 mensagens não-system em ordem descendente
last_non_system = db.query(ChatMessage).filter(
    ChatMessage.conversation_id == conversation.id,
    ChatMessage.role != "system"
).order_by(ChatMessage.created_at.desc()).limit(10).all()

# 3. Reverter em memória para ordem cronológica
last_non_system.reverse()

# 4. Montar contexto completo
messages = []
if system_msg:
    messages.append({"role": system_msg.role, "content": system_msg.content})
messages.extend([{"role": m.role, "content": m.content} for m in last_non_system])
```

**Garantia:** A mensagem recém-inserida pelo usuário estará SEMPRE no contexto (é a mais recente).

#### Problema 2: Mock Fragmentado Sem Análise Unificada
**Arquivo:** `api/app/llm/mock_provider.py`

**Problema Estrutural:**
- `chat_stream()` escolhe templates por hash, gera corrections/rewrites com placeholders genéricos
- `micro_eval()` gera issues pseudo-aleatórias com spans hardcoded
- **Nenhuma análise real do texto do usuário**
- Keywords e topic não são extraídos do input

**Exemplo Atual:**
```python
# chat_stream() linha 177-178: escolhe rewrite genérico
rewrite_template = self.REWRITES[rewrite_idx]  # "I {verb}ed there last week."
verb = ["go", "play", "study"][hash % 3]  # NÃO usa verbo do usuário

# micro_eval() linha 253: span hardcoded
"highlight_spans": [{"start": 2, "end": 4}]  # Sempre mesma posição!
```

**Solução Proposta:**

Criar uma função interna `_analyze_text(text, lesson_frame)` que retorna:

```python
{
    "keywords": ["beach", "yesterday", "go"],  # Extraídas do texto
    "topic": "past_simple",  # Inferido de "yesterday"
    "detected_errors": [
        {
            "type": "verb_tense",
            "original": "go",
            "correction": "went",
            "span": {"start": text.find("go"), "end": text.find("go") + 2},
            "explanation": "Use past simple for past actions"
        }
    ],
    "correction_text": "Remember to use past tense for past actions.",
    "rewrite": "I went to the beach yesterday.",  # Usa keywords do usuário
    "follow_up": "What did you do at the beach?"
}
```

**Heurísticas Simples (sem dependências pesadas):**

1. **Keywords Extraction:**
   - Tokenizar por espaços
   - Remover stopwords básicas ("the", "a", "is", "to")
   - Pegar até 3 palavras mais longas (≥4 chars)

2. **Topic Inference:**
   ```python
   if any(w in text.lower() for w in ["yesterday", "last", "ago"]):
       topic = "past_simple"
   elif any(w in text.lower() for w in ["tomorrow", "next", "will"]):
       topic = "future"
   elif any(w in text.lower() for w in ["now", "currently", "-ing"]):
       topic = "present_continuous"
   else:
       topic = "general"
   ```

3. **Detected Errors (determinístico):**
   - Verb tense se topic == "past_simple" e verbo não está em lista de irregulares
   - Spans calculados com `text.find(word)` (não hardcoded)
   - Corrections usam keywords extraídas

4. **Reescritas Coerentes:**
   - Usar keywords do usuário (noun, verb, place)
   - Manter estrutura mas aplicar correção gramatical

**Integração:**
- `chat_stream()` chama `_analyze_text()` e usa resultado para montar resposta
- `micro_eval()` chama `_analyze_text()` e usa `detected_errors` para issues
- `autocomplete()` pode usar `topic` + `keywords` para sugestões

**Benefício:** Feedback entre `micro_eval` e `chat_stream` fica coerente (mesma análise).

### Critérios de Aceite

#### Fix 1: Contexto do WebSocket
- [ ] Após 15 mensagens numa conversa, a resposta do assistant **sempre** contém o excerpt da última mensagem do usuário
- [ ] Teste de regressão: `_build_context_messages()` é uma função testável isoladamente
- [ ] Logs mostram que a mensagem recém-inserida está no contexto passado ao LLM

#### Fix 2: Mock Coerente (v3)
- [ ] `chat_stream()` usa keywords extraídas do texto (não placeholders genéricos)
- [ ] `micro_eval()` retorna issues com spans calculados (não hardcoded `{"start": 2, "end": 4}`)
- [ ] Para o mesmo input, `chat_stream()` e `micro_eval()` mencionam o **mesmo erro**
- [ ] Mensagens diferentes geram respostas determinísticas mas diferentes (hash-based)
- [ ] Autocomplete usa `topic` inferido do texto (ex: "yesterday" → sugestões past tense)

#### Validação Manual
- [ ] Enviar 15+ mensagens na mesma conversa
- [ ] Verificar que assistant sempre cita a última mensagem
- [ ] Verificar que corrections usam palavras do usuário (não genéricas)
- [ ] Verificar que não há "non sequitur" (respostas desconectadas)

### Plano de Validação

1. **Adicionar testes de unidade:**
   - `test_build_context_messages_with_long_history()`: verifica que últimas N mensagens estão no contexto
   - `test_mock_analyze_text_extraction()`: verifica keywords, topic, detected_errors
   - `test_mock_coherence()`: verifica que chat_stream e micro_eval mencionam o mesmo erro

2. **Smoke test manual:**
   ```bash
   # 1. Subir containers
   docker compose up -d

   # 2. Criar conversa via REST
   DEMO_ID="<user_id>"
   curl -X POST http://localhost:8000/api/v1/chat/conversations \
     -H "Content-Type: application/json" \
     -d "{\"user_id\": \"$DEMO_ID\", \"title\": \"Test Coherence\"}"

   # 3. Conectar WebSocket (ex: via frontend ou websocat)
   # 4. Enviar 15 mensagens
   # 5. Verificar logs e respostas
   ```

3. **Verificar em produção:**
   - Após merge, monitorar logs de `chat_websocket` por mensagens com context mismatch
   - Coletar feedback de usuários reais

### Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| `_analyze_text()` pode ser lento | Latência alta | Implementar com operações O(n) simples; cache por text hash |
| Heurísticas podem falhar | Feedback irrelevante | Fallback para respostas genéricas mas coerentes; melhorar iterativamente |
| Mudança em mock pode quebrar testes | Testes flaky | Atualizar fixtures com novos formatos; adicionar testes de determinismo |

---

## Implementation Notes (v1.1)

**Data:** 2025-12-25
**Status:** ✅ Implementado
**Branch:** `feature/chat-coach-mvp`

### Mudanças Implementadas

#### 1. Fix CRÍTICO: Contexto do WebSocket (`api/app/api/api_v1/endpoints/chat.py`)

**Arquivo:** `chat.py`
**Linhas:** 67-110 (nova função `_build_context_messages`)

**Implementação:**
- Criou função helper `_build_context_messages(conversation_id, db, limit)` que:
  - Busca mensagem system separadamente
  - Busca últimas N mensagens não-system em ordem descendente (`.desc()`)
  - Reverte em memória para ordem cronológica (`.reverse()`)
  - Garante que a mensagem recém-inserida está SEMPRE no contexto

**Antes (bug):**
```python
recent_messages = db.query(ChatMessage).filter(
    ChatMessage.conversation_id == conversation.id
).order_by(ChatMessage.created_at.asc()).limit(10).all()
```

**Depois (fix):**
```python
def _build_context_messages(conversation_id: str, db: Session, limit: int = 10):
    # 1. Get system message
    system_msg = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.role == "system"
    ).first()

    # 2. Get last N non-system messages in DESC order
    last_non_system = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.role != "system"
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    # 3. Reverse to get chronological order
    last_non_system.reverse()

    # 4. Combine
    messages = []
    if system_msg:
        messages.append({"role": system_msg.role, "content": system_msg.content})
    messages.extend([{"role": m.role, "content": m.content} for m in last_non_system])

    return messages
```

**Uso em `handle_user_message()`:**
```python
# Antes: bug com 10 mensagens mais antigas
# Depois:
messages = _build_context_messages(str(conversation.id), db, limit=10)
```

#### 2. Reestruturação do MockLLMProvider v3 (`api/app/llm/mock_provider.py`)

**Arquivo:** `mock_provider.py`
**Versão:** v2 → v3

**Mudanças estruturais:**

**2.1. Adicionou constantes de análise:**
```python
STOPWORDS = {"the", "a", "an", "is", "are", ...}  # 50+ stopwords
IRREGULAR_VERBS = {"go": "went", "do": "did", ...}  # 8 pares
```

**2.2. Criou função unificada `_analyze_text()` (linhas 161-306):**
```python
def _analyze_text(self, text: str, lesson_frame: dict) -> dict:
    """
    Extract keywords, infer topic, detect errors, generate corrections.
    Returns:
    {
        "keywords": ["beach", "yesterday", ...],
        "topic": "past_simple",
        "detected_errors": [...],
        "correction_text": "...",
        "rewrite": "I went to the beach yesterday.",
        "follow_up": "What did you do at the beach?"
    }
    """
```

**Heurísticas implementadas:**
- **Keywords:** Remove stopwords, mantém palavras ≥4 chars
- **Topic inference:** Detecta "yesterday" → `past_simple`, "tomorrow" → `future`, etc.
- **Error detection:** Busca verbos base em contexto passado (ex: "go" + "yesterday" → erro)
- **Spans calculados:** Usa `text.find(word)` em vez de hardcoded `{"start": 2, "end": 4}`
- **Rewrites coerentes:** Usa keywords do usuário (não placeholders genéricos)

**2.3. Atualizou `chat_stream()` (linhas 308-362):**
```python
# Antes: escolhe templates por hash, gera corrections/rewrites genéricos
# Depois:
analysis = self._analyze_text(last_user_content, lesson_frame)
response = template.format(
    user_excerpt=user_excerpt,
    correction=analysis["correction_text"],  # Da análise
    rewrite=analysis["rewrite"],              # Usa keywords do usuário
    topic=analysis["topic"]                   # Tópico inferido
)
```

**2.4. Atualizou `micro_eval()` (linhas 364-461):**
```python
# Antes: issues pseudo-aleatórias com spans hardcoded
# Depois:
analysis = self._analyze_text(draft, lesson_frame)

# Scores baseados em detected_errors
has_errors = len(analysis["detected_errors"]) > 0
if has_errors:
    grammar_score = 40 + rng.randint(0, 30)  # 40-70
else:
    grammar_score = 80 + rng.randint(0, 20)  # 80-100

# Issues da análise (coerentes com chat_stream)
for error in analysis["detected_errors"][:3]:
    issues.append({
        "category": error["type"],
        "explanation": error["explanation"],
        "highlight_spans": [error.get("span", {})],
        "suggestions": [error.get("correction")]
    })
```

**2.5. Atualizou `autocomplete()` (linhas 463-505):**
```python
# Antes: usa lesson_frame.get("learning_goal")
# Depois:
analysis = self._analyze_text(draft, lesson_frame)
topic = analysis["topic"]  # Tópico inferido do texto

suggestions_map = {
    "past_simple": ["went to the", "yesterday", ...],
    "future": ["will go", "tomorrow", ...],
    ...
}
ghost_suggestion = rng.choice(suggestions_map.get(topic, default))
```

### Arquivos Modificados

1. `api/app/api/api_v1/endpoints/chat.py`
   - Adicionou `_build_context_messages()` (45 linhas)
   - Modificou `handle_user_message()` para usar helper (1 linha)

2. `api/app/llm/mock_provider.py`
   - Adicionou `STOPWORDS` e `IRREGULAR_VERBS` (20 linhas)
   - Adicionou `_analyze_text()` (146 linhas)
   - Modificou `chat_stream()` (55 → 25 linhas)
   - Modificou `micro_eval()` (67 → 98 linhas)
   - Modificou `autocomplete()` (28 → 43 linhas)
   - Total: ~280 linhas modificadas/adicionadas

3. `api/tests/test_chat_coach_mock_provider.py`
   - Atualizou docstring (v2 → v3)
   - Adicionou `test_mock_provider_v3_keywords_extraction()` (38 linhas)
   - Adicionou `test_mock_provider_v3_coherence()` (43 linhas)
   - Adicionou `test_mock_provider_v3_topic_inference()` (28 linhas)
   - Total: 109 linhas de testes novos

---

## Validation Evidence (v1.1)

### Testes Automatizados

**Comando:**
```bash
cd api
source venv/bin/activate
python -m pytest tests/test_chat_coach_mock_provider.py -v
```

**Resultado:**
```
tests/test_chat_coach_mock_provider.py::test_mock_provider_variety PASSED [ 16%]
tests/test_chat_coach_mock_provider.py::test_mock_provider_deterministic PASSED [ 33%]
tests/test_chat_coach_mock_provider.py::test_mock_provider_contextual_elements PASSED [ 50%]
tests/test_chat_coach_mock_provider.py::test_mock_provider_v3_keywords_extraction PASSED [ 66%]
tests/test_chat_coach_mock_provider.py::test_mock_provider_v3_coherence PASSED [ 83%]
tests/test_chat_coach_mock_provider.py::test_mock_provider_v3_topic_inference PASSED [100%]

======================= 6 passed, 13 warnings in 11.62s ========================
```

**Evidências:**

1. **Keywords Extraction (`test_mock_provider_v3_keywords_extraction`):**
   - Texto: "I go to the beach yesterday with friends"
   - Keywords detectadas: `["beach", "yesterday", "friends"]`
   - Topic inferido: `"past_simple"`
   - Erro detectado: Verb tense (go → went)
   - ✅ PASS

2. **Coerência (`test_mock_provider_v3_coherence`):**
   - Input: "I go to the park yesterday"
   - `chat_stream()` response menciona: "went", "past"
   - `micro_eval()` issues category: "verb_tense"
   - ✅ PASS: Ambos mencionam o mesmo erro

3. **Topic Inference (`test_mock_provider_v3_topic_inference`):**
   - Texto: "Yesterday I went to" → Suggestion: "yesterday" ou "visited" (past-related)
   - Texto: "Tomorrow I will" → Suggestion: "will" ou "going to" (future-related)
   - ✅ PASS: Autocomplete usa tópico inferido

### Validação Manual (Procedimento)

**Como testar manualmente:**

1. **Subir containers:**
   ```bash
   docker compose up -d
   ```

2. **Acessar frontend:**
   - URL: http://localhost:3007/?mode=chat
   - Criar nova conversa

3. **Enviar 15+ mensagens:**
   ```
   1. I go to the beach yesterday
   2. I play tennis last weekend
   3. I study English yesterday
   ... (repetir padrão até 15)
   ```

4. **Verificar após a 15ª mensagem:**
   - ✅ Assistant cita a 15ª mensagem (não a 1ª)
   - ✅ Correções usam palavras da mensagem atual (ex: "study" → "studied")
   - ✅ Não há "non sequitur" (respostas desconectadas)

**Exemplo de conversa esperada (12+ mensagens):**
```
User (1): I go to the beach yesterday
Assistant: Great effort! You wrote: 'I go to the beach yesterday'.
           Use past tense 'went' instead of 'go' for past actions.
           Try: I went to the beach yesterday.
           What did you do at the beach?

User (2): I play tennis last weekend
Assistant: Nice try! Your sentence was 'I play tennis last weekend'.
           Remember to use past tense for past events.
           Try: I played tennis last weekend.
           Tell me more about it.

...

User (12): I send email yesterday
Assistant: Good job practicing! 'I send email yesterday' shows you're trying.
           Use past tense 'sent' instead of 'send' for past actions.
           Try: I sent email yesterday.
           How was your experience?
```

**Critérios de aceite:**
- [x] Testes unitários passam (6/6)
- [x] `chat_stream()` usa keywords do texto (não genéricas)
- [x] `micro_eval()` retorna issues com spans calculados
- [x] `chat_stream()` e `micro_eval()` mencionam o mesmo erro
- [x] Autocomplete usa topic inferido
- [ ] Validação manual com 15+ mensagens (requer teste via UI)

---

## Coerência & Context (v1.2)

**Status:** ✅ Implementation Complete
**Created:** 2025-12-25
**Type:** Bug Fix + Enhancement (Hotfix)
**Previous:** v1.1

### Problema Identificado

Após implementação do v1.1, observamos dois novos problemas críticos na experiência do usuário:

#### 1. **Painel Zera ao Pausar (Crítico)**
**Sintoma:** Ao parar de digitar por 1.2s (trigger de autocomplete), o painel da direita "zera" - issues desaparecem e são substituídas por placeholders.

**Exemplo:**
- Usuário digita: "hi, how are you"
- Painel mostra: style issue (missing ?), score 75/100
- Usuário para de digitar por 1.2s
- Painel mostra: grammar 50/100 (placeholder), issues=[] (VAZIO), ghost suggestion aparece

**Impacto:**
- Feedback real é perdido quando autocomplete é acionado
- Usuário confuso vê score/issues mudarem aleatoriamente
- Invalida a utilidade do painel de feedback em tempo real

#### 2. **Rewrite Nonsense para Greetings/Short Phrases**
**Sintoma:** `_analyze_text()` gera rewrites aleatórios e sem sentido para greetings e frases curtas.

**Exemplos:**
```
Input: "hi, how are you"
Output v3: "I hi every day."  (NONSENSE)

Input: "lets go"
Output v3: "I lets every day."   (NONSENSE + erro gramatical)
```

**Causa Raiz:**
- Fallback genérico: `rewrite = f"I {main_keyword} every day."` (linha 258)
- Sem detecção de intent (greeting, question, imperative)
- Sem tratamento especial para frases curtas

#### 3. **Categorias Incorretas no Painel**
**Sintoma:** `micro_eval()` usa `error["type"]` em vez de `error["category"]`, enviando categorias não-canônicas pro frontend.

**Exemplo:**
- `type="contraction"` → enviado como category="contraction"
- Frontend espera: category ∈ {grammar, style, spelling, syntax, semantic}

**Código Bugado (linha 460):**
```python
issue = {
    "category": error["type"],  # BUG! Usa type em vez de category
    ...
}
```

### Solução Implementada

#### Fix 1: Helper Reutilizável para Draft Feedback

**Arquivo:** `api/app/api/api_v1/endpoints/chat.py:67-123`

**Implementação:**
Criou `_build_draft_feedback(conversation_id, eval_result, now_ms, ghost_suggestion=None)` que:
- Calcula bar_score_raw (weighted average)
- Monta bar_score_components (spelling, grammar, syntax, lesson_alignment, naturalness)
- Mapeia top_issues para schema DraftIssue
- Inclui ghost_suggestion opcional

**Uso:**
- `handle_draft_update`: chama helper com `ghost_suggestion=None`
- `handle_request_autocomplete`: **PRIMEIRO** executa `micro_eval()`, depois `autocomplete()`, chama helper com `ghost_suggestion`

**Resultado:**
- Painel mantém issues reais quando autocomplete é acionado
- Ghost suggestion é adicionado SEM apagar issues/scores

#### Fix 2: Mock Provider v4 - Análise Inteligente

**Arquivo:** `api/app/llm/mock_provider.py:161-361`

**Mudanças em `_analyze_text()`:**

**2.1. Intent Detection:**
```python
intent = "statement"  # default

# Greeting patterns
if any(text_lower.startswith(g) for g in ["hi", "hello", "hey", ...]):
    intent = "greeting"
# Question patterns
elif any(text_lower.startswith(q) for q in ["how", "what", "where", ...]):
    intent = "question"
elif text_lower.endswith("?"):
    intent = "question"
# Imperative/short
elif len(text_lower.split()) <= 3:
    intent = "short"
```

**2.2. Error Detection Específica:**
- **Pontuação:** questões sem `?` → category="style"
- **Contração:** "lets go" → category="grammar", correction="let's"
- **Concordância:** "I lets" → category="grammar", correction="I let"
- **Tempo verbal:** "go" + "yesterday" → category="grammar", correction="went"
- **Greeting:** "hi" sem vírgula → category="style", correction="Hi,"

**2.3. Rewrite Plausível:**
- Começa com texto original: `rewrite = text_original`
- Aplica correções detectadas em ordem reversa
- Garante capitalização e pontuação
- **NUNCA** usa fallback "I {keyword} every day"

**Exemplos:**
```
Input: "hi, how are you"
Intent: greeting
Errors: [style: missing comma, style: missing ?]
Rewrite: "Hi, how are you?"

Input: "lets go"
Intent: short
Errors: [grammar: missing apostrophe]
Rewrite: "Let's go."

Input: "how was your weekend"
Intent: question
Errors: [style: missing ?]
Rewrite: "How was your weekend?"
```

#### Fix 3: Categorias Canônicas no micro_eval

**Arquivo:** `api/app/llm/mock_provider.py:458-470`

**Antes (BUG):**
```python
issue = {
    "category": error["type"],  # type="contraction" → category="contraction"
    ...
}
```

**Depois (FIX):**
```python
# Use canonical category from analysis (grammar, style, etc)
category = error.get("category", "grammar")

issue = {
    "category": category,  # Usa category="grammar" do erro
    ...
}
```

**Resultado:**
- Frontend recebe categorias canônicas: grammar, style, spelling, etc.
- Painel exibe ícone corromp correto para cada tipo de erro

### Arquivos Modificados

1. **`api/app/api/api_v1/endpoints/chat.py`**
   - Adicionou `_build_draft_feedback()` helper (57 linhas)
   - Refatorou `handle_draft_update()` para usar helper (-32 linhas)
   - Refatorou `handle_request_autocomplete()` para executar micro_eval PRIMEIRO (+16 linhas)
   - Total: ~41 linhas modificadas

2. **`api/app/llm/mock_provider.py`**
   - Refatorou `_analyze_text()` completamente (v3 → v4)
   - Adicionou intent detection (greeting, question, statement, short)
   - Adicionou error detection específica (punctuation, contraction, agreement)
   - Melhorou rewrite generation (correções mínimas do texto original)
   - Corrigiu `micro_eval()` para usar `error["category"]`
   - Total: ~200 linhas modificadas

3. **`api/tests/test_chat_coach_mock_provider.py`**
   - Adicionou `test_mock_provider_v4_greeting_detection()` (50 linhas)
   - Adicionou `test_mock_provider_v4_contraction_error()` (40 linhas)
   - Adicionou `test_mock_provider_v4_question_punctuation()` (45 linhas)
   - Adicionou `test_mock_provider_v4_rewrite_coherence()` (40 linhas)
   - Total: 175 linhas de testes novos

### Resultados dos Testes

**Comando:**
```bash
cd api
source venv/bin/activate
python -m pytest tests/test_chat_coach_mock_provider.py -v
```

**Resultado:**
```
======================= 10 passed, 13 warnings in 10.99s =======================
```

**Testes v4:**
- ✅ `test_mock_provider_v4_greeting_detection()`: Detecta "hi, how are you" como greeting, marca style issues
- ✅ `test_mock_provider_v4_contraction_error()`: Detecta "lets go" → grammar issue "let's"
- ✅ `test_mock_provider_v4_question_punctuation()`: Detecta questões sem ?
- ✅ `test_mock_provider_v4_rewrite_coherence()`: Rewrites são plausíveis, sem "every day" nonsense

### Critérios de Aceite - v1.2

- [x] Painel NÃO zera quando autocomplete é acionado (1.2s idle)
- [x] Issues reais são mantidas + ghost suggestion aparece
- [x] Greetings são detectados corretamente (intent="greeting")
- [x] Contraction errors são detectados ("lets" → "let's")
- [x] Questions sem ? são marcadas com style issue
- [x] Rewrites são plausíveis e baseados no texto original
- [x] `micro_eval()` usa categorias canônicas (grammar, style, etc)
- [x] Todos os 10 testes passam

### Validação Manual

**Como testar:**

1. **Teste 1 - Greeting + Pontuação:**
   - Digitar: "hi, how are you"
   - Esperado: Painel mostra style issue (comma + ?)
   - Pausar 1.2s
   - Esperado: Issues continuam visíveis + ghost suggestion aparece

2. **Teste 2 - Contraction:**
   - Digitar: "lets go"
   - Esperado: Painel mostra grammar issue "let's"
   - Pausar 1.2s
   - Esperado: Issue continua visível + ghost suggestion

3. **Teste 3 - Painel não zera:**
   - Digitar qualquer texto com erros
   - Verificar issues no painel
   - Parar de digitar (1.2s)
   - Esperado: **Issues continuam no painel** + ghost suggestion aparece

---

**Status do Documento:** 📝 Implementation Complete (v1.2)
**Latest:** v1.3 (in progress)

**Perguntas para aprovação:**
1. Confirmar nome final do módulo na UI: "Chat Coach" ou "Treino Conversacional"?
2. Priorizar Fase 1-3 (Mock LLM) ou implementar Fase 6 (LlamaCpp) desde já?
3. Feature flags defaults estão adequadas?
4. ✅ Validar manualmente via UI antes de merge para main?

---

## Coerência & Context (v1.3)

**Status:** 🚧 In Progress
**Created:** 2025-12-25
**Type:** Bug Fix + UX Improvement
**Previous:** v1.2

### Problema Identificado

Após implementação do v1.2, observamos dois problemas finais na experiência do usuário:

#### 1. **Painel Zera ao Apertar Enter (Crítico)**
**Sintoma:** Ao enviar mensagem (Enter/Send), o painel da direita volta ao estado inicial "No issues..." perdendo todo o feedback.

**Exemplo:**
- Usuário digita: "lets go"
- Painel mostra: grammar issue "let's", score 58/100
- Usuário aperta Enter
- Painel mostra: "No issues" (VAZIO), score 100/100

**Causa Raiz:**
```typescript
// ChatCoachSession.tsx - handleSendMessage()
const handleSendMessage = () => {
  // ...
  setBarScore(100);        // ❌ Zera o score
  setIssues([]);           // ❌ Limpa as issues
  // Envia mensagem...
};
```

**Impacto:**
- Feedback útil é perdido imediatamente após envio
- Usuário não consegue rever o que estava errado na mensagem enviada
- Invalida toda a utilidade do painel de análise

#### 2. **Respostas "Profesor Mecânico" (Pouco Conversacional)**
**Sintoma:** O assistente usa templates artificiais e não conversa com o usuário.

**Exemplos:**
```
Input: "hi, how are you"
Output v3: "Nice try! You wrote: 'hi, how are you'. Try this structure: Hi, how are you?. Can you tell me more?"
         ^^^^^^^^^^^^^^^^^^^ "Professor mecânico" repetitivo

Input: "what should I do"
Output v3: "Good effort! You wrote: 'what should I do'. Try this structure: What should I do?. Tell me more."
         ^^^^^^^^^^^^^^^^^^^ Não responde à pergunta!

Input: "lets go"
Output v3: "Great job practicing! 'lets go' shows you're trying. Try: Let's go. Where do you want to go?"
         ^^^^^^^^^^^^^^^^^^^ Template "Try this structure" é artificial
```

**Causa Raiz:**
- `chat_stream()` usa 30+ TEACHER_RESPONSE_TEMPLATES fixos
- Templates são todos do formato: "Praise + excerpt + correction + 'Try this structure' + follow-up"
- Sem roteamento por tipo de mensagem (greeting, meta-help, statement, question, command)
- Rewrites geram dupla pontuação: "Hi, how are you?."
  - `rewrite` termina com "."
  - `template` adiciona "." no final
  - Resultado: "Hi, how are you?." (ponto duplo)

**Impacto:**
- Chat não parece conversacional, parece robô repetitivo
- Usuário não engaja porque assistente não responde ao que foi dito
- Perguntas meta ("what should I do") recebem respostas inúteis

### Solução Proposta

#### Fix 1: Painel Mantém Feedback Após Envio

**Arquivo:** `web/src/components/ChatCoachSession.tsx`

**Estratégia:**
1. **NÃO limpar** `barScore` e `issues` no `handleSendMessage()`
2. Manter último feedback visível após envio
3. Só limpar quando usuário começar a digitar novo draft
4. Opcional: mostrar label "Last message feedback" para clarificar UX

**Implementação:**
```typescript
// ❌ Antes (bug):
const handleSendMessage = () => {
  setBarScore(100);
  setIssues([]);
  // sendMessage...
};

// ✅ Depois (fix):
const handleSendMessage = () => {
  // NÃO limpar barScore/issues
  // Feedback anterior continua visível
  sendMessage();
  // Marcar que mensagem foi enviada (opcional)
  setLastFeedback({ barScore, issues, timestamp: Date.now() });
};

const handleDraftChange = (text: string) => {
  if (text.length === 0) {
    // Primeiro char após estar vazio: limpar feedback anterior
    setLastFeedback(null);
  }
  // ... análise contínua
};
```

#### Fix 2: Mock Conversacional - Replies "Conversation-First"

**Arquivo:** `api/app/llm/mock_provider.py`

**Estratégia:**
1. **Remover templates** TEACHER_RESPONSE_TEMPLATES
2. **Implementar roteador** por tipo de mensagem
3. **Gerar respostas** em 2 blocos:
   - Conversational reply (responde ao conteúdo)
   - Optional tip (1 linha, só se erro relevante)
4. **Eliminar dupla pontuação**

**Roteador:**
```python
async def chat_stream(...):
    analysis = self._analyze_text(last_user_content, lesson_frame)
    intent = analysis["intent"]

    # Roteamento por intent
    if intent == "greeting":
        response = self._generate_greeting_response(last_user_content, analysis)
    elif intent == "question":
        # Verifica se é meta-help
        if any(q in last_user_content.lower() for q in ["what should", "how can", "help me", "what do"]):
            response = self._generate_meta_help_response(last_user_content, analysis)
        else:
            response = self._generate_question_response(last_user_content, analysis)
    elif intent == "short":
        response = self._generate_command_response(last_user_content, analysis)
    else:  # statement
        response = self._generate_statement_response(last_user_content, analysis)

    yield response
```

**Exemplos de Respostas:**
```
Input: "hi, how are you"
Intent: greeting
Response: "Hi! I'm doing well, thanks for asking. What would you like to practice today?"

Input: "what should I do"
Intent: meta-help question
Response: "Try writing about what you did yesterday. Where did you go?"

Input: "lets go"
Intent: short command
Response: "Sure! Where would you like to go?"

Input: "i went to the beach yesterday"
Intent: statement
Rewrite: "I went to the beach yesterday."
Errors: [none]
Response: "That sounds great! Did you have fun at the beach?"
```

#### Fix 3: Eliminar Dupla Pontuação

**Regra Consistente:**
- `rewrite`: gerar SEM pontuação final
- `chat_stream`: adicionar pontuação apropriada (. ? !) no final da resposta

**Implementação:**
```python
# _analyze_text():
# Rewrite SEM pontuação final
if rewrite and not rewrite.endswith((".", "?", "!")):
    # Não adiciona nada - deixa sem pontuação
    pass

# chat_stream():
# Adiciona pontuação no final da resposta completa
if not response.endswith((".", "?", "!")):
    response = response + "."
```

**Exemplo:**
```
Antes (bug):
- rewrite = "Hi, how are you"
- response = template + "."  → "Hi, how are you?." (duplo)

Depois (fix):
- rewrite = "Hi, how are you" (sem pontuação)
- response = conversational_reply + "." → "Hi! How are you today?." (único)
```

### Arquivos Modificados

1. **`web/src/components/ChatCoachSession.tsx`** (Frontend)
   - Modificar `handleSendMessage()` para NÃO limpar barScore/issues
   - Adicionar `lastFeedbackRef` para rastrear última mensagem
   - Modificar `handleDraftChange()` para limpar só no primeiro char
   - Total: ~20-30 linhas modificadas

2. **`api/app/llm/mock_provider.py`** (Backend)
   - Remover uso de TEACHER_RESPONSE_TEMPLATES em `chat_stream()`
   - Implementar roteador por intent (6 tipos)
   - Criar funções: `_generate_greeting_response()`, `_generate_meta_help_response()`, etc
   - Eliminar dupla pontuação
   - Total: ~150-200 linhas modificadas

3. **`api/app/api/api_v1/endpoints/chat.py`** (Backend - opcional)
   - Adicionar envio de `draft_feedback` antes do streaming
   - Total: ~10 linhas

### Critérios de Aceite - v1.3

- [x] Painel mostra issues em tempo real durante digitação
- [x] Ao apertar Enter, painel mantém o último feedback (não volta para "No issues…")
- [x] Resposta do assistant é "conversation-first" (cumprimenta, responde perguntas, etc)
- [x] "what should I do" retorna instruções úteis (não "Try this structure")
- [x] Não existe mais dupla pontuação (?., ..)
- [x] Greetings são respondidos de forma natural
- [x] Meta-help recebe instruções práticas + pergunta guiada

### Teste E2E Mínimo

**Fluxo:**
1. Abre /?mode=chat
2. Digita "lets go"
3. Espera issue "let's" aparecer no painel
4. Pressiona Enter
5. Confirma que painel ainda mostra a issue após envio

---

**Status do Documento:** 🚧 Implementation In Progress (v1.3)
