# Original User Request

## Initial Request — 2026-06-08T20:11:26+05:30

Optimize the Python Instagram terminal CLI codebase by cleaning up unnecessary code, refactoring/optimizing the implementation, fixing outstanding rendering/navigation bugs, and preparing the repository structure for sharing on GitHub.

Working directory: /home/akhil/declutter/Gemini_chats/instagram_cli
Integrity mode: development

## Requirements

### R1. Code Optimization and Cleanup
- Scan and remove dead, commented-out, or unused code from all files in the `src/` directory (e.g., the unused `browse_feed` function).
- Optimize imports, refactor redundant operations, and ensure clean pythonic code throughout the codebase.

### R2. Core Bug Fixes and Enhancements
- **ASCII Banner Layout**: Ensure the ASCII banner and the subtitle "★ Brainrot free instagram ★" are horizontally centered in the TUI.
- **Username Banner Resolution**: Resolve the "@None" username display in the banner header by checking cached session settings first, and falling back to calling `cl.username_from_user_id(cl.user_id)` if needed, persisting the result to session settings.
- **Clickable Media Links**: Formats Reels, Posts, and other hyperlinks in DMs as short clickable words (`Reel`, `Post`, `Link`) using terminal OSC 8 hyperlink sequences. Ensure the rendering pipeline outputs raw terminal escape sequences to standard stdout so that they are not stripped by `rich.console`.
- **Chat Load Command**: Implement a `/load` command in the interactive DM input prompt that increases the message limit by 15 and fetches older messages dynamically.

### R3. GitHub Repository Preparation
- Create a `.gitignore` file that excludes `venv/`, `__pycache__/`, local session files containing login cookies/secrets, and OS-specific files (e.g. `.DS_Store`).
- Create a `requirements.txt` file listing all external Python dependencies with pinned version numbers (e.g., `instagrapi`, `rich`, `questionary`, `requests`, `pillow`).
- Update `README.md` to document setup, configuration, and execution instructions.
- Create a `GITHUB_SETUP.md` markdown guide containing step-by-step terminal instructions for creating a GitHub repository, initializing git, staging/committing the files, and pushing the code.

## Verification Resources
- Run basic verification tests using the script at [test_dm_render.py](file:///home/akhil/.gemini/antigravity-cli/brain/79916be7-24b0-4de8-85ef-847821488ba5/scratch/test_dm_render.py) to check that OSC 8 escape sequences are correctly generated.
- Run the mock TUI using `./venv/bin/python3 -m src.cli -m interactive` to verify execution, layout centering, `/load` command, and username display.

## Acceptance Criteria

### Code Quality & Cleaning
- [ ] Unused function `browse_feed` and unused imports are removed from the source files.
- [ ] Code runs without syntax errors or runtime exceptions in mock mode.

### Layout & TUI Features
- [ ] The main menu banner and subtitle "★ Brainrot free instagram ★" are centered.
- [ ] Banner shows `@mock_user` (in mock mode) instead of `@None`.
- [ ] Typing `/load` inside a DM session successfully triggers loading of older messages.
- [ ] In direct messages, media links render as short words (`Reel`, `Post`, `Link`) and are formatted using valid OSC 8 terminal hyperlink sequences.

### GitHub Preparation
- [ ] `.gitignore` exists and excludes virtual environment directories, cache directories, and JSON session configurations.
- [ ] `requirements.txt` exists and lists the necessary external Python dependencies.
- [ ] `GITHUB_SETUP.md` exists and contains instructions for creating and pushing to a remote repository.
