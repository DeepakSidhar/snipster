import pytest
from sqlmodel import Session, SQLModel, create_engine

from snipster.models import Language, Snippet


@pytest.fixture(scope="module")
def engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()


# --- Language Enum Tests ---


def test_language_enum_values():
    assert Language.python.value == "py"
    assert Language.javascript.value == "js"
    assert Language.rust.value == "rs"


def test_language_enum_is_string():
    assert isinstance(Language.python, str)
    assert Language.python == "py"


# --- Snippet Creation Tests ---


def test_create_snippet_required_fields(session):
    snippet = Snippet(
        title="Hello World",
        code="print('Hello')",
        language=Language.python,
    )
    session.add(snippet)
    session.commit()
    session.refresh(snippet)
    assert snippet.id is not None
    assert snippet.title == "Hello World"
    assert snippet.code == "print('Hello')"
    assert snippet.language == Language.python


def test_create_snippet_all_fields(session):
    snippet = Snippet(
        title="Hello World",
        code="print('Hello')",
        description="A simple hello world program",
        language=Language.python,
        tags="intro,test",
        favorite=True,
    )
    session.add(snippet)
    session.commit()
    session.refresh(snippet)
    assert snippet.description == "A simple hello world program"
    assert snippet.tags == "intro,test"
    assert snippet.favorite is True


def test_snippet_default_values():
    snippet = Snippet(
        title="Test",
        code="x = 1",
        language=Language.python,
    )
    assert snippet.description is None
    assert snippet.tags is None
    assert snippet.favorite is False


def test_snippet_created_at_auto_generated(session):
    snippet = Snippet(
        title="Timestamp Test",
        code="pass",
        language=Language.python,
    )
    assert snippet.created_at is not None
    session.add(snippet)
    session.commit()
    session.refresh(snippet)
    assert snippet.created_at is not None


# --- String Representation ---


def test_snippet_str():
    snippet = Snippet(
        title="Hello World",
        code="print('Hello')",
        language=Language.python,
    )
    assert str(snippet) == "Hello World (py)"


def test_snippet_str_different_languages():
    js_snippet = Snippet(
        title="Console Log", code="console.log('hi')", language=Language.javascript
    )
    rs_snippet = Snippet(title="Println", code='println!("hi")', language=Language.rust)
    assert str(js_snippet) == "Console Log (js)"
    assert str(rs_snippet) == "Println (rs)"


# --- Tag List Property ---


def test_tag_list_with_tags():
    snippet = Snippet(
        title="Tagged",
        code="pass",
        language=Language.python,
        tags="python,beginner,tutorial",
    )
    assert snippet.tag_list == ["python", "beginner", "tutorial"]


def test_tag_list_empty():
    snippet = Snippet(
        title="No Tags",
        code="pass",
        language=Language.python,
    )
    assert snippet.tag_list == []


def test_tag_list_single_tag():
    snippet = Snippet(
        title="One Tag",
        code="pass",
        language=Language.python,
        tags="solo",
    )
    assert snippet.tag_list == ["solo"]


# --- Alternative Constructor ---


def test_create_snippet_classmethod():
    snippet = Snippet.create_snippet(
        title="good snippet",
        code="print('Hello')",
        description="A simple hello world program",
        language=Language.python,
        tags="intro,test",
    )
    assert snippet.title == "good snippet"
    assert snippet.code == "print('Hello')"


def test_create_snippet_classmethod_short_title():
    with pytest.raises(ValueError) as excinfo:
        Snippet.create_snippet(
            title="ab",
            code="print('Hello')",
            language=Language.python,
        )
    assert "Title must be at least 3 characters long" in str(excinfo.value)


def test_create_snippet_classmethod_minimum_title():
    snippet = Snippet.create_snippet(
        title="abc",
        code="x = 1",
        language=Language.python,
    )
    assert snippet.title == "abc"


# --- Database Persistence ---


def test_multiple_snippets_stored(session):
    snippets = [
        Snippet(title="First", code="1", language=Language.python),
        Snippet(title="Second", code="2", language=Language.javascript),
        Snippet(title="Third", code="3", language=Language.rust),
    ]
    for s in snippets:
        session.add(s)
    session.commit()
    from sqlmodel import select

    results = session.exec(select(Snippet)).all()
    assert len(results) >= 3
