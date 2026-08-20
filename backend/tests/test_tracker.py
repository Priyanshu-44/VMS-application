"""CameraTracker / Track -- Layer 4 of the false-alarm pipeline: dwell time
and cooldown. See app/services/tracker.py's module docstring for why tracks
are keyed by (zone, class) rather than true multi-object identity -- these
tests exercise that documented tradeoff directly.
"""
import pytest

from app.services import tracker as tracker_module
from app.services.tracker import STALE_AFTER_SECONDS, CameraTracker


@pytest.fixture(autouse=True)
def fixed_cooldown(monkeypatch):
    # Pin the cooldown window so these tests don't drift if the demo's
    # EVENT_COOLDOWN_SECONDS ever gets retuned again (see config.py).
    monkeypatch.setattr(tracker_module, "EVENT_COOLDOWN_SECONDS", 10)


def test_dwell_accumulates_across_updates_of_the_same_key():
    t = CameraTracker()
    first = t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)
    assert first.dwell_seconds() == 0

    second = t.update(zone_id=1, cls_name="person", centroid=(0.51, 0.5), now=103.5)
    assert second.track_id == first.track_id
    assert second.dwell_seconds() == pytest.approx(3.5)


def test_different_zone_or_class_gets_a_separate_track():
    t = CameraTracker()
    base = t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)
    other_zone = t.update(zone_id=2, cls_name="person", centroid=(0.5, 0.5), now=100.0)
    other_class = t.update(zone_id=1, cls_name="car", centroid=(0.5, 0.5), now=100.0)

    assert len(t.tracks) == 3
    assert other_zone.track_id != base.track_id
    assert other_class.track_id != base.track_id


def test_cooldown_gates_new_events_for_the_configured_window():
    t = CameraTracker()
    track = t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)
    assert track.in_cooldown(100.0) is False  # never fired yet

    track.start_cooldown(100.0)
    assert track.in_cooldown(105.0) is True    # 5s < 10s cooldown
    assert track.in_cooldown(109.9) is True    # just under the boundary
    assert track.in_cooldown(110.0) is False   # cooldown elapsed


def test_stale_track_is_pruned_and_a_fresh_sighting_resets_dwell():
    t = CameraTracker()
    t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)

    gap = STALE_AFTER_SECONDS + 1.5
    t.prune(now=100.0 + gap)
    assert len(t.tracks) == 0

    # A sighting after the stale gap starts a brand-new track rather than
    # resuming the old one -- exactly the tradeoff the module docstring
    # explains: dwell does not survive a gap longer than STALE_AFTER_SECONDS.
    fresh = t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0 + gap)
    assert fresh.dwell_seconds() == 0


def test_gap_within_the_stale_window_keeps_the_same_track():
    t = CameraTracker()
    first = t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)

    gap = STALE_AFTER_SECONDS - 1.0
    second = t.update(zone_id=1, cls_name="person", centroid=(0.52, 0.5), now=100.0 + gap)

    assert second.track_id == first.track_id
    assert second.dwell_seconds() == pytest.approx(gap)


def test_prune_only_removes_tracks_past_the_stale_threshold():
    t = CameraTracker()
    t.update(zone_id=1, cls_name="person", centroid=(0.5, 0.5), now=100.0)
    t.update(zone_id=2, cls_name="car", centroid=(0.5, 0.5), now=100.0 + STALE_AFTER_SECONDS + 1)

    t.prune(now=100.0 + STALE_AFTER_SECONDS + 1)
    remaining = list(t.tracks.values())
    assert len(remaining) == 1
    assert remaining[0].zone_id == 2
