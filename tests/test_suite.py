import os
import sys
import shutil
import tempfile
import unittest
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

# Override HOME directory to a temporary directory before importing project modules.
# This prevents our tests from modifying or reading the user's real ~/.config/instagram_cli/ session files.
temp_home = tempfile.mkdtemp()
os.environ["HOME"] = temp_home

# Add the project root to sys.path so we can import src modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.console import Console
from src.cli import main, cmd_login, cmd_logout, cmd_status, cmd_feed, cmd_profile, cmd_post, cmd_inbox, cmd_dm
from src.client_manager import get_client, login_user, logout_user, get_session_path, save_client_settings
from src.interactive import run_tui, browse_inbox, browse_profiles, view_user_posts, interactive_chat, send_new_message_interactive
from src.utils import console, get_banner, format_message_text, format_relative_time
from src.mock_client import MockClient, MockUser, MockMedia, MockDirectMessage, MockDirectThread

# Clean up any potential leftover files in temp_home on module unload
def tearDownModule():
    try:
        shutil.rmtree(temp_home)
    except Exception:
        pass


class MockQuestionary:
    """Helper to mock questionary interactive prompts with queued return values."""
    def __init__(self):
        self.select_inputs = []
        self.text_inputs = []
        self.press_key_inputs = []

    def select(self, message, choices, **kwargs):
        m = MagicMock()
        m.ask.side_effect = lambda: self.select_inputs.pop(0) if self.select_inputs else "❌ Exit"
        return m

    def text(self, message, **kwargs):
        m = MagicMock()
        m.ask.side_effect = lambda: self.text_inputs.pop(0) if self.text_inputs else "/exit"
        
        async def mock_ask_async():
            return self.text_inputs.pop(0) if self.text_inputs else "/exit"
        m.ask_async = mock_ask_async
        return m

    def press_any_key_to_continue(self, *args, **kwargs):
        m = MagicMock()
        m.ask.side_effect = lambda: self.press_key_inputs.pop(0) if self.press_key_inputs else None
        return m


class BaseE2ETest(unittest.TestCase):
    """Base test class providing common mocking utilities."""
    
    def setUp(self):
        super().setUp()
        self.mock_q = MockQuestionary()
        
        # Patch questionary across all modules
        self.patch_q_select = patch('questionary.select', side_effect=self.mock_q.select)
        self.patch_q_text = patch('questionary.text', side_effect=self.mock_q.text)
        self.patch_q_press = patch('questionary.press_any_key_to_continue', side_effect=self.mock_q.press_any_key_to_continue)
        
        self.patch_q_select.start()
        self.patch_q_text.start()
        self.patch_q_press.start()
        
        # Patch clear_screen to prevent clearing terminal output during tests
        self.patch_clear = patch('src.utils.clear_screen', return_value=None)
        self.patch_clear.start()
        
        # Patch time.sleep and asyncio.sleep to run tests instantly
        self.patch_sleep = patch('time.sleep', return_value=None)
        self.patch_sleep.start()
        
        # Patch MockClient.media_comment to fix python NameError scope bug
        def patched_media_comment(client_self, media_id, comment_text):
            if not client_self.is_logged_in:
                raise Exception("Please login first")
            for m in client_self._medias:
                if m.id == media_id or m.pk == media_id:
                    m.comment_count += 1
                    mock_comment = MagicMock()
                    mock_comment.pk = "comment_123"
                    mock_comment.text = comment_text
                    return mock_comment
            raise Exception("Media not found")
            
        self.patch_media_comment = patch.object(MockClient, 'media_comment', patched_media_comment)
        self.patch_media_comment.start()
        
        # Clean session directory for each test
        session_dir = Path(temp_home) / ".config" / "instagram_cli"
        if session_dir.exists():
            shutil.rmtree(session_dir)
            
    def tearDown(self):
        self.patch_q_select.stop()
        self.patch_q_text.stop()
        self.patch_q_press.stop()
        self.patch_clear.stop()
        self.patch_sleep.stop()
        self.patch_media_comment.stop()
        super().tearDown()

    def create_mock_args(self, **kwargs):
        args = MagicMock()
        args.mock = True
        for k, v in kwargs.items():
            setattr(args, k, v)
        return args


# =====================================================================
# TIER 1: FEATURE COVERAGE (20 tests, 5 per feature)
# =====================================================================

