from uuid import UUID

from contract_server.domain.session import Session


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Session] = {}

    def save(self, session: Session) -> None:
        self._store[session.id] = session

    def get(self, session_id: UUID) -> Session | None:
        return self._store.get(session_id)

    def list_all(self) -> list[Session]:
        return list(self._store.values())

    def update(self, session: Session) -> None:
        self._store[session.id] = session

    def delete(self, session_id: UUID) -> None:
        self._store.pop(session_id, None)
