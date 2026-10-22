"""Unit tests for sound manager audio controls."""

from backend.sound_manager import SoundManager


def test_sound_manager_mute_toggle():
    sm = SoundManager(is_muted=False)
    assert not sm.is_muted

    toggled = sm.toggle_mute()
    assert toggled is True
    assert sm.is_muted is True

    # Play when muted should not raise
    sm.play("non_existent_file.wav")
