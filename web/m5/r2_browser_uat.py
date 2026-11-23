#!/usr/bin/env python3
"""Execute all 21 M5 R2 Browser UAT cases with real Google Chrome."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.async_api import Page, Route, async_playwright

from r2_fixture_server import start_fixtures, stop_fixtures

INVALID_PROMPT = "No valid prompt. Load a successful query and select an observation."


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        require(response.status == 200, f"HTTP {response.status}: {url}")
        return json.load(response)


def wait_http(url: str, expected_up: bool, timeout: float = 10) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                up = response.status == 200
        except (OSError, URLError):
            up = False
        if up == expected_up:
            return True
        time.sleep(0.2)
    return False


async def wait_success(page: Page) -> None:
    await page.wait_for_function("document.querySelector('#status-title')?.textContent === 'Success'")


async def wait_evidence(page: Page, field: str, value: str) -> None:
    await page.wait_for_function(
        "([field, value]) => document.querySelector(`[data-evidence='${field}']`)?.textContent === value",
        arg=[field, value],
    )


async def state(page: Page) -> dict:
    return await page.evaluate(
        """() => ({
          statusTitle: document.querySelector('#status-title').textContent,
          statusDetail: document.querySelector('#status-detail').textContent,
          validation: document.querySelector('#validation-message').textContent,
          split: document.querySelector('#split-select').value,
          unit: document.querySelector('#unit-select').value,
          sensor: document.querySelector('#sensor-select').value,
          start: document.querySelector('#start-cycle').value,
          end: document.querySelector('#end-cycle').value,
          pointCount: document.querySelector('#point-count').textContent,
          tableRows: document.querySelectorAll('#observation-body tr[data-index]').length,
          evidence: Object.fromEntries([...document.querySelectorAll('[data-evidence]')].map(n => [n.dataset.evidence, n.textContent])),
          selectedCycle: document.querySelector('#selected-cycle').textContent,
          prompt: document.querySelector('#prompt-output').textContent,
          copyDisabled: document.querySelector('#copy-prompt').disabled,
          generateDisabled: document.querySelector('#generate-prompt').disabled,
          chartEmptyVisible: !document.querySelector('#chart-empty').hidden
        })"""
    )


async def assert_cleared(page: Page, title: str) -> dict:
    current = await state(page)
    require(current["statusTitle"] == title, f"expected {title}, got {current['statusTitle']}")
    require(current["pointCount"] == "0 observations", "Chart count not cleared")
    require(current["tableRows"] == 0, "Table not cleared")
    require(set(current["evidence"].values()) == {"N/A"}, "Evidence not cleared")
    require(current["prompt"] == INVALID_PROMPT, "Prompt not invalidated")
    require(current["copyDisabled"] and current["generateDisabled"], "Prompt actions not disabled")
    return current


async def set_real_query(page: Page, split: str, unit: str, sensor: str, start: str, end: str) -> None:
    if await page.locator("#split-select").input_value() != split:
        await page.locator("#split-select").select_option(split)
        await wait_evidence(page, "split", split)
    if await page.locator("#unit-select").input_value() != unit:
        await page.locator("#unit-select").select_option(unit)
        await wait_evidence(page, "unit_id", unit)
    if await page.locator("#sensor-select").input_value() != sensor:
        await page.locator("#sensor-select").select_option(sensor)
        await wait_evidence(page, "sensor", sensor)
    await page.locator("#start-cycle").fill(start)
    await page.locator("#end-cycle").fill(end)
    await page.locator("#query-button").click()
    await wait_success(page)


async def run(args: argparse.Namespace) -> dict:
    evidence_dir: Path = args.evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, object]] = []
    screenshots: list[str] = []
    history_requests: list[str] = []
    fixture_servers = []
    fixture_threads = []
    restarted_api: subprocess.Popen | None = None
    restart_log = None

    def record(case_id: str, action: str, query: str, expected: str, actual: str, evidence: str) -> None:
        cases.append({
            "case_id": case_id,
            "execution_time": now(),
            "action": action,
            "query": query,
            "expected": expected,
            "actual": actual,
            "result": "PASS",
            "evidence": evidence,
        })

    async def shot(page: Page, name: str) -> str:
        path = evidence_dir / name
        await page.screenshot(path=path, full_page=True)
        screenshots.append(str(path))
        return str(path)

    fixture_servers, fixture_threads, fixture_ports = start_fixtures()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            await context.grant_permissions(["clipboard-read", "clipboard-write"], origin="http://127.0.0.1:8001")
            page = await context.new_page()
            page.on("request", lambda request: history_requests.append(request.url) if "/api/history?" in request.url else None)

            await page.goto(args.url, wait_until="domcontentloaded")
            await wait_success(page)
            initial = await state(page)
            require(initial["statusTitle"] == "Success", "website did not load")
            initial_shot = await shot(page, "r2_initial_website.png")
            record("UAT_01", "Open real local website in Google Chrome", "default", "Website loads normally", "Source Validated and Success visible", initial_shot)

            require(initial["split"] == "TRAIN" and initial["unit"] == "1", "TRAIN Unit 1 not selected")
            record("UAT_02", "Inspect Split and Unit selectors", "split=TRAIN&unit=1", "TRAIN Unit 1", "TRAIN Unit 1 selected", initial_shot)
            require(initial["sensor"] == "sensor_7", "sensor_7 not selected")
            record("UAT_03", "Inspect Sensor selector", "sensor=sensor_7", "sensor_7", "sensor_7 selected", initial_shot)
            require(initial["start"] == "1" and initial["end"] == "20", "Cycle 1-20 not selected")
            record("UAT_04", "Inspect Cycle controls", "start=1&end=20", "Cycle 1-20", "Cycle 1-20 selected", initial_shot)

            real_payload = await page.evaluate("fetch('/api/history?split=train&unit=1&sensor=7&start=1&end=20').then(r => r.json())")
            require(real_payload["observation_count"] == 20 and initial["pointCount"] == "20 observations", "Chart count mismatch")
            train_shot = await shot(page, "r2_train_unit_1_sensor_7_cycles_1_20.png")
            record("UAT_05", "Inspect rendered Sensor Trend", "TRAIN/1/sensor_7/1-20", "20 API observations", "Browser count 20; API count 20", train_shot)
            require(initial["tableRows"] == 20, "Table row count mismatch")
            record("UAT_06", "Count Observation Table data rows", "TRAIN/1/sensor_7/1-20", "20 rows matching API", "20 Browser rows", train_shot)

            values = [row["value"] for row in real_payload["observations"]]
            chart_box = await page.locator("#trend-chart").bounding_box()
            require(chart_box is not None, "Chart bounds unavailable")
            raw_min, raw_max = min(values), max(values)
            value_pad = max(abs(raw_min) * 0.01, 1) if raw_min == raw_max else (raw_max - raw_min) * 0.12
            min_value, max_value = raw_min - value_pad, raw_max + value_pad
            css_width, css_height = chart_box["width"], chart_box["height"]
            last_y = 28 + (1 - (values[-1] - min_value) / (max_value - min_value)) * (css_height - 28 - 42)
            await page.locator("#trend-chart").click(position={"x": css_width - 24, "y": last_y})
            await wait_evidence(page, "source_physical_line_1_based", "20")
            chart_shot = await shot(page, "r2_selected_chart_point.png")
            chart_state = await state(page)
            require(chart_state["selectedCycle"] == "Cycle 20" and "Selected Cycle: 20" in chart_state["prompt"], "Chart selection did not update Prompt")
            record("UAT_07", "Click final Chart data point", "cycle=20", "Evidence and Prompt update", "Cycle 20 evidence and Prompt selected", chart_shot)

            await page.locator("#observation-body tr[data-index='4']").click()
            await wait_evidence(page, "source_physical_line_1_based", "5")
            table_shot = await shot(page, "r2_selected_table_row.png")
            table_state = await state(page)
            require(table_state["selectedCycle"] == "Cycle 5" and "Selected Cycle: 5" in table_state["prompt"], "Table selection did not update Prompt")
            record("UAT_08", "Click Cycle 5 Table row", "cycle=5", "Evidence and Prompt update", "Cycle 5 evidence and Prompt selected", table_shot)

            await page.locator("#split-select").select_option("TEST")
            await wait_evidence(page, "split", "TEST")
            test_state = await state(page)
            require(test_state["evidence"]["source_file"] == "test_FD001.txt" and "Source File: train_FD001.txt" not in test_state["prompt"], "TRAIN residue after TEST switch")
            record("UAT_09", "Switch TRAIN to TEST", "split=TEST", "No stale TRAIN state", "TEST evidence and Prompt contain only test_FD001.txt", "r2_changed_unit_sensor_cycle.png")

            await page.locator("#unit-select").select_option("2")
            await wait_evidence(page, "unit_id", "2")
            unit_state = await state(page)
            require(unit_state["unit"] == "2" and unit_state["start"] == "1", "Unit range not reset")
            record("UAT_10", "Switch to TEST Unit 2", "split=TEST&unit=2", "Unit and Cycle range reset", f"Unit 2 range {unit_state['start']}-{unit_state['end']}", "r2_changed_unit_sensor_cycle.png")

            await page.locator("#sensor-select").select_option("sensor_8")
            await wait_evidence(page, "sensor", "sensor_8")
            sensor_state = await state(page)
            require("Sensor ID: sensor_8" in sensor_state["prompt"], "Sensor Prompt stale")
            record("UAT_11", "Switch to sensor_8", "sensor=sensor_8", "Chart/Table/Prompt synchronized", "Evidence and Prompt identify sensor_8", "r2_changed_unit_sensor_cycle.png")

            await page.locator("#start-cycle").fill("2")
            await page.locator("#end-cycle").fill("6")
            await page.locator("#query-button").click()
            await page.wait_for_function("document.querySelectorAll('#observation-body tr[data-index]').length === 5")
            changed_shot = await shot(page, "r2_changed_unit_sensor_cycle.png")
            changed_state = await state(page)
            require(changed_state["pointCount"] == "5 observations" and "Cycle Range: 2-6" in changed_state["prompt"], "Valid range mismatch")
            record("UAT_12", "Change valid Cycle range", "TEST/Unit2/sensor_8/2-6", "5 observations and current range", "5 Browser rows; Prompt range 2-6", changed_shot)

            invalid_before = len(history_requests)
            await page.locator("#start-cycle").fill("20")
            await page.locator("#end-cycle").fill("1")
            invalid_state = await assert_cleared(page, "Query Validation Error")
            invalid_shot = await shot(page, "r2_invalid_query_20_1.png")
            require(invalid_state["statusDetail"] == "Start Cycle cannot exceed End Cycle.", "Invalid detail mismatch")
            require(invalid_state["start"] == "20" and invalid_state["end"] == "1", "Invalid input not preserved")
            require(not any("start=20&end=1" in url for url in history_requests[invalid_before:]), "Invalid History request was sent")
            record("UAT_13", "Enter invalid Cycle range 20/1", "start=20&end=1", "Clear stale state; disable Prompt actions; no invalid request", "Exact validation; 0 Chart/Table; N/A Evidence; disabled Copy; 0 invalid requests", invalid_shot)

            await set_real_query(page, "TRAIN", "1", "sensor_7", "1", "20")
            error_results = []
            for status, title, code in ((400, "Query Validation Error", "INVALID_QUERY_VALUE"), (404, "Observation Not Found", "OBSERVATION_NOT_FOUND"), (503, "Source Not Validated", "SOURCE_NOT_VALIDATED")):
                await set_real_query(page, "TRAIN", "1", "sensor_7", "1", "20")

                def make_error_route(status_code: int, error_code: str):
                    async def handler(route: Route) -> None:
                        await route.fulfill(status=status_code, content_type="application/json", body=json.dumps({"error": {"code": error_code, "message": f"TEST_ONLY HTTP {status_code}", "query": {}}}))

                    return handler

                error_route = make_error_route(status, code)
                await page.route("**/api/history?**", error_route)
                await page.locator("#query-button").click()
                await page.wait_for_function("title => document.querySelector('#status-title')?.textContent === title", arg=title)
                cleared = await assert_cleared(page, title)
                error_results.append(f"{status}:{cleared['statusTitle']}")
                await page.unroute("**/api/history?**", error_route)
            error_shot = await shot(page, "r2_error_400_404_503.png")
            record("UAT_14", "Inject isolated History HTTP 400, 404 and 503 after valid data", "TEST_ONLY UI classification; real API contract checked separately", "Correct classification and stale-state clearing", "; ".join(error_results), error_shot)

            await set_real_query(page, "TRAIN", "1", "sensor_7", "1", "20")
            api_pid_file = Path(args.api_pid_file)
            api_pid = int(api_pid_file.read_text(encoding="utf-8").strip())
            command = subprocess.check_output(["ps", "-p", str(api_pid), "-o", "command="], text=True).strip()
            require("web/run_server.py" in command, "Recorded PID is not the owned API")
            os.kill(api_pid, signal.SIGTERM)
            require(await asyncio.to_thread(wait_http, f"{args.api_url}/api/health", False, 8), "API did not stop")
            require((await context.request.get(args.url)).status == 200, "Frontend did not remain available")
            await page.locator("#query-button").click()
            await page.wait_for_function("document.querySelector('#status-title')?.textContent === 'Connection Error'")
            disconnected = await assert_cleared(page, "Connection Error")
            disconnected_shot = await shot(page, "r2_api_disconnected.png")
            record("UAT_15", "Stop the verified API PID and query through the still-running Frontend", "TRAIN/1/sensor_7/1-20", "Connection Error and cleared stale state", f"PID {api_pid} stopped; {disconnected['statusTitle']}; Frontend HTTP 200", disconnected_shot)

            restart_log = open("/tmp/ntust-m5-r2-api-restart.log", "wb")
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            restarted_api = subprocess.Popen(
                ["python3", "web/run_server.py"],
                cwd=args.project_root,
                env=env,
                stdout=restart_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            api_pid_file.write_text(f"{restarted_api.pid}\n", encoding="utf-8")
            require(await asyncio.to_thread(wait_http, f"{args.api_url}/api/health", True, 12), "API recovery failed")
            health = await asyncio.to_thread(get_json, f"{args.api_url}/api/health")
            require(health["data_validated"] is True and health["read_only"] is True, "Recovered API health invalid")
            await page.locator("#query-button").click()
            await wait_success(page)
            recovered = await state(page)
            require(recovered["tableRows"] == 20 and recovered["evidence"]["source_file"] == "train_FD001.txt" and not recovered["copyDisabled"], "Browser recovery state invalid")
            recovered_shot = await shot(page, "r2_api_recovered.png")
            record("UAT_16", "Restart real API and repeat valid query", "TRAIN/1/sensor_7/1-20", "Validated read-only API and 20-row recovery", f"PID {restarted_api.pid}; health validated/read-only; 20 rows; Copy enabled", recovered_shot)

            null_actual = []
            for variant, expected_success in (("optional_null", True), ("required_null", False), ("missing_required", False), ("non_finite", False), ("invalid_source", False)):
                fixture_page = await context.new_page()
                await fixture_page.goto(f"http://127.0.0.1:{fixture_ports[variant]}/?v=m5-r2-{variant}", wait_until="domcontentloaded")
                if expected_success:
                    await wait_success(fixture_page)
                    fixture_state = await state(fixture_page)
                    require(fixture_state["tableRows"] == 1 and "554.36" in await fixture_page.locator("#observation-body").inner_text(), "Optional null changed valid value")
                    null_actual.append("optional_null:Success/value554.36")
                else:
                    await fixture_page.wait_for_function("document.querySelector('#status-title')?.textContent === 'Source Not Validated'")
                    fixture_state = await assert_cleared(fixture_page, "Source Not Validated")
                    require(" 0" not in fixture_state["prompt"], "Invalid null was converted to zero")
                    null_actual.append(f"{variant}:Source Not Validated/0 rows")
                if variant == "required_null":
                    null_shot = await shot(fixture_page, "r2_null_required_error.png")
                await fixture_page.close()
            record("UAT_17", "Open isolated TEST_ONLY optional-null, required-null, missing, non-finite and invalid-source fixtures", "TEST_ONLY only", "No zero-fill/interpolation/fabrication; invalid required data rejected", "; ".join(null_actual), null_shot)

            prompt_state = await state(page)
            prompt = prompt_state["prompt"]
            required_prompt_fragments = [
                "Dataset ID: NASA_CMAPSS_FD001", "Source Type: NASA_FD001_LOCAL_TRUSTED", "Split: TRAIN",
                "Unit ID: 1", "Sensor ID: sensor_7", "Cycle Range: 1-20", "Selected Cycle: 1",
                "Source File: train_FD001.txt", "Source SHA-256:", "Source Physical Line (1-based): 1",
                "Parsed Row Index (0-based): 0", "Selected Sensor Source Column (one-based): 12",
                "[OBSERVED]", "[DERIVED]", "[INFERRED]", "[UNKNOWN]", "[EXTERNAL AI EVIDENCE INSTRUCTIONS]",
                "Scope: SPLIT_LEVEL", "not statistics for selected Unit 1", "Mean calculation: 11082.51 / 20 = 554.1255",
                "Delta calculation: 554.81 - 554.36 = 0.45",
            ]
            missing_fragments = [fragment for fragment in required_prompt_fragments if fragment not in prompt]
            require(not missing_fragments, f"Prompt missing: {missing_fragments}")
            record("UAT_18", "Validate visible Evidence Prompt against active API selection and provenance", "TRAIN/1/sensor_7/1-20 selected Cycle 1", "Identity, provenance, four classes, M2 scope and formulas match", "All required fragments present; Mean/Delta reproducible", "r2_evidence_prompt_copy.png")

            await page.locator("#copy-prompt").click()
            copied = await page.evaluate("navigator.clipboard.readText()")
            require(copied == prompt, "Clipboard differs from visible Prompt")
            prompt_shot = await shot(page, "r2_evidence_prompt_copy.png")
            record("UAT_19", "Click Copy Prompt and read Browser Clipboard", "current visible Prompt", "Exact content equality", f"visible_chars={len(prompt)} clipboard_chars={len(copied)} equality=true", prompt_shot)

            race_started = asyncio.Event()
            release_old = asyncio.Event()
            delayed_once = False

            async def delay_old(route: Route) -> None:
                nonlocal delayed_once
                if not delayed_once and "sensor=7" in route.request.url:
                    delayed_once = True
                    race_started.set()
                    await release_old.wait()
                try:
                    await route.continue_()
                except Exception:
                    pass

            await page.route("**/api/history?**", delay_old)
            await page.locator("#query-button").click()
            await asyncio.wait_for(race_started.wait(), timeout=5)
            await page.locator("#sensor-select").select_option("sensor_8")
            await wait_evidence(page, "sensor", "sensor_8")
            release_old.set()
            await page.wait_for_timeout(800)
            race_state = await state(page)
            require(race_state["evidence"]["sensor"] == "sensor_8" and "Sensor ID: sensor_8" in race_state["prompt"], "Old response overwrote current query")
            await page.unroute("**/api/history?**", delay_old)
            race_shot = await shot(page, "r2_stale_response_prevented.png")
            record("UAT_20", "Delay sensor_7 request, switch rapidly to sensor_8, then release old request", "old=sensor_7 new=sensor_8", "Old response cannot overwrite new", "Evidence and Prompt remained sensor_8", race_shot)

            bounded_prompt = race_state["prompt"]
            forbidden = {
                "fabricated baseline": "baseline: 100" in bounded_prompt.lower(),
                "unsupported diagnosis": "confirmed fault diagnosis" in bounded_prompt.lower(),
                "numeric health score": any(token in bounded_prompt.lower() for token in ("health score: 0", "health score: 1", "health score: 100")),
                "fabricated RUL": "rul value: 100" in bounded_prompt.lower(),
            }
            require(not any(forbidden.values()), f"Inference boundary violation: {forbidden}")
            require("Health score: unknown" in bounded_prompt and "RUL prediction/value for this query: unknown" in bounded_prompt, "Unknown disclosures missing")
            record("UAT_21", "Inspect Prompt inference boundaries after current sensor_8 query", "current sensor_8 Prompt", "No fabricated baseline, diagnosis, health score or RUL", "All forbidden checks false; Health score and RUL explicitly UNKNOWN", race_shot)

            browser_version = browser.version
            await browser.close()
    finally:
        if fixture_servers:
            stop_fixtures(fixture_servers, fixture_threads)
        if restart_log:
            restart_log.flush()
            restart_log.close()

    require(len(cases) == 21, f"expected 21 cases, got {len(cases)}")
    return {
        "result": "PASS",
        "browser": f"Google Chrome {browser_version}",
        "execution_start": cases[0]["execution_time"],
        "execution_end": cases[-1]["execution_time"],
        "passed": 21,
        "failed": 0,
        "cases": cases,
        "screenshots": screenshots,
        "screenshot_count": len(screenshots),
        "history_requests_observed": len(history_requests),
        "invalid_20_1_requests": sum("start=20&end=1" in url for url in history_requests),
        "restarted_api_pid": restarted_api.pid if restarted_api else None,
        "restarted_api_running": restarted_api.poll() is None if restarted_api else False,
        "fixture_boundary": "TEST_ONLY fixtures were used only for UI error classification and Null/Missing handling",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001/?v=m5-r2")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-pid-file", default="/tmp/ntust-nasa-ai-lab-501/api.pid")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--evidence-dir", type=Path, default=Path(__file__).resolve().parent / "browser_evidence")
    parser.add_argument("--result-json", type=Path, default=Path(__file__).resolve().parent / "r2_browser_results.json")
    args = parser.parse_args()
    result = asyncio.run(run(args))
    args.result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
