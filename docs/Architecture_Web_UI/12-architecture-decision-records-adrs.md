# 12. Architecture Decision Records (ADRs)

## ADR-001: Next.js over Streamlit
**Decision**: Use Next.js instead of Streamlit
**Rationale**: Better performance, more control, production-ready
**Consequences**: Longer initial development, better long-term maintainability

## ADR-002: SQLite over PostgreSQL
**Decision**: Start with SQLite
**Rationale**: Simpler deployment, sufficient for single user
**Consequences**: Easy migration path to PostgreSQL if needed

## ADR-003: WebSockets for Real-time
**Decision**: WebSocket-first for updates
**Rationale**: Lower latency than polling, better UX
**Consequences**: More complex error handling, connection management

## ADR-004: Monolithic Architecture
**Decision**: Single frontend, single backend
**Rationale**: Simpler for single user, easier deployment
**Consequences**: All components scale together

---
