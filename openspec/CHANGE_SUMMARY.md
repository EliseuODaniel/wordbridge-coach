# FillTheWord OpenSpec - Histórico de Mudanças

## 📋 Planejado: Spec4 Variedade + Progressão (2025-12-22)

**Status**: 📋 Planned → Pending Implementation
**Change Document**: `openspec/changes/2025-12-spec4-variedade-progressao-v1.md`
**Escopo**: Backend (Spec4 algorithm), Frontend (Study Session), Database (Seed), Documentation (Docker)

### Resumo

Implementação completa do algoritmo **Spec4** definido em `spec4.md`, incluindo:
1. **Variedade de frases por palavra** (algoritmo `get_sentence_for_word`)
2. **Progressão de vocabulário com janela dinâmica** (100 → 200 → 300...)
3. **Mix inteligente 25% novas / 75% revisões**
4. **Correção crítica do bug de card_id** em `/next-spec4`
5. **Seed de múltiplas frases por palavra** (3-5 frases)
6. **UI de goal edition** (word_goal_rank)
7. **Documentação Docker/WSL2** atualizada

### Atualizações OpenSpec (FASE 1)

#### DOMAINS.md
- ✅ Adicionado `sentence_id` em `ReviewEvent` (Spec4: variedade)
- ✅ Adicionado `word_goal_rank` em `User` (Spec4: goal configurável)
- ✅ Documentadas entidades Spec4: `WordSentence`, `UserFrequencyProgress`, `UserSessionStats`
- ✅ Atualizados invariants para incluir contrato Spec4

#### API.md
- ✅ Documentado endpoint `GET /api/v1/cards/next-spec4` com contrato completo
- ✅ Especificado que `card_id` é SEMPRE `Card.id` real
- ✅ Documentado `word_id` e `sentence_id` separados
- ✅ Atualizado `POST /answer` para documentar persistência de `sentence_id`
- ✅ Adicionado `word_goal_rank` em `PATCH /users/{id}`

#### SPEC.md
- ✅ Adicionada seção "Spec4: Variedade de Frases + Janela Dinâmica"
- ✅ Documentado algoritmo de variedade de frases (K=10)
- ✅ Documentado algoritmo de progressão (gating prefixal)
- ✅ Explicada coexistência Spec2 vs Spec4 (bandas vs janela)
- ✅ Tabela comparativa entre endpoints

#### CHANGE_SUMMARY.md
- ✅ Esta entrada adicionada documentando mudança planejada

### Próximos Passos (FASE 2 - Apply)

**Backend** (~8-12h):
1. Corrigir `/next-spec4` para retornar `card_id` real
2. Implementar `get_sentence_for_word` com variedade (K=10)
3. Garantir `ReviewEvent.sentence_id` sempre preenchido
4. Adicionar `word_goal_rank` em `UserUpdateRequest`
5. Criar script `seed_spec4_sentences.py` (3-5 frases/palavra)

**Frontend** (~2-3h):
6. Confirmar `StudySession` usa `/next-spec4` com `exclude_card_id`
7. `CardDisplay` suportar `memory_stage` uppercase
8. Adicionar slider de goal no modal de edição

**Docs** (~1h):
9. Atualizar `README.md` com `docker compose` (v2)
10. Adicionar notas WSL2 e correção de portas (3007:3000)

### Critérios de Aceite

- [ ] `next-spec4` retorna `card_id` existente em `Card` table
- [ ] `ReviewEvent.sentence_id` sempre preenchido após POST `/answer`
- [ ] Variedade de frases: K=10 últimas são evitadas quando há alternativas
- [ ] `PATCH /users/{id}` aceita `word_goal_rank` e ajusta progress
- [ ] Seed cria 3+ frases por palavra com Cards correspondentes
- [ ] Testes backend passam (pytest)
- [ ] Docs Docker funcionam em WSL2

---

# FillTheWord OpenSpec - Refinamento Final (Histórico)

**Data**: 2025-02-11
**Tipo**: Refinamento e Alinhamento Texto-Base
**Escopo**: Todas as seções 0-10 alinhadas aos exemplos exatos

## Resumo das Mudanças Realizadas (Histórico)

### 1. README.md - ✅ ATUALIZADO
**Removido**:
- ❌ Referências incorretas a RF-04/05/06 "removidos"
- ❌ Menções a "domínio simplificado"
- ❌ Status "Realinhado com Escopo MVP Local"

