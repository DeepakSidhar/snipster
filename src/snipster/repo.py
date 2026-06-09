from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlmodel import Session, col, select

from .exceptions import SnippetNotFoundError
from .models import Language, Snippet


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

    @abstractmethod
    def tag(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        pass

    # def _update_tags(self, snippet, tags, *, remove, sort) -> str:
    def _update_tags(
        self, snippet: Snippet, tags: tuple[str, ...], *, remove: bool, sort: bool
    ) -> str:
        # Parse existing tags into a set
        existing = {
            tag.strip() for tag in (snippet.tags or "").split(",") if tag.strip()
        }
        # Parse new tags into a set
        new = {tag.strip() for tag in tags if tag.strip()}
        all_tags = existing - new if remove else existing | new
        # Join and return as comma-separated string
        tag_list = sorted(all_tags) if sort else list(all_tags)
        return ", ".join(tag_list)


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

    def search(
        self, term: str, *, language: Language | None = None
    ) -> Sequence[Snippet]:
        term = term.lower()
        results = []
        for snippet in self._data.values():
            text = term in snippet.title.lower() or term in snippet.code.lower()
            lang = language is None or snippet.language == language
            if text and lang:
                results.append(snippet)
        return results

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self._data.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.favorite = not snippet.favorite

    def tag(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        snippet = self._data.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.tags = self._update_tags(snippet, tags, remove=remove, sort=sort)


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

    def search(
        self, term: str, *, language: Language | None = None
    ) -> Sequence[Snippet]:
        search_term = f"%{term}%"
        statement = select(Snippet).where(
            col(Snippet.title).ilike(search_term) | col(Snippet.code).ilike(search_term)
        )
        if language is not None:
            statement = statement.where(Snippet.language == language)
        return self.session.exec(statement).all()

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.session.get(Snippet, snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.favorite = not snippet.favorite
        self.session.add(snippet)
        self.session.commit()
        self.session.refresh(snippet)

    def tag(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        snippet = self.session.get(Snippet, snippet_id)
        if snippet is None:
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")
        snippet.tags = self._update_tags(snippet, tags, remove=remove, sort=sort)
        self.session.add(snippet)
        self.session.commit()
        self.session.refresh(snippet)
