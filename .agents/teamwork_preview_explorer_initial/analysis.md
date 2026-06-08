# Python Instagram Terminal CLI - Codebase Investigation Report

This report presents a detailed read-only codebase analysis of the Python Instagram terminal CLI project located at `/home/akhil/declutter/Gemini_chats/instagram_cli`.

---

## 1. Goal 1: Unused, Dead, and Commented-Out Code

The following sections identify all occurrences of unused imports, unused functions, dead classes, and obsolete functions across all files in the `src/` directory.

### A. `src/interactive.py`
1. **`browse_feed(cl)` Function** (Lines 88–196):
   - **Details**: This function retrieves and displays the user's home timeline feed. However, it is never called or imported anywhere in the application. The TUI main action menu (defined starting at line 59) only exposes "View Profile", "Direct Messages", "Logout", and "Exit".
   - **Line range**:
     ```python
     88: def browse_feed(cl):
     89:     """Retrieves and displays the home timeline feed post-by-post."""
     ...
     196: 
     ```
2. **`upload_photo_interactive(cl)` Function** (Lines 738–769):
   - **Details**: This interactive method for uploading photos is defined but never invoked. It is completely dead code.
   - **Line range**:
     ```python
     738: def upload_photo_interactive(cl):
     ...
     769: 
     ```
3. **Unused Imports**:
   - **`from datetime import datetime`** (Line 2): Imported at the top level of the file but not used globally. It is shadowed by a local `from datetime import datetime, timezone` import at line 420.
   - **`from rich.columns import Columns`** (Line 6): Imported from `rich.columns` but never used.
   - **`from instagrapi.exceptions import LoginRequired`** (Line 9): Imported from `instagrapi.exceptions` but never used.

---

### B. `src/utils.py`
1. **`detect_graphics_protocol()` Function** (Lines 116–152):
   - **Details**: Detects terminal capabilities (e.g., Kitty, iTerm2). It is only called inside `get_ansi_thumbnail()`, which is itself dead code.
2. **`get_ansi_thumbnail(url: str, width: int = 30)` Function** (Lines 154–237):
   - **Details**: Downloads and converts media images into ANSI block/terminal graphic characters. It is completely unused by the rest of the application.
3. **`THUMBNAIL_CACHE = {}` Dictionary** (Line 114):
   - **Details**: Used only by `get_ansi_thumbnail()`.
4. **`_extract_url_from_image_versions(image_versions2)` Function** (Lines 239–267):
   - **Details**: Extracts URL candidates from nested structures. Never called.
5. **`RawEscape` Class** (Lines 269–282):
   - **Details**: Custom class for yielding control segments to Rich. Only used by `_format_ansi_art()`.
6. **`_format_ansi_art(t, ansi_art)` Function** (Lines 300–309):
   - **Details**: Helper to wrap ANSI art. Never called.

---

### C. `src/cli.py`
1. **Unused Imports**:
   - **`from pathlib import Path`** (Line 4): Imported but unused.
   - **`from datetime import datetime`** (Line 5): Imported but unused.
   - **`clear_screen`** and **`get_banner`** (Line 7): Imported from `src.utils` but never used in CLI command dispatches.

---

### D. `src/client_manager.py`
1. **Unused Imports**:
   - **`import os`** (Line 1): Imported but unused.
   - **`import sys`** (Line 2): Imported but unused.
   - **`from instagrapi.exceptions import ... LoginRequired`** (Line 5): `LoginRequired` is imported but unused.

---

### E. `src/mock_client.py`
1. **Unused Imports**:
   - **`Dict`** and **`Union`** (Line 5): Imported from `typing` but unused.

---

## 2. Goal 2: ASCII Banner & Subtitle Definition and Rendering

### A. Location
* **Definition**: `src/utils.py` inside `get_banner()` (lines 30–69).
* **Rendering**: `src/interactive.py` inside `run_tui()` (lines 25 and 56) using `console.print(get_banner())`.

