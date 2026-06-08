# Project: Instagram CLI Optimizer

## Architecture
- CLI Subcommands: login, logout, status, feed, profile, post, inbox, dm, interactive/tui
- TUI Main Menu: View Profile, Direct Messages, Logout, Exit
- Client manager handles instagrapi login / mock mode settings caching
- DM chat rendering with custom InlineClickable escape sequences bypassing rich.console hyperlink stripping
- Interactive DM command parsing for '/load'

## Code Layout
- `src/cli.py` - Command-line parsing and subcommand routing
- `src/interactive.py` - TUI rendering, inbox management, and chat room buffers
- `src/client_manager.py` - Client instantiation, session loading/saving
- `src/mock_client.py` - Simulates Instagram API calls and data structures
- `src/utils.py` - Shared utilities, text formatting, date handling, and ASCII art

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Infrastructure | E2E Testing Track: Implement test framework and E2E tests for Tiers 1-4 | None | DONE |
| 2 | Code Cleanup and Optimizations | Remove dead code/functions, optimize imports across all src/ files | None | DONE |
| 3 | TUI Layout & Username | Center ASCII banner & subtitle, fix @None username banner header issue | M2 | DONE |
| 4 | Clickable Media Links | Implement InlineClickable OSC 8 hyperlinks for DM messages | M2 | DONE |
| 5 | Chat Load Command | Ensure `/load` command works in interactive DMs | M2 | DONE |
| 6 | GitHub Repository Prep | Create gitignore, requirements.txt, GITHUB_SETUP.md, update README.md | None | DONE |
| 7 | E2E Test Suite Validation | Run and pass all E2E tests (Final Milestone Phase 1) | M1, M3, M4, M5, M6 | DONE |
| 8 | Adversarial Testing & Audit | Run Challenger (Tier 5) and Forensic Auditor to finalize verification (Final Milestone Phase 2) | M7 | DONE |

## Interface Contracts
### Client Manager ↔ TUI
- `get_client(use_mock)` -> `cl`
- `cl.username` caching / restoration protocol
- `cl.username_from_user_id(cl.user_id)` fallback
### UTILS ↔ TUI
- `get_banner()` -> Rich Group with centered banner & subtitle
- `format_message_text(msg)` -> custom renderable supporting OSC 8 links
