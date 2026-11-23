#!/usr/bin/env python3
"""R1 browser interaction regression for invalid Cycle-range state handling."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Page, Route, async_playwright


INVALID_PROMPT = "No valid prompt. Load a successful query and select an observation."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def wait_for_success(page: Page) -> None:
    await page.locator("#status-title").wait_for(state="visible")
    await page.wait_for_function("document.querySelector('#status-title')?.textContent === 'Success'")


async def valid_query(page: Page, start: str = "1", end: str = "20") -> None:
    await page.locator("#start-cycle").fill(start)
    await page.locator("#end-cycle").fill(end)
    await page.locator("#query-button").click()
    await wait_for_success(page)


async def assert_invalid_state(page: Page, message: str) -> None:
    require(await page.locator("#status-title").text_content() == "Query Validation Error", "error title")
    require(await page.locator("#status-detail").text_content() == message, "error detail")
    require(await page.locator("#validation-message").text_content() == message, "validation message")
    require(await page.locator("#point-count").text_content() == "0 observations", "chart count cleared")
    require(await page.locator("#chart-empty").is_visible(), "chart empty state visible")
    require(await page.locator("#observation-body tr[data-index]").count() == 0, "table rows cleared")
    require(await page.locator("[data-evidence]").all_text_contents() == ["N/A"] * 11, "evidence cleared")
    require(await page.locator("#selected-cycle").text_content() == "No point", "selection cleared")
    require(await page.locator("#prompt-output").text_content() == INVALID_PROMPT, "prompt cleared")
    require(await page.locator("#generate-prompt").is_disabled(), "prompt generation disabled")
    require(await page.locator("#copy-prompt").is_disabled(), "copy disabled")


async def run(url: str, evidence_dir: Path) -> dict[str, object]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    history_requests: list[str] = []
    history_failures: list[str] = []
    results: list[dict[str, str]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        await context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
        page = await context.new_page()
        page.on("request", lambda request: history_requests.append(request.url) if "/api/history?" in request.url else None)
        page.on("requestfailed", lambda request: history_failures.append(request.url) if "/api/history?" in request.url else None)

        await page.goto(url, wait_until="domcontentloaded")
        await wait_for_success(page)
        require(await page.locator("#observation-body tr[data-index]").count() == 20, "initial rows")
        require(not await page.locator("#copy-prompt").is_disabled(), "initial copy enabled")
        await page.screenshot(path=evidence_dir / "r1_initial_valid_query.png", full_page=True)

        await page.locator("#start-cycle").fill("20")
        await page.locator("#start-cycle").press("Tab")
        await page.wait_for_timeout(100)
        requests_before_invalid = len(history_requests)
        await page.locator("#end-cycle").fill("1")
        await assert_invalid_state(page, "Start Cycle cannot exceed End Cycle.")
        require(await page.locator("#start-cycle").input_value() == "20", "invalid Start preserved")
        require(await page.locator("#end-cycle").input_value() == "1", "invalid End preserved")
        require(len(history_requests) == requests_before_invalid, "invalid query sent a History request")
        require(
            not any("start=20&end=1" in request for request in history_requests),
            "network log contains the invalid 20/1 query",
        )
        await page.screenshot(path=evidence_dir / "r1_invalid_20_1_cleared.png", full_page=True)
        await page.locator(".prompt-panel").screenshot(path=evidence_dir / "r1_invalid_prompt_disabled.png")
        results.extend(
            [
                {"id": "R1_01", "status": "PASS", "detail": "old result, chart, table, and evidence cleared"},
                {"id": "R1_02", "status": "PASS", "detail": "prompt invalidated; Generate and Copy disabled"},
                {"id": "R1_03", "status": "PASS", "detail": "History request count unchanged for invalid 20/1"},
            ]
        )

        await valid_query(page)
        require(await page.locator("#observation-body tr[data-index]").count() == 20, "recovery rows")
        require(await page.locator("[data-evidence='source_file']").text_content() == "train_FD001.txt", "recovery evidence")
        require(not await page.locator("#copy-prompt").is_disabled(), "recovery copy enabled")
        await page.screenshot(path=evidence_dir / "r1_corrected_valid_query.png", full_page=True)
        results.append({"id": "R1_05", "status": "PASS", "detail": "corrected 1/20 query restored current evidence and prompt"})

        invalid_cases = [
            ("1.5", "20", "Cycles must be positive integers."),
            ("0", "20", "Cycles must be positive integers."),
            ("-1", "20", "Cycles must be positive integers."),
            ("1", "999999", "Cycle range is outside the selected Unit."),
            ("", "20", "Cycles must be positive integers."),
        ]
        invalid_request_count = len(history_requests)
        for start, end, message in invalid_cases:
            await valid_query(page)
            invalid_request_count = len(history_requests)
            await page.locator("#start-cycle").fill(start)
            await page.locator("#end-cycle").fill(end)
            await assert_invalid_state(page, message)
            require(len(history_requests) == invalid_request_count, f"invalid History request for {start}/{end}")
        results.append({"id": "R1_06", "status": "PASS", "detail": "non-integer, zero, negative, outside, and empty inputs fail closed"})

        await valid_query(page)
        race_started = asyncio.Event()
        release_race = asyncio.Event()
        race_enabled = True

        async def delay_history(route: Route) -> None:
            nonlocal race_enabled
            if race_enabled and "/api/history?" in route.request.url:
                race_enabled = False
                race_started.set()
                await release_race.wait()
            try:
                await route.continue_()
            except Exception:
                # AbortController may close the intercepted request before release.
                pass

        await page.route("**/api/history?**", delay_history)
        await page.locator("#query-button").click()
        await asyncio.wait_for(race_started.wait(), timeout=5)
        await page.locator("#start-cycle").fill("20")
        await page.locator("#end-cycle").fill("1")
        release_race.set()
        await page.wait_for_timeout(1000)
        await assert_invalid_state(page, "Start Cycle cannot exceed End Cycle.")
        await page.screenshot(path=evidence_dir / "r1_pending_request_cancelled.png", full_page=True)
        results.append({"id": "R1_04", "status": "PASS", "detail": "pending History request could not restore stale success"})
        await page.unroute("**/api/history?**")

        await valid_query(page)
        await page.locator("#split-select").select_option("TEST")
        await wait_for_success(page)
        require(await page.locator("[data-evidence='split']").text_content() == "TEST", "TEST selector")
        unit_options = await page.locator("#unit-select option").count()
        require(unit_options > 1, "Unit selector options")
        await page.locator("#unit-select").select_option(index=1)
        await wait_for_success(page)
        await page.locator("#sensor-select").select_option("sensor_8")
        await wait_for_success(page)
        require(await page.locator("[data-evidence='sensor']").text_content() == "sensor_8", "Sensor selector")
        visible_prompt = await page.locator("#prompt-output").text_content()
        await page.locator("#copy-prompt").click()
        copied = await page.evaluate("navigator.clipboard.readText()")
        require(copied == visible_prompt, "clipboard content")
        results.append({"id": "R1_07", "status": "PASS", "detail": "Split, Unit, Sensor, valid query, and Copy remain operational"})

        version = browser.version
        await browser.close()

    return {
        "result": "PASS",
        "browser": f"Google Chrome {version}",
        "tests": results,
        "passed": len(results),
        "failed": 0,
        "history_request_count": len(history_requests),
        "history_request_failures": len(history_failures),
        "invalid_20_1_history_requests": 0,
        "screenshots": sorted(path.name for path in evidence_dir.glob("r1_*.png")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001/?v=m5-r1")
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "m5" / "browser_evidence",
    )
    args = parser.parse_args()
    result = asyncio.run(run(args.url, args.evidence_dir))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
