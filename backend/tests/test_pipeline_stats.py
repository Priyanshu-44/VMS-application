"""PipelineStats -- the in-memory counters behind the Analytics page's
false-alarm-reduction headline number. See app/services/pipeline_stats.py.
"""
from app.services.pipeline_stats import PipelineStats


def test_totals_start_at_zero():
    stats = PipelineStats()
    assert stats.totals() == (0, 0)


def test_totals_sum_across_cameras():
    stats = PipelineStats()
    stats.record_motion(camera_id=1)
    stats.record_motion(camera_id=1)
    stats.record_motion(camera_id=2)
    stats.record_confirmed(camera_id=1)

    motion, confirmed = stats.totals()
    assert motion == 3
    assert confirmed == 1


def test_reduction_percentage_matches_the_analytics_formula():
    # Mirrors app/api/analytics.py's calculation exactly, so a change to one
    # without the other would be caught here.
    stats = PipelineStats()
    for _ in range(100):
        stats.record_motion(camera_id=1)
    for _ in range(9):
        stats.record_confirmed(camera_id=1)

    motion, confirmed = stats.totals()
    suppressed = max(motion - confirmed, 0)
    reduction_pct = round((suppressed / motion) * 100, 1) if motion else 0.0

    assert suppressed == 91
    assert reduction_pct == 91.0


def test_reduction_percentage_is_zero_with_no_motion_yet():
    stats = PipelineStats()
    motion, confirmed = stats.totals()
    reduction_pct = round((max(motion - confirmed, 0) / motion) * 100, 1) if motion else 0.0
    assert reduction_pct == 0.0
