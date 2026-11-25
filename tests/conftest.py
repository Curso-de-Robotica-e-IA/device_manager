"""Pytest configuration supporting two test modes:

1. Mocked mode (default): fast, isolated unit tests (`pytest`).
2. Real device mode (`pytest --device -m device`): runs end-to-end tests
   against a physical Android device and prints a latency benchmark table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Generator

import pytest

from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.connection.device_connection import DeviceConnection
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.manager import DeviceManager


@dataclass
class BenchmarkEntry:
    name: str
    iterations: int
    min_ms: float
    avg_ms: float
    max_ms: float
    budget_ms: float | None = None
    baseline_ms: float | None = None
    exceeded: bool = False


class BenchmarkRecorder:
    """Collects execution timings (in ms) for real-device benchmark tests."""

    def __init__(
        self,
        default_iterations: int = 3,
        baseline: dict[str, float] | None = None,
        max_regression_pct: float = 25.0,
        strict: bool = False,
    ) -> None:
        self.default_iterations = max(1, default_iterations)
        self.baseline: dict[str, float] = dict(baseline or {})
        self.max_regression_pct = max_regression_pct
        self.strict = strict
        self.entries: list[BenchmarkEntry] = []

    def _resolve_budget(
        self,
        name: str,
        max_avg_ms: float | None,
    ) -> tuple[float | None, float | None]:
        baseline_ms = self.baseline.get(name)
        baseline_limit = (
            baseline_ms * (1.0 + self.max_regression_pct / 100.0)
            if baseline_ms is not None
            else None
        )
        if max_avg_ms is not None and baseline_limit is not None:
            return min(max_avg_ms, baseline_limit), baseline_ms
        return (
            max_avg_ms if max_avg_ms is not None else baseline_limit,
            baseline_ms,
        )

    def measure(
        self,
        name: str,
        func: Callable[[], Any],
        iterations: int | None = None,
        max_avg_ms: float | None = None,
    ) -> Any:
        runs = max(1, iterations or self.default_iterations)
        timings_ms: list[float] = []
        last_result: Any = None
        for _ in range(runs):
            start = perf_counter()
            last_result = func()
            timings_ms.append((perf_counter() - start) * 1000.0)

        avg_ms = sum(timings_ms) / len(timings_ms)
        budget_ms, baseline_ms = self._resolve_budget(name, max_avg_ms)
        exceeded = budget_ms is not None and avg_ms > budget_ms

        self.entries.append(
            BenchmarkEntry(
                name=name,
                iterations=runs,
                min_ms=min(timings_ms),
                avg_ms=avg_ms,
                max_ms=max(timings_ms),
                budget_ms=budget_ms,
                baseline_ms=baseline_ms,
                exceeded=exceeded,
            )
        )
        if self.strict and exceeded:
            raise AssertionError(
                f'Latency regression in {name}: avg {avg_ms:.2f} ms > '
                f'budget {budget_ms:.2f} ms'
            )
        return last_result

    def save_baseline(self, path: str | Path) -> Path:
        dest = Path(path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            entry.name: round(entry.avg_ms, 2) for entry in self.entries
        }
        dest.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        return dest

    @staticmethod
    def load_baseline(path: str | Path) -> dict[str, float]:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        return {str(k): float(v) for k, v in raw.items()}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        '--device',
        action='store_true',
        default=False,
        help='Run real-device integration and benchmark tests.',
    )
    parser.addoption(
        '--device-serial',
        action='store',
        default=None,
        help='Specific Android device serial to target in --device mode.',
    )
    parser.addoption(
        '--benchmark-iterations',
        action='store',
        type=int,
        default=3,
        help='Number of iterations per benchmarked operation (default: 3).',
    )
    parser.addoption(
        '--benchmark-output',
        action='store',
        default='benchmark_report.md',
        help='Output file path for the Markdown benchmark report (default: benchmark_report.md).',
    )
    parser.addoption(
        '--benchmark-baseline',
        action='store',
        default=None,
        help='Optional JSON baseline file to compare average latencies against.',
    )
    parser.addoption(
        '--benchmark-save-baseline',
        action='store',
        default=None,
        help='Optional JSON output path to save current benchmark averages as a baseline.',
    )
    parser.addoption(
        '--benchmark-max-regression-pct',
        action='store',
        type=float,
        default=25.0,
        help='Maximum allowed latency increase (%) over baseline (default: 25.0).',
    )
    parser.addoption(
        '--benchmark-strict',
        action='store_true',
        default=False,
        help='Fail benchmark tests immediately when any operation exceeds its budget/baseline.',
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if config.getoption('--device'):
        return
    skip_device = pytest.mark.skip(
        reason='Real-device benchmark test (pass --device to run).'
    )
    for item in items:
        if 'device' in item.keywords:
            item.add_marker(skip_device)


@pytest.fixture(scope='session')
def benchmark_recorder(request: pytest.FixtureRequest) -> BenchmarkRecorder:
    iterations = int(request.config.getoption('--benchmark-iterations'))
    baseline_opt = request.config.getoption('--benchmark-baseline')
    baseline = (
        BenchmarkRecorder.load_baseline(baseline_opt) if baseline_opt else None
    )
    max_reg = float(request.config.getoption('--benchmark-max-regression-pct'))
    strict = bool(request.config.getoption('--benchmark-strict'))
    recorder = BenchmarkRecorder(
        default_iterations=iterations,
        baseline=baseline,
        max_regression_pct=max_reg,
        strict=strict,
    )
    request.config._benchmark_recorder = recorder  # type: ignore[attr-defined]
    return recorder


@pytest.fixture(scope='session')
def real_device_manager(
    request: pytest.FixtureRequest,
) -> Generator[DeviceManager, None, None]:
    if not request.config.getoption('--device'):
        pytest.skip('Pass --device to run real-device tests.')

    connector = DeviceConnection(gateway=AdbutilsAdbGateway())
    dm = DeviceManager(check_dependencies=False, connector=connector)
    try:
        if not dm.connected_devices:
            visible = [
                svc.serial_number for svc in dm.connector.visible_devices()
            ]
            if visible:
                dm.connect_devices(visible[0])
        if not dm.connected_devices:
            pytest.skip('No physical Android device connected via ADB.')
        yield dm
    finally:
        dm.close()


@pytest.fixture(scope='session')
def real_device(
    request: pytest.FixtureRequest,
    real_device_manager: DeviceManager,
) -> tuple[str, DeviceInfo, DeviceActions]:
    requested_serial: str | None = request.config.getoption('--device-serial')
    if requested_serial:
        if requested_serial not in real_device_manager:
            real_device_manager.connect_devices(requested_serial)
        if requested_serial not in real_device_manager:
            pytest.skip(
                f'Requested device {requested_serial!r} not connected.'
            )
        serial = requested_serial
    else:
        serial = real_device_manager.connected_devices[0]

    info, actions = real_device_manager[serial]
    request.config._benchmark_serial = serial  # type: ignore[attr-defined]
    return serial, info, actions


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    recorder: BenchmarkRecorder | None = getattr(
        config, '_benchmark_recorder', None
    )
    if not recorder or not recorder.entries:
        return

    output_path = Path(str(config.getoption('--benchmark-output'))).resolve()
    serial = getattr(config, '_benchmark_serial', 'unknown')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        '# Device Benchmark Report',
        '',
        f'- **Date:** {timestamp}',
        f'- **Device Serial:** `{serial}`',
        f'- **Iterations per operation:** {recorder.default_iterations}',
        '',
        '| Operation | Runs | Min (ms) | Avg (ms) | Max (ms) | Budget (ms) | Status |',
        '|---|---:|---:|---:|---:|---:|:---:|',
    ]
    for entry in recorder.entries:
        budget_str = (
            f'{entry.budget_ms:.2f}' if entry.budget_ms is not None else '-'
        )
        status_str = (
            'SLOW'
            if entry.exceeded
            else ('PASS' if entry.budget_ms is not None else '-')
        )
        lines.append(
            f'| `{entry.name}` | {entry.iterations} | '
            f'{entry.min_ms:.2f} | {entry.avg_ms:.2f} | {entry.max_ms:.2f} | '
            f'{budget_str} | {status_str} |'
        )
    lines.append('')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    terminalreporter.write_line(f'Benchmark report saved to: {output_path}')

    save_baseline_opt = config.getoption('--benchmark-save-baseline')
    if save_baseline_opt:
        baseline_path = recorder.save_baseline(save_baseline_opt)
        terminalreporter.write_line(
            f'Benchmark baseline saved to: {baseline_path}'
        )
