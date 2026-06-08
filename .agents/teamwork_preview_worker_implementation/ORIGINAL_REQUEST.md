## 2026-06-08T14:54:25Z
You are the Implementation Worker. Your goal is to implement Milestones 2-6 as specified in the project scope:
1. **Milestone 2 (Code Cleanup and Optimizations)**:
   - Remove unused function `browse_feed` in `src/interactive.py`.
   - Remove unused function `upload_photo_interactive` in `src/interactive.py`.
   - Remove unused imports `from datetime import datetime`, `from rich.columns import Columns`, and `from instagrapi.exceptions import LoginRequired` in `src/interactive.py`.
   - Remove unused functions `detect_graphics_protocol`, `get_ansi_thumbnail`, `_extract_url_from_image_versions`, and `_format_ansi_art` in `src/utils.py`.
   - Remove unused imports/variables: `THUMBNAIL_CACHE`, `RawEscape` in `src/utils.py`.
   - Remove unused imports `from pathlib import Path`, `from datetime import datetime`, and unused imports `clear_screen`, `get_banner` in `src/cli.py`.
   - Remove unused imports `import os`, `import sys`, `LoginRequired` in `src/client_manager.py`.
   - Remove unused imports `Dict`, `Union` in `src/mock_client.py`.

2. **Milestone 3 (TUI Layout & Username Banner)**:
   - Centering of the banner and the subtitle "★ Brainrot free instagram ★" is already done in `utils.py:get_banner()`. Ensure that they are centered horizontally in the terminal and no layout problems occur.
   - Fix the "@None" username display in the banner header by checking cached session settings first, and falling back to calling `cl.username_from_user_id(cl.user_id)` if needed, persisting the result to session settings. Replace lines 29-53 in `src/interactive.py` with robust resolution code that handles null/string variations of "None" or "null".

3. **Milestone 4 (Clickable Media Links)**:
   - Formats Reels, Posts, and other hyperlinks in DMs as short clickable words (`Reel`, `Post`, `Link`) using terminal OSC 8 hyperlink sequences.
   - Implement an `InlineClickable` renderable class in `src/utils.py` that yields the start and end OSC 8 hyperlink escape sequences with `control=True` segments inside `__rich_console__`, preventing `rich.console` from stripping them.
   - Use `InlineClickable` in `format_message_text` in `src/utils.py` for shared Reels, Posts, and external Link objects.

4. **Milestone 5 (Chat Load Command & Comment Bug)**:
   - Ensure the `/load` command works in interactive DMs.
   - Fix the `NameError: name 'text' is not defined` bug inside `MockClient.media_comment` in `src/mock_client.py` (lines 337-340) by passing the text to an `__init__` method of the Comment class or equivalent scope-safe definition.

5. **Milestone 6 (GitHub Prep)**:
   - Create a `.gitignore` file that excludes `venv/`, `__pycache__/`, local session files containing login cookies/secrets (e.g. `session.json` or `*session.json`), and OS-specific files (e.g. `.DS_Store`).
   - Create a `requirements.txt` file listing all external Python dependencies with pinned version numbers (e.g., `instagrapi`, `rich`, `questionary`, `requests`, `pillow`). You can check their versions from the environment if needed.
   - Update `README.md` to document setup, configuration, and execution instructions.
   - Create a `GITHUB_SETUP.md` markdown guide containing step-by-step terminal instructions for creating a GitHub repository, initializing git, staging/committing the files, and pushing the code.

6. **Testing & Verification**:
   - Run the E2E test suite `./run_tests.sh` to ensure all 49 tests pass successfully.
   - Ensure your code does not introduce syntax or runtime errors.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your handoff report to `/home/akhil/declutter/Gemini_chats/instagram_cli/.agents/teamwork_preview_worker_implementation/handoff.md` and send me a message when done.
Your working directory is /home/akhil/declutter/Gemini_chats/instagram_cli/.agents/teamwork_preview_worker_implementation
Your identity is teamwork_preview_worker_implementation.
