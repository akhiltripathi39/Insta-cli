## 2026-06-08T14:47:24Z
You are the E2E Testing Track Worker. Your objective is to design and implement a comprehensive, opaque-box E2E test suite for the Python Instagram terminal CLI, covering Tiers 1-4.
Please follow these instructions:
1. We have identified 4 core features:
   - F1: Session Management (login/logout/status/settings cache)
   - F2: Direct Message Rendering (custom InlineClickable OSC 8 hyperlinks for Reel, Post, Link)
   - F3: DM Interactive Chat & /load command (limit incrementing, history loading)
   - F4: Profile View & TUI Main Menu (banner and subtitle centering, resolving "@None" username display)
2. Create a test suite in a file `tests/test_suite.py` containing at least 49 test cases matching the 4 tiers:
   - Tier 1: Feature Coverage (>=20 test cases, 5 per feature)
   - Tier 2: Boundary & Corner Cases (>=20 test cases, 5 per feature)
   - Tier 3: Cross-Feature Combinations (>=4 test cases covering feature interactions)
   - Tier 4: Real-world Application Scenarios (>=5 test cases exercising multi-feature flows)
3. The tests should invoke the CLI in mock mode (using the -m / --mock option) or import the codebase modules and run them with mock input/output redirection. You can execute CLI commands as subprocesses (e.g. `./venv/bin/python3 -m src.cli -m ...`).
4. Ensure you write the tests to `tests/test_suite.py`.
5. Create a test runner script `run_tests.sh` or a python equivalent to run the full test suite.
6. Verify your test cases by running them, checking their output, and documenting the test commands and results in your handoff report.
7. Once the tests are fully operational and verified, publish `TEST_READY.md` and `TEST_INFRA.md` in the project root according to the templates in the Project Pattern instructions.
8. NEVER modify the application source code files in `src/` directly — only write files in `tests/` and document your work.
9. Report back by writing a Handoff Report to `/home/akhil/declutter/Gemini_chats/instagram_cli/.agents/teamwork_preview_worker_e2e/handoff.md` and sending me a message.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your working directory is /home/akhil/declutter/Gemini_chats/instagram_cli/.agents/teamwork_preview_worker_e2e
Your identity is teamwork_preview_worker_e2e.
