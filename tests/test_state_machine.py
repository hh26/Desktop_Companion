"""Unit tests for Finite State Machine, physics, and boundaries."""

import pytest
from backend.state_machine import CompanionEngine, State, Direction


@pytest.fixture
def test_config():
    return {
        "render": {"scale": 2.0, "frame_width": 32, "frame_height": 32},
        "movement": {
            "walk_speed_px_per_tick": 5.0,
            "wander_interval_min_seconds": 1.0,
            "wander_interval_max_seconds": 2.0,
            "gravity_px_per_tick": 10.0
        },
        "behavior_weights": {"idle": 0.0, "wander": 1.0, "sleep": 0.0}
    }


def test_initial_state(test_config):
    engine = CompanionEngine(test_config)
    assert engine.state == State.IDLE
    assert engine.width == 64
    assert engine.height == 64


def test_set_bounds(test_config):
    engine = CompanionEngine(test_config)
    engine.set_bounds(0, 0, 1000, 800)
    assert engine.min_x == 0
    assert engine.min_y == 0
    assert engine.max_x == 1000 - 64
    assert engine.y == 500.0


def test_transition_from_idle_to_walking(test_config):
    engine = CompanionEngine(test_config)
    engine.target_duration = 0.5
    # Advance time past target duration
    engine.update(0.6)
    assert engine.state == State.WALKING


def test_walking_movement_and_boundary_reversal(test_config):
    engine = CompanionEngine(test_config)
    engine.state = State.WALKING
    engine.direction = Direction.RIGHT
    engine.x = engine.max_x - 2.0
    engine.target_duration = 10.0

    # Moving right should hit boundary and reverse to left, switching state to sitting
    engine.update(0.1)
    assert engine.state == State.SITTING
    assert engine.direction == Direction.LEFT
    assert engine.x == float(engine.max_x)


def test_drag_and_drop_physics(test_config):
    engine = CompanionEngine(test_config)
    engine.set_bounds(0, 0, 1000, 800)

    # Grab pet at (100, 100)
    engine.handle_mouse_down(100, 100)
    assert engine.state == State.DRAGGED

    # Drag to mid-air (200, 200)
    engine.handle_mouse_drag(200, 200)
    assert engine.state == State.DRAGGED

    # Release in mid-air -> should transition to FALLING
    engine.handle_mouse_up()
    assert engine.state == State.FALLING

    # Simulate gravity steps until it lands on floor
    for _ in range(50):
        update = engine.update(0.05)
        if engine.state == State.SITTING:
            break

    assert engine.state == State.SITTING
    assert engine.y == float(engine.max_y)


def test_hug_state_transitions(test_config):
    engine = CompanionEngine(test_config)
    engine.state = State.WAITING_HUG
    engine.target_duration = 5.0
    engine.update(0.1)
    assert engine.state == State.WAITING_HUG

    # Transition to HUGGING
    engine.state = State.HUGGING
    engine.target_duration = 1.0
    engine.update(1.2)
    # Hug finished, should return to idle
    assert engine.state == State.IDLE


def test_kiss_state_transitions(test_config):
    engine = CompanionEngine(test_config)
    engine.state = State.WAITING_KISS
    engine.target_duration = 5.0
    engine.update(0.1)
    assert engine.state == State.WAITING_KISS

    # Transition to KISSING
    engine.state = State.KISSING
    engine.target_duration = 1.0
    engine.update(1.2)
    # Kiss finished, should return to idle
    assert engine.state == State.IDLE


def test_hanging_physics_and_release(test_config):
    engine = CompanionEngine(test_config)
    engine.set_bounds(0, 0, 1000, 800)

    # Grab pet and drag to mid-air
    engine.handle_mouse_down(100, 100)
    engine.handle_mouse_drag(200, 200)

    # Release with allow_hang=True and 100% chance
    hung = engine.handle_mouse_up(allow_hang=True, hang_chance=1.0)
    assert hung is True
    assert engine.state == State.HANGING

    # While hanging, coordinates stay fixed and gravity does not pull him down yet
    initial_y = engine.y
    engine.target_duration = 2.0
    engine.update(1.0)
    assert engine.state == State.HANGING
    assert engine.y == initial_y

    # Exceed target duration: realizes and transitions to FALLING
    engine.update(1.2)
    assert engine.state == State.FALLING

    # Gravity pulls him down until landing on floor
    for _ in range(50):
        engine.update(0.05)
        if engine.state == State.SITTING:
            break

    assert engine.state == State.SITTING
    assert engine.y == float(engine.max_y)