### B. Centering Mechanism
The banner is centered horizontally within the terminal using Rich's `Align.center()` wrapper inside a `Group`:
```python
    g = Group(
        Align.center(Text(banner_text_padded, style="bold #C13584")),
        Align.center(Text("★ Brainrot free instagram ★", style="bold #E1306C"))
    )
```
Before aligning, the ASCII art block is normalized by padding all lines to the maximum line length (`max_len`):
```python
    lines = banner_text.splitlines()
    max_len = max(len(l) for l in lines) if lines else 0
    padded_lines = [l.ljust(max_len) for l in lines]
    banner_text_padded = "\n".join(padded_lines)
```
This guarantees that the ASCII art structure does not skew or break when `Align.center()` is executed relative to the terminal's boundary.

---

## 3. Goal 3: Username Banner Header Resolution & "@None" Fix

### A. Location
* **TUI Resolution Loop**: `src/interactive.py` (lines 29–53)
* **Client Manager Session Load**: `src/client_manager.py` (lines 114–125)

### B. How the `@None` Occurs
1. **Session Restore**: When loading a session, `client_manager.py` loads the settings JSON (`session.json`). If the session file lacks a valid `"username"` key or has `"username": "None"`, the client's `cl.username` property is set to Python `None` or the string `"None"`.
2. **Resolution failure**: In `interactive.py`, the resolution logic checks:
   `if not getattr(cl, "username", None) or cl.username == "None":`
   If the session file indeed has `"username": "None"`, or if fetching fails, and the subsequent rate-limited API call `cl.username_from_user_id(cl.user_id)` raises an exception or returns `None`/`"None"`, the variable `cl.username` retains the string value `"None"`.
3. **Fallback evaluation**: The line `my_username = cl.username or "Logged In"` evaluates to `"None"` because `"None"` is a non-empty, truthy string in Python.
4. **Rendering**: The TUI prints `Logged in as: @None` (lines 56–57).

### C. Proposed Robust Fix & Fallback Implementation
To resolve this, we can replace lines 29–53 in `src/interactive.py` with a robust resolver that explicitly checks for null/string variations of `"None"` and uses `cl.username_from_user_id` with cached settings as fallback:

```python
    # Robustly resolve own username to avoid rendering @None
    my_username = "Logged In"
    try:
        current_username = getattr(cl, "username", None)
        is_invalid = not current_username or str(current_username).strip().lower() in ("none", "null", "")
        
        if is_invalid:
            from src.client_manager import get_session_path, save_client_settings
            import json
            session_path = get_session_path(use_mock)
            
            # 1. Attempt cached fallback first
            if session_path.exists():
                try:
                    with open(session_path, "r") as f:
                        data = json.load(f)
                    cached_val = data.get("username")
                    if cached_val and str(cached_val).strip().lower() not in ("none", "null", ""):
                        cl.username = str(cached_val).strip()
                except Exception:
                    pass
            
            # 2. Attempt API fallback if still invalid
            current_username = getattr(cl, "username", None)
            is_still_invalid = not current_username or str(current_username).strip().lower() in ("none", "null", "")
            if is_still_invalid and getattr(cl, "user_id", None):
                try:
                    fetched = cl.username_from_user_id(cl.user_id)
                    if fetched and str(fetched).strip().lower() not in ("none", "null", ""):
                        cl.username = str(fetched).strip()
                        # Save the updated username back to the session cache
                        if session_path.exists():
                            save_client_settings(cl, session_path, cl.username)
                except Exception:
                    pass

        # Final check for string representations
        resolved = getattr(cl, "username", None)
        if resolved and str(resolved).strip().lower() not in ("none", "null", ""):
            my_username = str(resolved).strip()
        else:
            my_username = "Logged In"
    except Exception:
        my_username = "Logged In"
```

---

## 4. Goal 4: DM Rendering Logic & Clickable Link OSC 8 Escape Sequences

### A. Location
* **Inbox Message Loop**: `src/interactive.py` inside `interactive_chat()` (lines 536–606)
* **Message Formatter**: `src/utils.py` inside `format_message_text()` (lines 311–454)

### B. Current Formatting of Reels, Posts, and Links
* **Reels (clip)** (Lines 351–383): If the message contains a shared Reel, it formats the text as `🎬 Shared Reel [from @creator]`. If a `code` exists, it appends a link using Rich's native format:
  `link_text.append("Reel", style="bold #405DE6 link https://instagram.com/reel/{code}")`
