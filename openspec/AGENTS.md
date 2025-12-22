# FillTheWord Development Workflow

## Agent Roles

This document defines the roles and workflows for AI agents working on the FillTheWord project.

### Codex (Orchestrator)
**Primary Decision Maker and Project Coordinator**

**Responsibilities:**
- Overall project architecture decisions
- Feature prioritization and scope definition
- Technical direction and stack choices
- Code review and quality assurance
- Integration planning and testing strategy
- Release management and deployment decisions

**When to engage:**
- Major architectural changes
- New feature planning and scoping
- Integration between services
- Performance and scaling decisions
- Code review and final approvals
- Production deployment decisions

### Claude (Developer Principal)
**Primary Implementation Specialist**

**Responsibilities:**
- Core feature implementation
- Code writing and debugging
- Database schema and migrations
- API endpoint development
- Frontend component development
- Testing and validation
- Documentation updates

**When to engage:**
- Feature implementation (post-spec)
- Bug fixes and troubleshooting
- Database changes and migrations
- API development and testing
- Frontend component updates
- Performance optimizations
- Code refactoring

## Development Workflow

### Phase 1: Proposal (Codex Led)
**Objective**: Define what to build and why

**Process:**
1. **Requirements Analysis**
   - Review user requirements and business needs
   - Define scope and constraints
   - Identify technical dependencies
   - Estimate complexity and risk

2. **Specification Creation**
   - Create/update OpenSpec documents
   - Define API contracts and data models
   - Document success criteria and validation
   - Plan integration points

3. **Architecture Planning**
   - Design system interactions
   - Choose technologies and approaches
   - Plan database schema changes
   - Define testing strategy

**Deliverables:**
- OpenSpec SPEC.md updates
- OpenSpec API.md updates
- Change request document (openspec/changes/)
- Technical design document (if complex)

### Phase 2: Apply (Claude Led)
**Objective**: Build the feature according to specification

**Process:**
1. **Implementation**
   - Write code following the specification
   - Create database migrations if needed
   - Implement API endpoints and frontend components
   - Add tests and documentation

2. **Integration**
   - Integrate with existing systems
   - Update API routing and documentation
   - Ensure backward compatibility
   - Test cross-service interactions

3. **Validation**
   - Manual testing of core functionality
   - Automated test execution
   - Performance validation
   - Error handling verification

**Deliverables:**
- Working code implementation
- Database migrations (if applicable)
- Updated documentation
- Test results and validation evidence

### Phase 3: Archive (Codex Led)
**Objective**: Finalize and document the change

**Process:**
1. **Review**
   - Code review against specification
   - Integration testing validation
   - Performance assessment
   - Security and compliance check

2. **Documentation**
   - Update OpenSpec with implementation details
   - Mark change document as completed
   - Update API documentation
   - Create runbooks and guides

3. **Deployment**
   - Plan deployment strategy
   - Execute deployment with rollback plan
   - Monitor post-deployment performance
   - Handle any issues or rollbacks

**Deliverables:**
- Updated OpenSpec documents
- Completed change documentation
- Deployment documentation
- Monitoring and runbook updates

## File Organization

### OpenSpec Structure
```
openspec/
├── SPEC.md              # Master specification document
├── API.md               # API contract and endpoints
├── AGENTS.md            # This workflow document
└── changes/
    ├── YYYY-MM-feature-v1.md    # Change proposals
    ├── YYYY-MM-feature-v1.md    # Completed changes
    └── archived/                 # Historical changes
```

### Change Document Template
```markdown
# Change: [Feature Name]

**Date**: YYYY-MM-DD
**Status**: ✅ Applied / 📋 Planned
**Version**: v1.0

## Overview
[Brief description of what changes]

## Changes
[Detailed implementation description]

## Validation
[How to test and validate]

## Success Criteria
[What constitutes completion]
```

## Communication Protocol

### Handoff Process
1. **Codex → Claude**: "Ready for implementation" with spec reference
2. **Claude → Codex**: "Implementation complete" with test results
3. **Codex → Claude**: "Approved for deployment" or "Request changes"

### Status Updates
- **In Progress**: Active development
- **Blocked**: Waiting for dependencies or decisions
- **Ready for Review**: Implementation complete, awaiting review
- **Approved**: Changes reviewed and approved
- **Deployed**: Changes live in production

### Escalation Paths
- **Technical Issues**: Claude researches, proposes solutions to Codex
- **Architecture Decisions**: Claude proposes, Codex decides
- **Priority Conflicts**: Codex resolves based on project goals
- **Resource Issues**: Both agents coordinate on solutions

## Quality Gates

### Before Implementation (Codex)
- [ ] Specification is clear and complete
- [ ] Success criteria are defined and measurable
- [ ] Technical approach is sound and documented
- [ ] Dependencies are identified and available
- [ ] Risks are assessed and mitigated

### Before Review (Claude)
- [ ] Code follows project standards and conventions
- [ ] Tests are written and passing
- [ ] Documentation is updated and accurate
- [ ] Manual testing validates core functionality
- [ ] Performance meets defined targets

### Before Deployment (Codex)
- [ ] Code review is complete and approved
- [ ] Integration testing is successful
- [ ] Documentation is current and accurate
- [ ] Rollback plan is documented and tested
- [ ] Monitoring is configured and working

## Decision Matrix

| Decision Type | Primary Agent | Secondary Review |
|---------------|---------------|------------------|
| Architecture | Codex | Claude (consult) |
| Implementation | Claude | Codex (review) |
| API Design | Codex | Claude (feedback) |
| Database Changes | Claude | Codex (review) |
| Frontend UX | Claude | Codex (review) |
| Performance | Both | Joint decision |
| Security | Codex | Claude (consult) |
| Deployment | Codex | Claude (support) |

## Examples

### Example 1: New Feature Implementation
**Codex**: Creates change document for "User Settings API" with full specification
**Claude**: Implements endpoints, frontend components, and tests according to spec
**Codex**: Reviews implementation, validates against requirements, approves deployment

### Example 2: Bug Fix
**Claude**: Identifies bug in daily limit calculation, proposes fix approach
**Codex**: Reviews proposal, approves implementation plan
**Claude**: Implements fix, adds tests, validates functionality
**Codex**: Reviews and approves deployment

### Example 3: Performance Optimization
**Claude**: Identifies slow query in stats endpoint, proposes optimization
**Codex**: Reviews approach, considers broader implications
**Claude**: Implements optimization with fallback and monitoring
**Codex**: Reviews performance gains, approves deployment

This workflow ensures clear responsibilities, systematic development process, and high-quality deliverables while maintaining flexibility for different types of work.
