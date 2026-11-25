from pathlib import Path

import pytest

from tests.conftest import BenchmarkRecorder


def test_benchmark_recorder_budget_and_strict_mode(mocker) -> None:
    # Simulate 200ms per call (0.0 -> 0.2 -> 0.2 -> 0.4)
    mocker.patch(
        'tests.conftest.perf_counter',
        side_effect=[0.0, 0.2, 0.2, 0.4],
    )
    recorder = BenchmarkRecorder(default_iterations=2, strict=False)
    result = recorder.measure('op.slow', lambda: 'ok', max_avg_ms=100.0)
    assert result == 'ok'
    assert len(recorder.entries) == 1
    assert recorder.entries[0].avg_ms == pytest.approx(200.0)
    assert recorder.entries[0].budget_ms == 100.0
    assert recorder.entries[0].exceeded is True

    mocker.patch('tests.conftest.perf_counter', side_effect=[0.0, 0.2])
    strict_recorder = BenchmarkRecorder(default_iterations=1, strict=True)
    with pytest.raises(
        AssertionError, match=r'Latency regression in op\.slow'
    ):
        strict_recorder.measure('op.slow', lambda: 'ok', max_avg_ms=100.0)


def test_benchmark_recorder_baseline_save_load_and_regression(
    tmp_path: Path,
    mocker,
) -> None:
    baseline_file = tmp_path / 'baseline.json'

    mocker.patch('tests.conftest.perf_counter', side_effect=[0.0, 0.1])
    rec1 = BenchmarkRecorder(default_iterations=1)
    rec1.measure('DeviceInfo.get_screen_gui_xml', lambda: '<xml/>')
    saved = rec1.save_baseline(baseline_file)
    assert saved == baseline_file.resolve()

    loaded = BenchmarkRecorder.load_baseline(baseline_file)
    assert loaded == {'DeviceInfo.get_screen_gui_xml': 100.0}

    # 25% regression allowance -> budget = 125.0 ms; 150 ms must fail in strict mode
    mocker.patch('tests.conftest.perf_counter', side_effect=[0.0, 0.15])
    rec2 = BenchmarkRecorder(
        default_iterations=1,
        baseline=loaded,
        max_regression_pct=25.0,
        strict=True,
    )
    with pytest.raises(
        AssertionError,
        match=r'Latency regression in DeviceInfo\.get_screen_gui_xml',
    ):
        rec2.measure('DeviceInfo.get_screen_gui_xml', lambda: '<xml/>')
