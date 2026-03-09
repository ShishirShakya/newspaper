"""
Create a persistent browser context with anti-detection options to reduce
"not a robot" / CAPTCHA challenges on newspapers.com and similar sites.
"""

import asyncio
import threading

# Realistic Chrome on Windows (avoids "Headless Chrome" detection)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


async def create_persistent_context(playwright, user_data_dir: str):
    """
    Launch a persistent Chromium context with:
    - Automation flag disabled (--disable-blink-features=AutomationControlled)
    - Realistic user-agent
    - playwright-stealth applied (with UA override for persistent context)
    """
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        viewport={"width": 1280, "height": 800},
        args=["--disable-blink-features=AutomationControlled"],
        user_agent=USER_AGENT,
        locale="en-US",
    )
    try:
        from playwright_stealth import Stealth
        stealth = Stealth(navigator_user_agent_override=USER_AGENT)
        await stealth.apply_stealth_async(context)
    except Exception:
        pass
    return context


async def wait_for_enter_or_timeout(timeout_sec: int) -> None:
    """
    Keep the browser session open until the user presses Enter in the terminal,
    or until timeout_sec (e.g. 600 = 10 minutes). Use when login/CAPTCHA is required.
    """
    done = asyncio.Event()
    loop = asyncio.get_event_loop()

    def wait_enter() -> None:
        input("Press Enter when you have finished logging in (browser will then close)... ")
        loop.call_soon_threadsafe(done.set)

    t = threading.Thread(target=wait_enter, daemon=True)
    t.start()
    try:
        await asyncio.wait_for(done.wait(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        print("Login wait timed out after {} minutes.".format(timeout_sec // 60))