**Adicionado**:
- ✅ Status "Alinhado com Texto-Base Definitivo (seções 0-10)"
- ✅ RF-01..RF-06 presentes e completos
- ✅ Domínio completo (não simplificado)
- ✅ Workflow OpenSpec/SDD documentado
- ✅ Stack 4 serviços local/offline
- ✅ Corpora pipeline Tatoeba/ParaCrawl/OpenSubtitles

### 2. PROJECT.md - ✅ WORKFLOW OPENSPEC ADICIONADO
**Seção Nova**: Workflow OpenSpec/SDD
- ✅ Instalação CLI: `npm i -g @fission-ai/openspec`
- ✅ Estrutura padrão: PROJECT/SPEC/DOMAINS/API/ARCH/TASKS
- ✅ Ciclo de vida: Proposal → Apply → Archive
- ✅ Comandos úteis e boas práticas

### 3. DOMAINS.md - ✅ ENTIDADES CORRIGIDAS

**Word Entity** - Campos Adicionados:
- ✅ `lemma` (string) - Forma base do dicionário
- ✅ `part_of_speech` (enum) - noun, verb, adjective, etc.
- ✅ `features` (JSON) - Propriedades gramaticais específicas
- ✅ Exemplos de JSON features por tipo

**Language Entity** - Idiomas Explícitos:
- ✅ EN: "lessac-glow_tts" (female, American English)
- ✅ ES: "es_male-glow_tts" (male, Spanish neutral)
- ✅ FR: "fr_female-glow_tts" (female, French standard)
- ✅ PT: "pt_br_female-glow_tts" (female, Brazilian Portuguese)

**User Entity** - Idiomas Configurados:
- ✅ `native_language` (FK Language.code)
- ✅ `target_language` (FK Language.code)
- ✅ Combinações suportadas documentadas
- ✅ Settings expandidos

### 4. API.md - ✅ PAYLOADS EXATOS TEXTO-BASE (CORRIGIDO)

**GET /api/cards/next** - Payload Exato:
```json
{
  "card_id": "...",
  "sentence": "The ___ is on the table.",  // ✅ CAMPO ADICIONADO
  "gap": {"start": 4, "end": 8},
  "sentence_translation": "...",
  "grammar_hint": "...",
  "memory_stage": "learning",
  "audio_word_url": "/api/audio/en/word/abc123.wav",
  "audio_sentence_url": "/api/audio/en/sentence/def456.wav"
}
```

**POST /api/cards/{id}/answer** - Payload Exato:
- ✅ Request: `{ "answer": "book", "response_time_ms": 3200 }`  // ✅ CAMPO CORRIGIDO
- ✅ Response: `{ "correct": true, "correct_answer": "book", "sentence_full": "...", "quality": 5, "next_review_at": "..." }`  // ✅ FORMATO ESPECÍFICO
- ✅ SM-2 quality 0-5, easiness_factor >= 1.3

**TTS** - POST /tts Adicionado:
- ✅ Opção POST /tts conforme texto-base
- ✅ Parâmetros: text, lang, voice_type, kind: "word"|"sentence"
- ✅ Voice models específicos por idioma
- ✅ Cache structure: audio/<lang>/<type>/<slug>.wav

### 5. SPEC.md - ✅ INDICADOR VISUAL E CORPORA

**RF-01** - Memória Visual:
- ✅ Indicador 0-4 bolinhas conforme texto-base
- ✅ 0 bolinhas (cinza): new
- ✅ 1-2 bolinhas (amarelo): learning
- ✅ 3 bolinhas (azul): review
- ✅ 4 bolinhas (verde): mature

**Pipeline Corpora** - Referência Adicionada:
- ✅ Tatoeba/ParaCrawl/OpenSubtitles
- ✅ Processamento: Download → Parsing → Filtering → Gap Creation → Validation
- ✅ Referência para DOMAINS.md detalhes

## Correções Específicas da API (ÚLTIMA ATUALIZAÇÃO)

### Problemas Identificados e Corrigidos:
1. **CAMPO FALTANTE**: GET /api/cards/next não incluía campo "sentence"
   - ✅ **CORRIGIDO**: Adicionado campo "sentence" com frase completa em L2
   - ✅ **IMPACTO**: Front-end agora tem acesso ao texto completo para renderização

2. **REQUEST BODY INCORRETO**: POST /api/cards/{id}/answer usava apenas "response_time"
   - ✅ **CORRIGIDO**: Alterado para "{answer, response_time_ms}" conforme texto-base
   - ✅ **IMPACTO**: Backend receberá campo correto para medição de performance

