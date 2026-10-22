"""Dialogue Manager for Display Buddy."""

import random
from typing import List, Optional, Dict, Any, Union


DEFAULT_BORED_DAD_JOKES = [
    "Hi bored, I'm {name}! Nice to meet you! 😄",
    "Hi bored! I'm your desktop buddy, classic dad joke never fails! 😂",
    "Hi bored, nice to meet you! I'm {name}! 👋✨"
]

DEFAULT_BORED_CREATIVE = [
    "Quick! Stare at the ceiling until you see patterns! 👀",
    "Have you tried spinning around in your chair 3 times? 🔄",
    "Time for a sip of water or a quick stretch! ☕💧",
    "Wanna see me do a backflip? ...Okay, I can't, but imagine it! 🤸‍♂️✨",
    "If you're bored, drag me around the screen and test my gravity! 🚀",
    "Whenever you're bored, right-click me and ask for a hug! 🤗",
    "Draw a tiny smiley face on a sticky note. Right now! 📝😊",
    "What if we opened 50 browser tabs and closed none of them? 🤫"
]

DEFAULT_SAY_SOMETHING_LITERAL = [
    "Something.",
    "Something! 😜",
    "You told me to say 'something', so... something! 😄",
    "...Something! Classic. 😂"
]

DEFAULT_SAY_SOMETHING_FACTS = [
    "Fun fact: Sea otters hold hands when they sleep so they don't drift away! 🦦💤",
    "Did you know octopuses have three hearts and blue blood? 🐙💙",
    "Fun fact: Bananas are technically berries, but strawberries aren't! 🍌🍓",
    "Did you know honey never spoils? Archaeologists found edible honey in 3,000-year-old tombs! 🍯✨",
    "Did you know cats spend about 70% of their lives sleeping? Honestly, mood. 🐱💤",
    "Did you know sloths can hold their breath underwater longer than dolphins? Up to 40 minutes! 🦥🌊",
    "Fun fact: Cows have best friends and get stressed when separated! 🐮❤️",
    "Did you know wombat poop is cube-shaped so it doesn't roll away? True story! 🟦💩",
    "Random thought: Why is 'abbreviation' such a long word? 🤔",
    "Fun fact: A fluffy cumulus cloud can weigh over a million pounds! ☁️✨"
]

DEFAULT_HANGING_QUOTES = [
    "Look ma, no gravity! 🛸✨",
    "Wait... I forgot how to fall! 🧗‍♂️😅",
    "Newton left the chat. 🌌",
    "Gravity is merely a polite suggestion! 😎",
    "I guess I live up here now! 🏠☁️",
    "Help! Who turned off the physics engine?! ⚙️😂",
    "Just hanging out! Get it? 'Hanging' out! 🪂",
    "The floor is lava, so I'm staying right here! 🌋"
]

DEFAULT_HANGING_DROP_QUOTES = [
    "Uh oh... don't look down! 😱",
    "Aaaand gravity's back! 🪂💨",
    "Whoooaaaa! Catch meee! 🏃‍♂️💨",
    "Down I goooo! 🚀"
]


