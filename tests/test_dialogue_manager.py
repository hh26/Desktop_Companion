"""Unit tests for dialogue manager quote selection and triggers."""

from backend.dialogue_manager import DialogueManager


def test_dialogue_manager_quotes():
    data = {
        "idle_quotes": ["Quote 1", "Quote 2"],
        "click_quotes": ["Click 1", "Click 2"]
    }
    dm = DialogueManager(data)

    q1 = dm.get_random_idle_quote()
    assert q1 in data["idle_quotes"]

    cq1 = dm.get_random_click_quote()
    assert cq1 in data["click_quotes"]


def test_dialogue_manager_update_trigger():
    data = {"idle_quotes": ["Hello world!"]}
    dm = DialogueManager(data)
    dm.interval = 1.0  # Force 1 second interval

    assert dm.update(0.5) is None
    quote = dm.update(0.6)  # Exceeds interval
    assert quote == "Hello world!"


def test_dialogue_manager_bored_quotes():
    data = {
        "bored_quotes": {
            "dad_joke": ["Hi bored, I'm {name}!"],
            "creative": ["Go spin in your chair 3 times!"]
        }
    }
    dm = DialogueManager(data)

    # Test with custom companion name
    quote = dm.get_bored_quote(companion_name="Kannan")
    assert quote in ["Hi bored, I'm Kannan!", "Go spin in your chair 3 times!"]


def test_dialogue_manager_say_something_quotes():
    data = {
        "say_something_quotes": {
            "literal": ["Something."],
            "facts": ["Octopuses have three hearts!"]
        }
    }
    dm = DialogueManager(data)

    quote = dm.get_say_something_quote()
    assert quote in ["Something.", "Octopuses have three hearts!"]


def test_dialogue_manager_hanging_quotes():
    data = {
        "hanging_quotes": ["Look ma, no gravity! 🛸✨"],
        "hanging_drop_quotes": ["Uh oh... don't look down! 😱"]
    }
    dm = DialogueManager(data)

    hq = dm.get_random_hanging_quote()
    assert hq == "Look ma, no gravity! 🛸✨"

    dq = dm.get_random_hanging_drop_quote()
    assert dq == "Uh oh... don't look down! 😱"
