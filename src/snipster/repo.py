from abc import ABC, abstractmethod
from collections.abc import Sequence
from sqlmodel import Session, select
from .exceptions import SnippetNotFoundError
from .models import Snippet, Language


# Abstract layer of the following (add, list, get, delete)
# to be implemented by the concrete class of in memory and db.
class SnippetRepository(ABC):
    @abstractmethod
    def add(self, snippet: Snippet) -> None:
        pass

    @abstractmethod
    def list(self) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def get(self, snippet_id: int) -> Snippet | None:
        pass

    @abstractmethod
    def delete(self, snippet_id: int) -> None:
        pass

    @abstractmethod
    def search(self, term: str, *, language: str | None = None) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def toggle_favorite(self, snippet_id: int) -> None:
        pass


class InMemorySnippetRepo(SnippetRepository):
    def __init__(self) -> None:
        self._data: dict[int, Snippet] = {}  # empty dict

    def add(self, snippet: Snippet) -> None:
        next_id = max(self._data.keys(), default=0) + 1
        snippet.id = next_id
        self._data[next_id] = snippet

    def list(self) -> Sequence[Snippet]:
        return list(self._data.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._data.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        snippet = self._data.pop(snippet_id, None)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")

    def search(self, query: str, language : Language | None = None) -> Sequence[Snippet]:
        query = query.lower()
        results =  []
        for snippet in self._data.values():
            text =  query in snippet.title.lower() or query in snippet.code.lower()
            lang =  language is None or snippet.language == language
            if text and lang:
                results.append(snippet)
        return results

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self._data.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.favorite = not snippet.favorite


class DBSnippetRepo(SnippetRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    # session.add + commit + refresh
    def add(self, snippet: Snippet) -> None:
        self.session.add(snippet)
        self.session.commit()  # commit immediately
        self.session.refresh(snippet)

    # session.execute(select(...)).scalars().all()
    def list(self) -> Sequence[Snippet]:
        statement = select(Snippet)
        return self.session.exec(statement).all()

    # session.get(Model, id)
    def get(self, snippet_id: int) -> Snippet | None:
        return self.session.get(Snippet, snippet_id)

    # Check + session.delete + commit
    def delete(self, snippet_id: int) -> None:
        snippet = self.session.get(Snippet, snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        self.session.delete(snippet)
        self.session.commit()

    def search(self, query: str, language : Language | None = None) -> Sequence[Snippet]:
        search = f"%{query}%"
        statment = select(Snippet).where(Snippet.title.ilike(search) | Snippet.code.ilike(search))
        if language is not None:
            statment = statment.where(Snippet.language == language)
        return self.session.exec(statment).all()

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.session.get(Snippet, snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.favorite = not snippet.favorite
        self.session.add(snippet)
        self.session.commit()
        self.session.refresh(snippet)