class DialogueManager:
    def __init__(self, dialogues: dict):
        self.idle_quotes: List[str] = dialogues.get("idle_quotes", [])
        self.click_quotes: List[str] = dialogues.get("click_quotes", [])

        # Bored quotes (supports dict or list)
        bored_raw = dialogues.get("bored_quotes")
        if isinstance(bored_raw, dict):
            self.bored_dad_jokes = bored_raw.get("dad_joke", DEFAULT_BORED_DAD_JOKES)
            self.bored_creative = bored_raw.get("creative", DEFAULT_BORED_CREATIVE)
        elif isinstance(bored_raw, list) and bored_raw:
            self.bored_dad_jokes = [q for q in bored_raw if "Hi bored" in q] or DEFAULT_BORED_DAD_JOKES
            self.bored_creative = [q for q in bored_raw if "Hi bored" not in q] or DEFAULT_BORED_CREATIVE
        else:
            self.bored_dad_jokes = DEFAULT_BORED_DAD_JOKES
            self.bored_creative = DEFAULT_BORED_CREATIVE

        # Say something quotes (supports dict or list)
        say_raw = dialogues.get("say_something_quotes")
        if isinstance(say_raw, dict):
            self.say_literal = say_raw.get("literal", DEFAULT_SAY_SOMETHING_LITERAL)
            self.say_facts = say_raw.get("facts", DEFAULT_SAY_SOMETHING_FACTS)
        elif isinstance(say_raw, list) and say_raw:
            self.say_literal = [q for q in say_raw if "something" in q.lower()] or DEFAULT_SAY_SOMETHING_LITERAL
            self.say_facts = [q for q in say_raw if "something" not in q.lower()] or DEFAULT_SAY_SOMETHING_FACTS
        else:
            self.say_literal = DEFAULT_SAY_SOMETHING_LITERAL
            self.say_facts = DEFAULT_SAY_SOMETHING_FACTS

        # Hanging & drop quotes
        self.hanging_quotes = dialogues.get("hanging_quotes") or DEFAULT_HANGING_QUOTES
        self.hanging_drop_quotes = dialogues.get("hanging_drop_quotes") or DEFAULT_HANGING_DROP_QUOTES

        self.last_quote: Optional[str] = None
        self.timer: float = 0.0
        self.interval: float = random.uniform(30.0, 75.0)

    def update(self, delta_time: float) -> Optional[str]:
        """Periodically trigger an idle quote."""
        self.timer += delta_time
        if self.timer >= self.interval:
            self.timer = 0.0
            self.interval = random.uniform(35.0, 80.0)
            return self.get_random_idle_quote()
        return None

    def get_random_idle_quote(self) -> Optional[str]:
        if not self.idle_quotes:
            return None
        choices = [q for q in self.idle_quotes if q != self.last_quote] or self.idle_quotes
        quote = random.choice(choices)
        self.last_quote = quote
        return quote

    def get_random_click_quote(self) -> Optional[str]:
        if not self.click_quotes:
            return None
        choices = [q for q in self.click_quotes if q != self.last_quote] or self.click_quotes
        quote = random.choice(choices)
        self.last_quote = quote
        return quote

    def get_bored_quote(self, companion_name: str = "Buddy") -> str:
        """
        Responds to 'I'm bored.' with 'Hi bored, I'm [name]' dad joke (~50% chance),
        or a fun creative suggestion (~50% chance).
        """
        is_dad_joke = random.random() < 0.50
        if is_dad_joke and self.bored_dad_jokes:
            template = random.choice(self.bored_dad_jokes)
            return template.replace("{name}", companion_name)
        elif self.bored_creative:
            return random.choice(self.bored_creative)
        return f"Hi bored, I'm {companion_name}! Nice to meet you! 😄"

    def get_say_something_quote(self) -> str:
        """
        Responds to 'Say something' by saying 'something' (~45% chance),
        or providing a random fun fact / quirky observation (~55% chance).
        """
        is_literal = random.random() < 0.45
        if is_literal and self.say_literal:
            return random.choice(self.say_literal)
        elif self.say_facts:
            return random.choice(self.say_facts)
        return "Something. 😄"

    def get_random_hanging_quote(self) -> str:
        """Quirky dialogue when companion stays suspended in mid-air."""
        if not self.hanging_quotes:
            return "Look ma, no gravity! 🛸✨"
        return random.choice(self.hanging_quotes)

    def get_random_hanging_drop_quote(self) -> str:
        """Cartoon realization dialogue when hang time expires and gravity returns."""
        if not self.hanging_drop_quotes:
            return "Uh oh... don't look down! 😱"
        return random.choice(self.hanging_drop_quotes)
