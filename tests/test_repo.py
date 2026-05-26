import pytest
from snipster.exceptions import SnippetNotFoundError
from snipster.models import Language, Snippet
from snipster.repo import (
  #  DBSnippetRepo,
  #  InMemorySnippetRepo,
    SnippetRepository,
)


# --- Interface Tests ---


def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError, match="Can't instantiate abstract class SnippetRepository"):
        SnippetRepository()


def test_cannot_subclass_without_all_methods():
    class IncompleteRepo(SnippetRepository):
        def add(self, snippet):
            pass

        def list(self):
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteRepo"):
        IncompleteRepo()


# --- Fixtures ---
# Note: `engine` and `session` come from tests/conftest.py.


@pytest.fixture
def example_snippet() -> Snippet:
    return Snippet(title="Test", code="print('hi')", language=Language.python)


@pytest.fixture
def example_snippets() -> list[Snippet]:
    return [
        Snippet(
            title="print to stdout",
            code="print('hello world')",
            language=Language.python,
        ),
        Snippet(
            title="get user input",
            code="input('enter city: ')",
            language=Language.python,
        ),
        Snippet(
            title="random number",
            code="let _ = nums.choose(&mut rng);",
            language=Language.rust,
        ),
    ]


# --- InMemorySnippetRepo Tests ---


def test_in_memory_add_and_list(example_snippet):
    repo = InMemorySnippetRepo()
    repo.add(example_snippet)
    assert len(repo.list()) == 1
    assert repo.list()[0].title == "Test"


def test_in_memory_get(example_snippet):
    repo = InMemorySnippetRepo()
    repo.add(example_snippet)
    retrieved = repo.get(1)
    assert retrieved is not None
    assert retrieved.title == "Test"
    assert retrieved.code == "print('hi')"


def test_in_memory_get_nonexistent():
    repo = InMemorySnippetRepo()
    assert repo.get(999) is None


def test_in_memory_delete(example_snippet):
    repo = InMemorySnippetRepo()
    repo.add(example_snippet)
    repo.delete(1)
    assert len(repo.list()) == 0


def test_in_memory_delete_nonexistent():
    repo = InMemorySnippetRepo()
    with pytest.raises(SnippetNotFoundError):
        repo.delete(999)


def test_in_memory_assigns_ids(example_snippets):
    repo = InMemorySnippetRepo()
    for s in example_snippets:
        repo.add(s)
    assert len(repo.list()) == 3
    assert repo.get(1) is not None
    assert repo.get(2) is not None
    assert repo.get(3) is not None


def test_in_memory_full_lifecycle(example_snippet):
    repo = InMemorySnippetRepo()
    repo.add(example_snippet)
    assert len(repo.list()) == 1
    retrieved = repo.get(1)
    assert retrieved is not None
    assert retrieved.title == "Test"
    with pytest.raises(SnippetNotFoundError):
        repo.delete(2)
    repo.delete(1)
    assert len(repo.list()) == 0
    assert repo.get(1) is None


# --- DBSnippetRepo Tests ---


def test_db_add_and_list(session, example_snippet):
    repo = DBSnippetRepo(session)
    repo.add(example_snippet)
    assert len(repo.list()) == 1
    assert repo.list()[0].title == "Test"


def test_db_get(session, example_snippet):
    repo = DBSnippetRepo(session)
    repo.add(example_snippet)
    retrieved = repo.get(1)
    assert retrieved is not None
    assert retrieved.title == "Test"


def test_db_get_nonexistent(session):
    repo = DBSnippetRepo(session)
    assert repo.get(999) is None


def test_db_delete(session, example_snippet):
    repo = DBSnippetRepo(session)
    repo.add(example_snippet)
    repo.delete(1)
    assert len(repo.list()) == 0


def test_db_delete_nonexistent(session):
    repo = DBSnippetRepo(session)
    with pytest.raises(SnippetNotFoundError):
        repo.delete(999)


def test_db_assigns_id(session, example_snippet):
    repo = DBSnippetRepo(session)
    repo.add(example_snippet)
    assert example_snippet.id is not None
    assert example_snippet.id == 1


def test_db_full_lifecycle(session, example_snippet):
    repo = DBSnippetRepo(session)
    repo.add(example_snippet)
    assert len(repo.list()) == 1
    snippet = repo.get(1)
    assert snippet is not None
    assert snippet.title == "Test"
    repo.delete(1)
    assert len(repo.list()) == 0
    with pytest.raises(SnippetNotFoundError):
        repo.delete(1)