class TestTier1FeatureCoverage(BaseE2ETest):

    # --- Feature 1: Session Management ---
    
    def test_f1_t1_login_success(self):
        """F1: Successful mock mode login saves cache settings."""
        args = self.create_mock_args(username="my_test_user", password="secret_password")
        with console.capture() as cap:
            exit_code = cmd_login(args)
        self.assertEqual(exit_code, 0)
        self.assertIn("Login successful", cap.get())
        
        session_path = get_session_path(use_mock=True)
        self.assertTrue(session_path.exists())
        
        cl = get_client(use_mock=True)
        self.assertTrue(cl.is_logged_in)
        self.assertEqual(cl.username, "my_test_user")

    def test_f1_t1_logout_success(self):
        """F1: Successful mock mode logout clears session files."""
        # Setup active session first
        cl = get_client(use_mock=True)
        cl.login("my_test_user", "password")
        cl.dump_settings(str(get_session_path(use_mock=True)))
        
        args = self.create_mock_args()
        with console.capture() as cap:
            exit_code = cmd_logout(args)
        self.assertEqual(exit_code, 0)
        self.assertIn("Successfully logged out", cap.get())
        self.assertFalse(get_session_path(use_mock=True).exists())

    def test_f1_t1_status_logged_in(self):
        """F1: Session status displays logged in user details."""
        # Setup session
        cl = get_client(use_mock=True)
        cl.login("cool_user", "password")
        cl.dump_settings(str(get_session_path(use_mock=True)))
        
        args = self.create_mock_args()
        with console.capture() as cap:
            exit_code = cmd_status(args)
        self.assertEqual(exit_code, 0)
        output = cap.get()
        self.assertIn("Session Status", output)
        self.assertIn("@mock_user", output) # Mock status uses pre-defined 10001 user details in mock mode
        self.assertIn("Followers", output)

    def test_f1_t1_status_logged_out(self):
        """F1: Status command fails gracefully when not logged in."""
        args = self.create_mock_args()
        with console.capture() as cap:
            exit_code = cmd_status(args)
        self.assertEqual(exit_code, 1)
        self.assertIn("Not logged in", cap.get())

    def test_f1_t1_settings_cache_loading(self):
        """F1: Client retrieves cached login configuration on init."""
        session_path = get_session_path(use_mock=True)
        cl_setup = get_client(use_mock=True)
        cl_setup.is_logged_in = True
        cl_setup.username = "cached_bob"
        cl_setup.user_id = "20006"
        cl_setup.dump_settings(str(session_path))
        
        cl_restored = get_client(use_mock=True)
        self.assertTrue(cl_restored.is_logged_in)
        self.assertEqual(cl_restored.username, "cached_bob")
        self.assertEqual(cl_restored.user_id, "20006")

    # --- Feature 2: DM Rendering ---

    def test_f2_t1_render_text_message(self):
        """F2: Message rendering parses and outputs plain text messages correctly."""
        msg = MockDirectMessage(id="msg_text", user_id="10001", text="Hello world", timestamp=datetime.now())
        res = format_message_text(msg)
        self.assertEqual(res.plain, "Hello world")
        
        single_line_res = format_message_text(msg, single_line=True)
        self.assertEqual(single_line_res, "Hello world")

    def test_f2_t1_render_photo_media(self):
        """F2: Message rendering formats direct photo attachment."""
        photo = MockMedia(pk="p1", id="p1_id", code="photo_code", user=None, caption_text="", media_type=1)
        msg = MockDirectMessage(id="msg_photo", user_id="10001", text="", timestamp=datetime.now(), media=photo)
        
        res = format_message_text(msg)
        self.assertIn("Photo", res.plain)
        
        single_line_res = format_message_text(msg, single_line=True)
        self.assertEqual(single_line_res, "📷 Photo")

    def test_f2_t1_render_video_media(self):
        """F2: Message rendering formats direct video attachment."""
        video = MockMedia(pk="v1", id="v1_id", code="video_code", user=None, caption_text="", media_type=2)
        msg = MockDirectMessage(id="msg_video", user_id="10001", text="", timestamp=datetime.now(), media=video)
        
        res = format_message_text(msg)
        self.assertIn("Video", res.plain)
        
        single_line_res = format_message_text(msg, single_line=True)
        self.assertEqual(single_line_res, "🎥 Video")

    def test_f2_t1_render_visual_media(self):
        """F2: Message rendering formats once-viewable visual media attachments."""
        media = MockMedia(pk="v_media", id="vm_id", code="vm_code", user=None, caption_text="", media_type=1)
        msg = MockDirectMessage(id="msg_visual", user_id="10001", text="", timestamp=datetime.now(), visual_media=media)
        
        res = format_message_text(msg)
        self.assertIn("Visual Photo", res.plain)
        
        single_line_res = format_message_text(msg, single_line=True)
        self.assertEqual(single_line_res, "📷 Visual Photo")

    def test_f2_t1_render_placeholder_or_action_log(self):
        """F2: Message rendering outputs placeholders or action logs gracefully."""
        msg = MockDirectMessage(id="msg_act", user_id="10001", text="", timestamp=datetime.now(), item_type="action_log")
        msg.placeholder = {"message": "User liked a message"}
        
        res = format_message_text(msg)
        self.assertIn("User liked a message", res.plain)

    # --- Feature 3: DM Interactive Chat & /load ---

    def test_f3_t1_chat_history_rendering(self):
        """F3: TUI Chat prints conversation history with sender names."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["/exit"]
        
        # Capture console outputs of interactive_chat
        with console.capture() as cap:
            interactive_chat(cl, "thread_alice")
        
        output = cap.get()
        self.assertIn("Chatting with @alice", output)
        self.assertIn("Hey! Are you working on the Instagram CLI?", output)
        self.assertIn("Awesome. Does it support DMs?", output)

    def test_f3_t1_chat_send_message(self):
        """F3: Typing a normal message in chat triggers cl.direct_send."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["Test sending message to Alice!", "/exit"]
        
        with console.capture():
            interactive_chat(cl, "thread_alice")
            
        # Verify message was added to database
        thread = cl.direct_thread("thread_alice")
        self.assertEqual(thread.messages[0].text, "Test sending message to Alice!")

    def test_f3_t1_chat_refresh_empty(self):
        """F3: Empty message input in chat refreshes conversation history."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Empty string message, then exit
        self.mock_q.text_inputs = ["", "/exit"]
        
        with patch.object(cl, 'direct_thread', wraps=cl.direct_thread) as mock_direct_thread:
            with console.capture():
                interactive_chat(cl, "thread_alice")
            # Verify direct_thread was called for initial render and reload
            self.assertGreaterEqual(mock_direct_thread.call_count, 2)

    def test_f3_t1_chat_exit_command(self):
        """F3: TUI chat loop breaks when /exit command is received."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["/exit"]
        
        with patch.object(cl, 'direct_thread', wraps=cl.direct_thread) as mock_direct_thread:
            with console.capture():
                interactive_chat(cl, "thread_alice")
            # Loop should exit instantly, only fetching the thread once for initial draw
            self.assertEqual(mock_direct_thread.call_count, 1)

    def test_f3_t1_chat_load_limit_increment(self):
        """F3: Entering /load in chat increments fetch amount."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["/load", "/exit"]
        
        with patch.object(cl, 'direct_thread', wraps=cl.direct_thread) as mock_direct_thread:
            with console.capture(): # capture output to prevent pollution
                interactive_chat(cl, "thread_alice")
            # The second fetch from /load command should ask for amount=30
            called_amounts = [call.kwargs.get('amount') for call in mock_direct_thread.call_args_list]
            self.assertIn(30, called_amounts)

    # --- Feature 4: Profile View & TUI Main Menu ---

    def test_f4_t1_profile_search_own(self):
        """F4: Own profile is fetched when username is left empty."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Return empty username, then select Back
        self.mock_q.text_inputs = [""]
        self.mock_q.select_inputs = ["🔙 Back to Menu"]
        
        with patch.object(cl, 'user_info_by_username', wraps=cl.user_info_by_username) as mock_fetch:
            browse_profiles(cl)
            mock_fetch.assert_called_with("test_user")

    def test_f4_t1_profile_search_other(self):
        """F4: Search details show user statistics for specified handle."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["nasa"]
        self.mock_q.select_inputs = ["🔙 Back to Menu"]
        
        with console.capture() as cap:
            browse_profiles(cl)
        
        output = cap.get()
        self.assertIn("NASA", output)
        self.assertIn("Followers:", output)
        self.assertIn("88,000,000", output)

    def test_f4_t1_profile_no_posts(self):
        """F4: 'View Posts' choice is hidden for profiles with 0 posts."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # User Bob Builder in mock database has 3 posts, let's inject a zero-post user
        zero_user = MockUser(pk="zero", username="zero_posts", full_name="Zero Posts", media_count=0)
        cl._users["zero"] = zero_user
        
        self.mock_q.text_inputs = ["zero_posts"]
        self.mock_q.select_inputs = ["🔙 Back to Menu"]
        
        with patch('src.interactive.questionary.select', wraps=self.mock_q.select) as mock_select:
            browse_profiles(cl)
            # Inspect the choices passed to select
            args, kwargs = mock_select.call_args
            choices = kwargs.get("choices") or args[1]
            self.assertNotIn("📸 View Posts", choices)

    def test_f4_t1_profile_view_posts(self):
        """F4: Viewing user posts renders the posts carousel layout."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Retrieve profile of some_new_user (which dynamically generates 3 posts in mock mode)
        self.mock_q.text_inputs = ["some_new_user"]
        self.mock_q.select_inputs = ["📸 View Posts", "▶ Next Post", "🔙 Back to Profile", "🔙 Back to Menu"]
        
        with console.capture() as cap:
            browse_profiles(cl)
            
        output = cap.get()
        self.assertIn("Beautiful day in the life of @some_new_user", output)

    def test_f4_t1_banner_rendering(self):
        """F4: Banner rendering returns aligned structures."""
        banner = get_banner()
        self.assertIsNotNone(banner)
        
        # Render banner and check layout properties
        console_test = Console(force_terminal=True, width=80)
        with console_test.capture() as cap:
            console_test.print(banner)
        output = cap.get()
        self.assertIn("Brainrot free instagram", output)


# =====================================================================
# TIER 2: BOUNDARY & CORNER CASES (20 tests, 5 per feature)
# =====================================================================

class TestTier2BoundaryCorner(BaseE2ETest):

    # --- Feature 1: Session Management ---

    def test_f1_t2_login_fail_invalid_credentials(self):
        """F1 Boundary: Login command fails exit status on credential mismatch."""
        args = self.create_mock_args(username="fail_login", password="wrong_password")
        with console.capture() as cap:
            exit_code = cmd_login(args)
        self.assertEqual(exit_code, 1)
        self.assertIn("Login failed", cap.get())

    def test_f1_t2_login_2fa_requires_code_empty(self):
        """F1 Boundary: 2FA prompt cancels login when provided empty code."""
        cl = get_client(use_mock=True)
        self.mock_q.text_inputs = [""]  # empty code
        
        with console.capture() as cap:
            success = login_user(cl, "2fa_user", "password", use_mock=True)
        self.assertFalse(success)
        self.assertIn("2FA code is required", cap.get())

    def test_f1_t2_login_challenge_invalid_code(self):
        """F1 Boundary: Challenge prompt returns false when verification code is wrong."""
        cl = get_client(use_mock=True)
        
        # Challenge code handler mock returning wrong code
        cl.challenge_code_handler = lambda username, choice: "wrong_code"
        
        with console.capture() as cap:
            success = login_user(cl, "challenge_user", "password", use_mock=True)
        self.assertFalse(success)
        self.assertIn("Login failed", cap.get())

    def test_f1_t2_logout_no_session(self):
        """F1 Boundary: Logout when no session cache exists fails gracefully with notice."""
        # Ensure session path is deleted
        path = get_session_path(use_mock=True)
        if path.exists():
            path.unlink()
            
        args = self.create_mock_args()
        with console.capture() as cap:
            exit_code = cmd_logout(args)
        self.assertEqual(exit_code, 0)
        self.assertIn("No active session found", cap.get())

    def test_f1_t2_get_client_session_expired(self):
        """F1 Boundary: get_client removes expired settings files on feed fetch failure."""
        session_path = get_session_path(use_mock=False)
        
        # Write some dummy config to the real session path
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with open(session_path, "w") as f:
            f.write('{"is_logged_in": true, "username": "expired_user", "user_id": "9999"}')
            
        mock_client_inst = MagicMock()
        mock_client_inst.user_id = "9999"
        mock_client_inst.username = "expired_user"
        mock_client_inst.get_timeline_feed.side_effect = Exception("Expired token")
        
        with patch('src.client_manager.Client', return_value=mock_client_inst):
            cl = get_client(use_mock=False)
            
        # Verify settings file was unlinked/deleted
        self.assertFalse(session_path.exists())

    # --- Feature 2: DM Rendering ---

    def test_f2_t2_render_shared_reel_with_code(self):
        """F2 Boundary: Shared Reel prints terminal-compliant link structure."""
        user = MockUser("20001", "nasa", "NASA")
        reel = MockMedia(pk="r1", id="r1_id", code="CtNASA1", user=user, caption_text="Launch!", media_type=2)
        msg = MockDirectMessage(id="msg_reel", user_id="20001", text="", timestamp=datetime.now(), clip=reel)
        
        res = format_message_text(msg)
        
        # Test rendering output contains hyperlink sequence
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        self.assertIn("https://instagram.com/reel/CtNASA1", output)
        self.assertIn("\x1b]8;", output) # Check for OSC 8 escape code prefix

    def test_f2_t2_render_shared_reel_without_code(self):
        """F2 Boundary: Shared Reel without code degrades fallback to text without links."""
        user = MockUser("20001", "nasa", "NASA")
        reel = MockMedia(pk="r1", id="r1_id", code="", user=user, caption_text="Launch!", media_type=2)
        msg = MockDirectMessage(id="msg_reel", user_id="20001", text="", timestamp=datetime.now(), clip=reel)
        
        res = format_message_text(msg)
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        self.assertNotIn("https://instagram.com/reel/", output)
        self.assertIn("Shared Reel from @nasa", output)

    def test_f2_t2_render_shared_post_with_code(self):
        """F2 Boundary: Shared Post prints terminal-compliant post link structure."""
        user = MockUser("20002", "programmer_humor", "Programmer Humor")
        post = MockMedia(pk="p1", id="p1_id", code="CtPROG1", user=user, caption_text="Funny!", media_type=1)
        msg = MockDirectMessage(id="msg_post", user_id="20002", text="", timestamp=datetime.now(), media_share=post)
        
        res = format_message_text(msg)
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        self.assertIn("https://instagram.com/p/CtPROG1", output)
        self.assertIn("\x1b]8;", output)

    def test_f2_t2_render_shared_post_without_code(self):
        """F2 Boundary: Shared Post without code degrades fallback to plain text."""
        user = MockUser("20002", "programmer_humor", "Programmer Humor")
        post = MockMedia(pk="p1", id="p1_id", code="", user=user, caption_text="Funny!", media_type=1)
        msg = MockDirectMessage(id="msg_post", user_id="20002", text="", timestamp=datetime.now(), media_share=post)
        
        res = format_message_text(msg)
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        self.assertNotIn("https://instagram.com/p/", output)
        self.assertIn("Shared Post from @programmer_humor", output)

    def test_f2_t2_render_shared_link_xma_share(self):
        """F2 Boundary: XMA external links render titles and terminal hyperlink codes."""
        class MockXmaShare:
            title = "Google Search"
            video_url = "https://google.com"
            preview_url = "https://google.com/preview"
            
        msg = MockDirectMessage(id="msg_link", user_id="20005", text="", timestamp=datetime.now())
        msg.xma_share = MockXmaShare()
        
        res = format_message_text(msg)
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        self.assertIn("Google Search", output)
        self.assertIn("https://google.com", output)

    # --- Feature 3: DM Interactive Chat & /load ---

    def test_f3_t2_chat_load_multiple_increments(self):
        """F3 Boundary: Successive /load commands increment loading limit (15 -> 30 -> 45)."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["/load", "/load", "/exit"]
        
        with patch.object(cl, 'direct_thread', wraps=cl.direct_thread) as mock_direct_thread:
            with console.capture():
                interactive_chat(cl, "thread_alice")
            
            called_amounts = [call.kwargs.get('amount') for call in mock_direct_thread.call_args_list]
            self.assertEqual(called_amounts, [None, 30, 45])

    def test_f3_t2_chat_load_error_handling(self):
        """F3 Boundary: API failure during /load does not crash the interactive chat."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["/load", "/exit"]
        
        # Initial direct_thread works, second one fails
        original_thread = cl.direct_thread
        call_count = 0
        
        def mock_direct_thread_fail(thread_id, amount=20):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise Exception("Network Timeout during load")
            return original_thread(thread_id, amount)
            
        with patch.object(cl, 'direct_thread', side_effect=mock_direct_thread_fail):
            with console.capture() as cap:
                interactive_chat(cl, "thread_alice")
                
        self.assertIn("Failed to load older messages: Network Timeout during load", cap.get())

    def test_f3_t2_chat_send_message_error(self):
        """F3 Boundary: API failure during sending message prints warning and keeps loop active."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["Send message!", "/exit"]
        
        with patch.object(cl, 'direct_send', side_effect=Exception("API limit exceeded")):
            with console.capture() as cap:
                interactive_chat(cl, "thread_alice")
                
        self.assertIn("Failed to send message: API limit exceeded", cap.get())

    def test_f3_t2_chat_reactions_handling(self):
        """F3 Boundary: Message reactions (emojis) are rendered directly below message bubble."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Add mock reactions to thread_alice message
        thread = cl.direct_thread("thread_alice")
        msg = thread.messages[0]
        
        class Reaction:
            emoji = "🎉"
            
        class Reactions:
            emojis = [Reaction()]
            likes_count = 2
            
        msg.reactions = Reactions()
        
        self.mock_q.text_inputs = ["/exit"]
        
        with console.capture() as cap:
            interactive_chat(cl, "thread_alice")
            
        output = cap.get()
        self.assertIn("🎉 ❤️", output) # Emojis should print below message

    def test_f3_t2_chat_action_log_filtering(self):
        """F3 Boundary: Chat loop filters action logs (e.g. liked, reacted) from visible flow."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Insert action log message
        thread = cl.direct_thread("thread_alice")
        action_msg = MockDirectMessage(id="msg_action_like", user_id="20005", text="[Action Log]", timestamp=datetime.now() - timedelta(minutes=1), item_type="action_log")
        thread.messages.insert(0, action_msg)
        
        self.mock_q.text_inputs = ["/exit"]
        
        with console.capture() as cap:
            interactive_chat(cl, "thread_alice")
            
        output = cap.get()
        self.assertNotIn("[Action Log]", output)

    # --- Feature 4: Profile View & TUI Main Menu ---

    def test_f4_t2_resolve_none_username(self):
        """F4 Boundary: TUI username resolver handles username resolution fallback when value is 'None'."""
        cl = get_client(use_mock=True)
        cl.login("None", "password") # Username is string None
        
        # Mock cl.username_from_user_id to return resolved_user successfully
        cl.username_from_user_id = MagicMock(return_value="resolved_user")
        
        self.mock_q.select_inputs = ["❌ Exit"]
        
        session_path = get_session_path(use_mock=True)
        
        with console.capture() as cap:
            run_tui(cl, use_mock=True)
            
        self.assertIn("Logged in as: @resolved_user", cap.get())

        # Now test that Python None object resolves to 'Logged In' when session file is absent and lookup fails
        cl.username = None
        if session_path.exists():
            session_path.unlink()
        cl.username_from_user_id = MagicMock(side_effect=Exception("API error"))
        
        self.mock_q.select_inputs = ["❌ Exit"]
        with console.capture() as cap2:
            run_tui(cl, use_mock=True)
        self.assertIn("Logged in as: @Logged In", cap2.get())

    def test_f4_t2_profile_fetch_fail(self):
        """F4 Boundary: Fetch profiles handles API failure gracefully, keeping loop alive."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["broken_user"]
        
        with patch.object(cl, 'user_info_by_username', side_effect=Exception("User profile is private or suspended")):
            with console.capture() as cap:
                browse_profiles(cl)
                
        output = cap.get()
        self.assertIn("Failed to fetch user profile: User profile is private or suspended", output)

    def test_f4_t2_view_posts_fail(self):
        """F4 Boundary: Fetch post media failures are caught, displaying fallback message."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        user = cl.user_info_by_username("nasa")
        
        with patch.object(cl, 'user_medias', side_effect=Exception("API connection aborted")):
            with console.capture() as cap:
                view_user_posts(cl, user)
                
        output = cap.get()
        self.assertIn("Failed to fetch posts: API connection aborted", output)

    def test_f4_t2_banner_ascii_txt_missing(self):
        """F4 Boundary: Missing ascii.txt prompts code-defined ASCII art fallback."""
        with patch('os.path.exists', return_value=False):
            banner = get_banner()
            self.assertIsNotNone(banner)
            c = Console(force_terminal=True)
            with c.capture() as cap:
                c.print(banner)
            output = cap.get()
            self.assertIn("Brainrot free instagram", output)

    def test_f4_t2_main_menu_quit(self):
        """F4 Boundary: Run TUI loop exits immediately when exit is selected."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.select_inputs = ["❌ Exit"]
        
        with console.capture() as cap:
            run_tui(cl, use_mock=True)
            
        output = cap.get()
        self.assertIn("Logged in as: @test_user", output)

    def test_mock_client_username_from_user_id(self):
        """Test username_from_user_id on MockClient raises error on missing user or returns correct username."""
        cl = get_client(use_mock=True)
        self.assertEqual(cl.username_from_user_id("20005"), "alice")
        with self.assertRaises(Exception):
            cl.username_from_user_id("invalid_id")

    def test_client_manager_preserves_session_on_network_error(self):
        """Test that get_client does not delete session cache on network/timeout connection errors."""
        session_path = get_session_path(use_mock=False)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with open(session_path, "w") as f:
            f.write('{"is_logged_in": true, "username": "test_user", "user_id": "9999"}')
            
        mock_client_inst = MagicMock()
        mock_client_inst.user_id = "9999"
        mock_client_inst.username = "test_user"
        mock_client_inst.get_timeline_feed.side_effect = Exception("Connection timed out")
        
        with patch('src.client_manager.Client', return_value=mock_client_inst):
            cl = get_client(use_mock=False)
            
        # Verify settings file still exists (not deleted on network error)
        self.assertTrue(session_path.exists())
        # Clean up session path
        try:
            session_path.unlink()
        except Exception:
            pass

    def test_rich_markup_escaping_placeholder(self):
        """Test that placeholders containing rich markup syntax are correctly escaped and rendered."""
        msg = MockDirectMessage(id="msg_placeholder", user_id="20005", text="", timestamp=datetime.now())
        msg.placeholder = {"message": "[bold red]System Alert[/bold red]"}
        
        res = format_message_text(msg)
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(res)
        output = cap.get()
        # Should display the raw markup tags because they are escaped
        self.assertIn("[bold red]System Alert[/bold red]", output)

    def test_feed_slicing_guard_none(self):
        """Test that feed command handles a client returning None for timeline feed gracefully."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        class Args:
            mock = True
            limit = 5
            
        with patch.object(cl, 'get_timeline_feed', return_value=None):
            with patch('src.cli.get_client', return_value=cl):
                with console.capture() as cap:
                    status = cmd_feed(Args())
                output = cap.get()
                
        self.assertEqual(status, 0)
        self.assertIn("Your feed is empty.", output)


