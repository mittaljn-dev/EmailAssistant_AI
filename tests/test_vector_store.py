"""
test_vector_store.py
────────────────────
Tests for the vector_store module.

Run with:
    uv run pytest tests/ -v

Each test function starts with test_ so pytest finds it automatically.
The -v flag means verbose — shows each test name and pass/fail.
"""

# sys and Path let us make sure Python can find our src/ package
import sys
from pathlib import Path

# Add the project root to Python's search path.
# This is needed so "from src.email_assistant..." works when
# pytest runs from the project root directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pytest is our testing framework
import pytest

# Import the functions we want to test
from src.email_assistant.vector_store import (
    save_email,
    search_emails,
    get_all_emails,
    delete_all_emails,
    collection_count,
)


# ── Fixtures ───────────────────────────────────────────────────
# A fixture is a function that runs before tests to set up
# a known starting state. The @pytest.fixture decorator tells
# pytest this is a fixture, not a regular test.

@pytest.fixture(autouse=True)
def clean_database():
    """
    This fixture runs before EVERY test automatically.
    autouse=True means we don't need to manually request it.

    It clears the database before each test so tests don't
    interfere with each other. A clean database means each
    test starts from a known empty state.

    This is called test isolation — each test is independent.
    """
    delete_all_emails()
    # yield passes control to the test function
    # everything after yield runs AFTER the test completes
    yield
    # Clean up after the test too — leave no trace
    delete_all_emails()


# ── Tests ──────────────────────────────────────────────────────

def test_collection_starts_empty():
    """
    After clearing, the collection should have zero records.
    This is the simplest possible test — verifies our
    clean_database fixture is working correctly.
    """
    # assert means "I claim this is true"
    # If collection_count() returns anything other than 0,
    # this test fails with a clear error message
    assert collection_count() == 0


def test_save_email_increases_count():
    """
    Saving one email should increase the count from 0 to 1.
    Tests that save_email() actually stores something.
    """
    assert collection_count() == 0        # starts empty

    save_email(
        original="Please send the report by Friday.",
        processed="Please submit the report by Friday.",
        action="rewrite"
    )

    assert collection_count() == 1        # now has one record


def test_save_multiple_emails():
    """
    Saving three emails should result in count of 3.
    Tests that multiple saves work correctly.
    """
    save_email("Email one.", "Result one.", "rewrite")
    save_email("Email two.", "Result two.", "summarize")
    save_email("Email three.", "Result three.", "extract")

    assert collection_count() == 3


def test_save_email_returns_string_id():
    """
    save_email() should return a UUID string as the record ID.
    Tests that the return value is a non-empty string.

    A UUID looks like: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    """
    doc_id = save_email("Test email.", "Test result.", "rewrite")

    # Check it returned something
    assert doc_id is not None

    # Check it's a string
    assert isinstance(doc_id, str)

    # Check it's not empty
    assert len(doc_id) > 0


def test_search_returns_list():
    """
    search_emails() should always return a list.
    Tests the return type even when database is empty.
    """
    # Search on empty database should return empty list
    # not None, not an error
    results = search_emails("any query")
    assert isinstance(results, list)


def test_search_finds_relevant_email():
    """
    After saving an email about deadlines, searching for
    'deadline' should find it.

    This tests that semantic search actually works —
    that saving and searching are connected correctly.
    """
    save_email(
        original="The project deadline is next Friday.",
        processed="The project is due next Friday.",
        action="rewrite"
    )

    results = search_emails("deadline friday")

    # Should find at least one result
    assert len(results) >= 1

    # Each result should have these three keys
    assert "document" in results[0]
    assert "metadata" in results[0]
    assert "distance" in results[0]


def test_search_result_metadata_has_required_fields():
    """
    Each search result's metadata should contain
    action, timestamp, and preview fields.

    Tests that save_email() stores metadata correctly.
    """
    save_email(
        original="Meeting moved to 3pm tomorrow.",
        processed="The meeting has been rescheduled to 3:00 PM tomorrow.",
        action="rewrite"
    )

    results = search_emails("meeting time")
    assert len(results) >= 1

    metadata = results[0]["metadata"]

    # Check all required metadata fields exist
    assert "action" in metadata
    assert "timestamp" in metadata
    assert "preview" in metadata

    # Check the action was stored correctly
    assert metadata["action"] == "rewrite"


def test_search_result_distance_is_float():
    """
    Distance scores should be floating point numbers
    between 0.0 and 2.0 (cosine distance range).
    """
    save_email("Test email content.", "Test result.", "summarize")
    results = search_emails("test email")

    assert len(results) >= 1
    distance = results[0]["distance"]

    # Should be a number
    assert isinstance(distance, float)

    # Cosine distance is always between 0 and 2
    assert 0.0 <= distance <= 2.0


def test_get_all_emails_returns_list():
    """
    get_all_emails() should return a list.
    Tests return type on both empty and populated database.
    """
    # Empty database
    assert isinstance(get_all_emails(), list)

    # Populated database
    save_email("Some email.", "Some result.", "clarity")
    assert isinstance(get_all_emails(), list)


def test_get_all_emails_returns_correct_count():
    """
    get_all_emails() should return the same number of
    records as collection_count().
    """
    save_email("Email A.", "Result A.", "rewrite")
    save_email("Email B.", "Result B.", "summarize")

    all_emails = get_all_emails()
    assert len(all_emails) == 2


def test_delete_all_emails_clears_database():
    """
    After saving emails and deleting all, count should be 0.
    Tests that delete_all_emails() actually removes records.
    """
    save_email("Email to delete.", "Result.", "extract")
    save_email("Another email.", "Result.", "clarity")
    assert collection_count() == 2        # confirm they were saved

    deleted = delete_all_emails()

    assert deleted == 2                   # returns count of deleted
    assert collection_count() == 0        # database is now empty


def test_delete_returns_zero_on_empty_database():
    """
    Deleting from an empty database should return 0
    without crashing.

    Tests edge case — what happens when there's nothing to delete.
    """
    assert collection_count() == 0
    deleted = delete_all_emails()
    assert deleted == 0


def test_all_four_action_types_save_correctly():
    """
    All four action types should save and be retrievable.
    Tests that the action field works for every feature.
    """
    save_email("Email 1.", "Result 1.", "rewrite")
    save_email("Email 2.", "Result 2.", "summarize")
    save_email("Email 3.", "Result 3.", "extract")
    save_email("Email 4.", "Result 4.", "clarity")

    assert collection_count() == 4

    all_emails = get_all_emails()
    # Extract all action types from saved emails
    actions = [e["metadata"]["action"] for e in all_emails]

    assert "rewrite"   in actions
    assert "summarize" in actions
    assert "extract"   in actions
    assert "clarity"   in actions