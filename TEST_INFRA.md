# TEST_INFRA — E2E Test Infrastructure

This document details the testing architecture, environment setup, and isolation/mocking strategies for the Python Instagram terminal CLI E2E test suite.

## 1. Architectural Layout
The test suite is structured to test the application's CLI and TUI commands without making live API calls or polluting the developer's local state.
- **Test Suite**: Located in `tests/test_suite.py` containing 49 test cases organized in hierarchical test classes.
- **Runner**: Located in `run_tests.sh` which executes the test suite using the virtual environment's Python (`./venv/bin/python3 -m unittest tests/test_suite.py -v`).

## 2. Mocking & Isolation Strategy

### A. HOME Directory Redirection
To protect the user's real session cache (`~/.config/instagram_cli/session.json`), the test suite redirects `HOME` to a temporary directory at import time:
```python
temp_home = tempfile.mkdtemp()
os.environ["HOME"] = temp_home
```
This forces all codebase modules (such as `client_manager.py`) to resolve standard paths (like `Path.home()`) to our isolated temp space. The temp directory is cleaned up upon test suite termination.

### B. Questionary Prompt Mocking
The interactive Terminal User Interface (TUI) relies on `questionary` for menu selection and text inputs. Since these would block stdin in automated test runs, a `MockQuestionary` helper class is injected to intercept calls:
- **`select`**: Returns pre-programmed menu choices sequentially, defaulting to `"❌ Exit"` when exhausted.
- **`text`**: Returns pre-programmed strings, defaulting to `"/exit"` to guarantee that chat/search loops always terminate.
- **`press_any_key_to_continue`**: Instantly returns `None` to prevent stalling the test execution.

### C. Truecolor Rendering for Link Assertions
To verify that Feature 2 (DM Rendering) outputs compliant OSC 8 hyperlinks, the test console is configured to enforce truecolor output:
```python
c = Console(force_terminal=True, color_system="truecolor")
```
This forces Rich to output raw OSC 8 escape codes (`\x1b]8;...`) even within terminal-less CI environments, allowing test assertions to verify link structure using raw string search.

### D. Workaround for Scoping Bug in Mock Client
The mock client (`src/mock_client.py`) has a NameError scope bug inside `media_comment()` due to the `text = text` assignment inside a local class body. The test suite patches `MockClient.media_comment` at the base class level to catch comments, increment counts, and return a mock Comment object safely without modifying the source files.

## 3. Test Cases (Tiers 1-4)
- **Tier 1 (Feature Coverage)**: Validates standard functionality of Session Management, DM Rendering, Interactive Chat, and Profile TUI.
- **Tier 2 (Boundary & Corner Cases)**: Validates authentication failures, invalid verification inputs, corrupt settings file unlinks, missing files fallback, and API failures.
- **Tier 3 (Cross-Feature Combinations)**: Evaluates interactions, such as session expiration mid-chat, profile views leading to messaging, relogin context switches, and cache deletions.
- **Tier 4 (Real-world Application Scenarios)**: Simulates end-to-end user flows representing complete user journeys.