3. **RESPONSE FORMAT INCORRETO**: POST resposta não seguia formato texto-base
   - ✅ **CORRIGIDO**: Formatado como "{correct, correct_answer, sentence_full, quality, next_review_at}"
   - ✅ **IMPACTO**: Front-end receberá dados exatos esperados pelo texto-base

4. **TTS POST ENDPOINT**: Faltava documentação do POST /tts
   - ✅ **CORRIGIDO**: Adicionado endpoint POST /tts com parâmetros completos
   - ✅ **IMPACTO**: API flexível para geração de áudio conforme especificado

## Checklist de Itens Resolvidos

### Documentação ✅
- [x] README.md atualizado sem referências incorretas
- [x] PROJECT.md com workflow OpenSpec/SDD
- [x] DOMAINS.md com entidades completas
- [x] API.md com payloads exatos E CORRIGIDOS
- [x] SPEC.md alinhado ao texto-base
- [x] CHANGE_SUMMARY.md detalhado

### Entidades ✅  
- [x] Word: lemma, part_of_speech, features (JSON)
- [x] Language: EN/ES/FR/PT com vozes específicas
- [x] User: native_language, target_language
- [x] UserCardState: SM-2 completo
- [x] ReviewEvent: quality 0-5, response_time_ms

### API ✅ (CORRIGIDO)
- [x] GET /api/cards/next: payload exato texto-base COM CAMPO "sentence"
- [x] POST /api/cards/{id}/answer: request com "answer" e "response_time_ms"
- [x] POST /api/cards/{id}/answer: response no formato "{correct, correct_answer, sentence_full, quality, next_review_at}"
- [x] POST /tts: opção para geração de áudio conforme texto-base
- [x] Cache áudio: estrutura correta

### Features ✅
- [x] RF-01: indicador visual 0-4 bolinhas
- [x] RF-02: validação tolerante mantida
- [x] RF-03: TTS local com cache
- [x] RF-04: sessões estudo
- [x] RF-05: estatísticas básicas  
- [x] RF-06: configuração revisão

### Pipeline ✅
- [x] Tatoeba/ParaCrawl/OpenSubtitles referenciados
- [x] Processamento documentado
- [x] Seed data inicial descrito

## Estatísticas das Mudanças

### Linhas Alteradas:
- **README.md**: ~90 linhas atualizadas
- **PROJECT.md**: +50 linhas (workflow OpenSpec)
- **DOMAINS.md**: ~80 linhas modificadas (entidades)
- **API.md**: ~120 linhas modificadas (payloads exatos + CORREÇÕES)
- **SPEC.md**: ~40 linhas atualizadas (RF-01 + corpora)
- **CHANGE_SUMMARY.md**: ~80 linhas (novo conteúdo + atualizações)

### Total: ~460 linhas modificadas/adicionadas

## Validação Final

✅ **Texto-Base 100% Alinhado**: Todas as seções 0-10  
✅ **Payloads Exatos**: API com exemplos precisos E CORRIGIDOS  
✅ **Campo "sentence"**: Adicionado ao GET /api/cards/next  
✅ **Request "response_time_ms"**: Corrigido no POST /api/cards/{id}/answer  
✅ **Response Format**: Ajustado ao formato texto-base  
✅ **POST /tts**: Documentado conforme especificação  
✅ **Entidades Completas**: Todos os campos do texto-base  
✅ **Workflow OpenSpec**: Install/Init/Apply/Archive  
✅ **4 Serviços**: api, frontend, tts, db containers  
✅ **Local/Offline**: Funcionamento sem internet  
✅ **SM-2 Completo**: quality 0-5, easiness_factor >= 1.3  
✅ **Cache Áudio**: audio/<lang>/<type>/<slug>.wav  
✅ **Corpora Pipeline**: Tatoeba/ParaCrawl/OpenSubtitles  

## Próximos Passos

1. **Review Final**: Validar todas as mudanças com time técnico
2. **Versionamento**: Considerar versão "v1.0-alinhada-corrigida" 
3. **Implementação**: Seguir tasks alinhadas em tasks/
4. **Testing**: Validar funcionamento offline e SM-2 com payloads corrigidos

A documentação OpenSpec está agora 100% alinhada ao texto-base original (seções 0-10) com todos os exemplos, entidades e payloads exatos, INCLUINDO as correções específicas de API para garantir compatibilidade total.
