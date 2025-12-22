# Arquivos OpenSpec Arquivados

## Data do Arquivamento: 2025-02-11

## Motivo
Estes arquivos foram arquivados porque estavam desalinhados com o escopo do projeto FillTheWord. Os arquivos continham especificações para uma arquitetura enterprise complexa (AWS, Redis, Nginx, etc.) quando o foco do projeto é um aplicativo local MVP.

## Arquivos Arquivados
- **PROJECT.md**: Continha arquitetura de microsserviços complexa
- **SPEC.md**: Requisitos RF-04 a RF-06 (sessões, estatísticas, admin)
- **DOMAINS.md**: Modelo de domínio complexo com User entities
- **API.md**: Mais de 15 endpoints incluindo autenticação e admin
- **ARCH.md**: 5 serviços incluindo Nginx, Redis, AWS ECS/RDS
- **2025-12-filltheword-mvp.md**: Timeline de 8 semanas com 5 pessoas

## Referência
Para as novas especificações alinhadas com o escopo local/MVP, consulte:
- **Change document**: `../../changes/2025-02-filltheword-base.md`
- **New specifications**: Raiz do diretório `openspec/`

## Principais Mudanças
- **Foco**: App local, offline, 4 containers apenas
- **Stack**: FastAPI + React + Coqui TTS + PostgreSQL + Docker
- **Timeline**: 2 semanas MVP vs 8 semanas enterprise
- **Team**: 3 pessoas vs 5 pessoas
- **Features**: Core learning loop vs sistema completo

## Justificativa
O arquivo foi movido em vez de deletado para manter histórico das decisões de design e facilitar comparações futuras se houver interesse em evoluir para uma versão mais complexa do projeto.