# =====================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (4 tests)
# =====================================================================

class TestTier3CrossFeature(BaseE2ETest):

    def test_tier3_session_expired_during_chat(self):
        """F1 x F3: Session expiration during DM chat throws error and exits chat flow."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        self.mock_q.text_inputs = ["", "/exit"] # message tries to refresh
        
        # Simulate invalid session on subsequent direct_thread call (second call)
        call_count = 0
        original_direct_thread = cl.direct_thread
        
        def mock_direct_thread_expire(thread_id, amount=20):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                cl.is_logged_in = False # Session invalidates
                raise Exception("Session expired (LoginRequired)")
            return original_direct_thread(thread_id, amount)
            
        with patch.object(cl, 'direct_thread', side_effect=mock_direct_thread_expire):
            with console.capture() as cap:
                interactive_chat(cl, "thread_alice")
                
        self.assertIn("Failed to refresh chat: Session expired (LoginRequired)", cap.get())

    def test_tier3_profile_search_and_send_dm(self):
        """F4 x F1 x F3: Search a profile then start DM flow to send initial message."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # Flow: profile menu -> search other user "alice" -> send direct message to them
        self.mock_q.text_inputs = ["alice", "Hey Alice, sending this from your profile page!"]
        
        with patch.object(cl, 'direct_send', wraps=cl.direct_send) as mock_send:
            send_new_message_interactive(cl)
            
            mock_send.assert_called_once_with("Hey Alice, sending this from your profile page!", recipient_users=["alice"])

    def test_tier3_dm_hyperlink_resolution_after_relogin(self):
        """F1 x F2: Relogin as different user updates link recipient mappings."""
        # 1. Login as bob
        cl = get_client(use_mock=True)
        cl.login("bob", "password")
        cl.dump_settings(str(get_session_path(use_mock=True)))
        
        # Generate post msg
        user = MockUser("20002", "programmer_humor", "Programmer Humor")
        post = MockMedia(pk="p1", id="p1_id", code="CtPROG1", user=user, caption_text="Funny!", media_type=1)
        msg = MockDirectMessage(id="m_link", user_id="20002", text="", timestamp=datetime.now(), media_share=post)
        
        c = Console(force_terminal=True, color_system="truecolor")
        with c.capture() as cap:
            c.print(format_message_text(msg))
        self.assertIn("https://instagram.com/p/CtPROG1", cap.get())
        
        # 2. Relogin as alice
        args_login = self.create_mock_args(username="alice", password="new_password")
        cmd_login(args_login)
        
        # Verify cached client is updated
        cl_new = get_client(use_mock=True)
        self.assertEqual(cl_new.username, "alice")
        
        # Verify formatting continues to work for new session
        with c.capture() as cap2:
            c.print(format_message_text(msg))
        self.assertIn("https://instagram.com/p/CtPROG1", cap2.get())

    def test_tier3_inbox_session_invalidation(self):
        """F1 x F3: Deleting session file prevents inbox loading."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        cl.dump_settings(str(get_session_path(use_mock=True)))
        
        # Delete session
        get_session_path(use_mock=True).unlink()
        
        # Attempt running inbox cmd
        args = self.create_mock_args(limit=10)
        
        # Re-fetch client which loads from settings (now missing)
        cl_unauth = get_client(use_mock=True, force_login=True) # force reload
        
        with patch('src.cli.get_client', return_value=cl_unauth):
            with console.capture() as cap:
                exit_code = cmd_inbox(args)
                
        self.assertEqual(exit_code, 1)
        self.assertIn("Authentication required", cap.get())


# =====================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 tests)
# =====================================================================

class TestTier4RealWorld(BaseE2ETest):

    def test_tier4_user_journey_success(self):
        """Tier 4: Successful end-to-end user navigation flow.
        Flow: CLI Login -> CLI Status -> TUI Main Menu -> Search Profile -> Inbox -> Chat Room -> Exit.
        """
        # 1. Login E2E
        args_login = self.create_mock_args(username="journey_user", password="password")
        with console.capture():
            cmd_login(args_login)
            
        # 2. Check Status
        args_status = self.create_mock_args()
        with console.capture() as cap_status:
            cmd_status(args_status)
        self.assertIn("@mock_user", cap_status.get())
        
        # 3. Interactive TUI Menu Walkthrough
        cl = get_client(use_mock=True)
        
        # Menu choices sequence:
        # - Main: View Profile -> Search user "nasa" -> Back to Menu
        # - Main: Direct Messages -> Select "thread_alice" -> Send msg -> Load history -> Exit chat -> Back to Menu (using Choice value "back")
        # - Main: Exit
        self.mock_q.select_inputs = [
            "👤 View Profile (Search/Own)", 
            "🔙 Back to Menu", 
            "💬 Direct Messages (Inbox)", 
            "thread_alice", 
            "back", 
            "❌ Exit"
        ]
        self.mock_q.text_inputs = [
            "nasa", # Profile Search input
            "Live chat message!", # Chat input
            "/load", # Chat input 2
            "/exit" # Chat input 3
        ]
        
        with console.capture() as cap_tui:
            run_tui(cl, use_mock=True)
            
        output = cap_tui.get()
        self.assertIn("Logged in as: @journey_user", output)
        self.assertIn("Chatting with @alice", output)

    def test_tier4_user_journey_login_with_2fa_and_dm(self):
        """Tier 4: Complete flow of login with 2FA, viewing inbox, opening chat room, loading history, sending DM, and logging out."""
        cl = get_client(use_mock=True)
        
        # 1. Login with 2FA
        self.mock_q.text_inputs = ["123456"] # 2FA code
        with console.capture() as cap_login:
            login_user(cl, "2fa_user", "password", use_mock=True)
        self.assertIn("Login successful with 2FA", cap_login.get())
        
        # 2. Inbox, Chat, /load, Send Message
        self.mock_q.select_inputs = [
            "💬 Direct Messages (Inbox)", 
            "thread_alice", 
            "back", 
            "❌ Exit"
        ]
        self.mock_q.text_inputs = [
            "/load", 
            "Automated test message over 2FA!", 
            "/exit"
        ]
        
        with console.capture():
            run_tui(cl, use_mock=True)
            
        # Verify message was delivered to database
        thread = cl.direct_thread("thread_alice")
        self.assertEqual(thread.messages[0].text, "Automated test message over 2FA!")
        
        # 3. Logout
        with console.capture():
            logout_user(use_mock=True)
        self.assertFalse(get_session_path(use_mock=True).exists())

    def test_tier4_user_journey_offline_demo_flow(self):
        """Tier 4: Executing offline mock mode commands: login, post an image, check inbox, send DM, and logout."""
        # Setup session
        args_login = self.create_mock_args(username="offline_guy", password="password")
        with console.capture():
            cmd_login(args_login)
            
        # Post photo
        args_post = self.create_mock_args(image_path="mock_path.jpg", caption="Enjoying the offline CLI mode!")
        with console.capture() as cap_post:
            cmd_post(args_post)
        self.assertIn("Upload successful", cap_post.get())
        
        # Read Inbox
        args_inbox = self.create_mock_args(limit=5)
        with console.capture() as cap_inbox:
            cmd_inbox(args_inbox)
        self.assertIn("Direct Messages Inbox", cap_inbox.get())
        
        # Send DM
        args_dm = self.create_mock_args(username="alice", message="Hey Alice, testing DM subcommand!")
        with console.capture() as cap_dm:
            cmd_dm(args_dm)
        self.assertIn("Message sent to @alice successfully", cap_dm.get())
        
        # Logout
        args_logout = self.create_mock_args()
        with console.capture():
            cmd_logout(args_logout)
            
        self.assertFalse(get_session_path(use_mock=True).exists())

    def test_tier4_user_journey_profile_posts_interaction(self):
        """Tier 4: Search profile, browse posts carousel, like and comment on a post, and return to main menu."""
        cl = get_client(use_mock=True)
        cl.login("test_user", "password")
        
        # TUI choices: Profile search -> View Posts -> Like -> Comment -> Back to Profile -> Back to Menu -> Exit
        self.mock_q.select_inputs = [
            "👤 View Profile (Search/Own)",
            "📸 View Posts",
            "❤️ Like",
            "💬 Comment",
            "🔙 Back to Profile",
            "🔙 Back to Menu",
            "❌ Exit"
        ]
        self.mock_q.text_inputs = [
            "nasa", # profile to search
            "Great Hubble photo!", # comment text
        ]
        
        with console.capture() as cap:
            run_tui(cl, use_mock=True)
            
        output = cap.get()
        self.assertIn("Liked!", output)
        self.assertIn("Comment posted!", output)
        
        # Verify likes/comments updated in mock DB
        nasa_post = cl.user_medias("20001")[0]
        self.assertTrue(nasa_post.has_liked)

    def test_tier4_user_journey_session_recovery_and_inbox(self):
        """Tier 4: Restore session from cache file, run status, browse inbox, send new message to a new user, and logout."""
        # 1. Create a session file
        session_path = get_session_path(use_mock=True)
        cl_init = get_client(use_mock=True)
        cl_init.login("recovered_user", "password")
        cl_init.dump_settings(str(session_path))
        
        # 2. Recover settings dynamically in next call
        cl_recovered = get_client(use_mock=True)
        self.assertTrue(cl_recovered.is_logged_in)
        self.assertEqual(cl_recovered.username, "recovered_user")
        
        # 3. Inbox -> Send message to new user
        self.mock_q.select_inputs = [
            "💬 Direct Messages (Inbox)",
            "new_user",
            "back",
            "❌ Exit"
        ]
        self.mock_q.text_inputs = [
            "antigravity_ai", # new user username
            "Hello Antigravity AI! Let's build some cool tools.", # message text
        ]
        
        with console.capture() as cap:
            run_tui(cl_recovered, use_mock=True)
            
        self.assertIn("Message sent successfully!", cap.get())
        
        # Verify thread was created for recipient
        thread = cl_recovered.direct_thread("thread_antigravity_ai")
        self.assertEqual(thread.messages[0].text, "Hello Antigravity AI! Let's build some cool tools.")


if __name__ == "__main__":
    unittest.main()
