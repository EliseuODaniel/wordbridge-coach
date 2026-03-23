# TTS AGENTS.md

Instruções específicas do serviço de TTS.

## Escopo

Aplica-se a tudo dentro de `tts/`.

## Objetivo

- manter o serviço simples, previsível e desacoplado do frontend
- preservar geração e cache de áudio sem introduzir dependências desnecessárias

## Regras de mudança

- trate o TTS como serviço de infraestrutura de produto, não como lugar de lógica pedagógica
- mudanças de contrato HTTP devem ser refletidas em docs e consumidores
- não commite modelos grandes ou caches gerados