* **Posts (media_share)** (Lines 384–415): Formats the text as `📸 Shared Post [from @creator]`. If a `code` exists, it appends:
  `link_text.append("Post", style="bold #405DE6 link https://instagram.com/p/{code}")`
* **External Links (xma_share)** (Lines 417–440): Formats the text as `🔗 Title`. If a URL exists, it appends:
  `link_text.append("Link", style="bold #405DE6 link {display_link}")`

### C. Rich Console Stripping & Enforcing Clickable Links via OSC 8
By default, `rich.console.Console` detects whether the terminal supports hyperlinks. If the detection fails or returns false (common inside various virtual terminals or TMUX environments), Rich strips the `link` style and prints only the plain label text ("Reel", "Post", "Link").

To bypass Rich's built-in stripping and force raw terminal-compliant OSC 8 escape sequences without breaking console padding, text wrapping, and width calculations, we can wrap the link in a custom Rich-compatible inline renderable:

```python
class InlineClickable:
    """
    Custom inline renderable that outputs terminal OSC 8 hyperlinks.
    Uses control=True on the start and end escape segments so that Rich does
    not strip them and does not count them towards layout width calculations.
    """
    def __init__(self, prefix: str, label: str, url: str, style: str = ""):
        self.prefix = prefix
        self.label = label
        self.url = url
        self.style = style

    def __rich_console__(self, console, options):
        from rich.segment import Segment
        from rich.style import Style

        # Output the prefix (e.g. "🔗 ")
        yield Segment(self.prefix)

        # Output the OSC 8 start sequence as a zero-width control segment
        osc8_start = f"\x1b]8;;{self.url}\x1b\\"
        yield Segment(osc8_start, control=True)

        # Output the visible link label with proper style applied
        style_obj = console.get_style(self.style) if self.style else Style.null()
        yield Segment(self.label, style=style_obj)

        # Output the OSC 8 end sequence as a zero-width control segment
        osc8_end = "\x1b]8;;\x1b\\"
        yield Segment(osc8_end, control=True)
```

In `format_message_text()` in `src/utils.py`, we can return a `Group` containing the main panel text and an `InlineClickable` instance:
* **Reels**: `InlineClickable("🔗 ", "Reel", f"https://instagram.com/reel/{code}", "bold #405DE6")`
* **Posts**: `InlineClickable("🔗 ", "Post", f"https://instagram.com/p/{code}", "bold #405DE6")`
* **Links**: `InlineClickable("🔗 ", "Link", display_link, "bold #405DE6")`

---

## 5. Goal 5: DM Chat Commands & `/load` Limit Command

### A. Location
* **TUI Chat Input Loop**: `src/interactive.py` inside `chat_loop_async()` (lines 640–684)

### B. Command Handling & `/load` Mechanics
1. **Input Reader**: The prompt uses `questionary.text().ask_async()` with custom keybindings.
2. **Commands Dispatcher**: Once input is returned, it is evaluated (lines 652–684).
3. **`/load` Command (Lines 670–680)**:
   - When the user enters `/load`, the input block catches the command case-insensitively (`message_text.lower() == "/load"`):
     ```python
     670:                 if message_text.lower() == "/load":
     671:                     limit_container[0] += 15
     672:                     clear_screen()
     673:                     console.print(f"[info]Loading older messages (limit: {limit_container[0]})...[/info]")
     674:                     try:
     675:                         new_thread = await asyncio.to_thread(cl.direct_thread, thread_id, amount=limit_container[0])
     676:                         thread_container[0] = new_thread
     677:                     except Exception as e:
     678:                         console.print(f"[error]Failed to load older messages: {e}[/error]")
     679:                         await asyncio.sleep(1.5)
     680:                     continue
     ```
   - **Limit Tracking**: The message retrieval limit is stored inside a mutable list `limit_container = [15]` (initialized at line 512).
   - **Mechanics**:
     * The limit is incremented by 15: `limit_container[0] += 15`.
     * The background thread fetches the thread history using the new limit: `cl.direct_thread(thread_id, amount=limit_container[0])`.
     * The local state container `thread_container[0]` is updated with the fetched thread.
     * The loop is restarted (`continue`), triggering a complete redraw of the chat console displaying the expanded history.
