from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
from instagrapi.mixins.challenge import ChallengeChoice

from src.utils import console
from src.mock_client import MockClient

# Path to session storage
SESSION_DIR = Path.home() / ".config" / "instagram_cli"
SESSION_FILE = SESSION_DIR / "session.json"
MOCK_SESSION_FILE = SESSION_DIR / "session_mock.json"

def get_session_path(use_mock: bool) -> Path:
    """Gets the appropriate session file path."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return MOCK_SESSION_FILE if use_mock else SESSION_FILE

def setup_challenge_handler(cl: Client):
    """Sets up the email/SMS verification challenge handler for the client."""
    def challenge_code_handler(username: str, choice: ChallengeChoice):
        console.print(f"\n[warning]⚠️ Instagram is requiring verification for account: {username}[/warning]")
        method = "SMS" if choice == ChallengeChoice.SMS else "Email"
        console.print(f"[info]Verification code has been sent via {method}.[/info]")
        
        # We need an interactive prompt to get the code
        import questionary
        code = questionary.text(f"Enter the verification code sent to your {method}:").ask()
        if code:
            return code.strip()
        return False
        
    cl.challenge_code_handler = challenge_code_handler

def patch_client(cl: Client):
    """Patches Client methods to convert raw API outputs to parsed typed lists."""
    from instagrapi.extractors import extract_media_v1

    # Patch extract_media_v1_xma globally to fix Pydantic validation errors for video_url scheme
    import instagrapi.extractors
    if not getattr(instagrapi.extractors.extract_media_v1_xma, "_patched", False):
        original_xma = instagrapi.extractors.extract_media_v1_xma

        def patched_extract_media_v1_xma(data):
            import copy
            data = copy.deepcopy(data)
            target_url = data.get("target_url") or ""
            if target_url and not (target_url.startswith("http://") or target_url.startswith("https://")):
                if "://" in target_url:
                    parts = target_url.split("://", 1)
                    if parts[0] == "instagram":
                        data["target_url"] = f"https://instagram.com/{parts[1]}"
                    else:
                        data["target_url"] = f"https://{parts[1]}"
                elif target_url.startswith("/"):
                    data["target_url"] = f"https://instagram.com{target_url}"
                else:
                    data["target_url"] = f"https://instagram.com/{target_url}"
            
            try:
                return original_xma(data)
            except Exception:
                return None

        patched_extract_media_v1_xma._patched = True
        instagrapi.extractors.extract_media_v1_xma = patched_extract_media_v1_xma

    if not getattr(cl.get_timeline_feed, "_patched", False):
        original_get_timeline_feed = cl.get_timeline_feed

        def patched_get_timeline_feed(*args, **kwargs):
            raw_feed = original_get_timeline_feed(*args, **kwargs)
            if isinstance(raw_feed, dict):
                medias = []
                items = raw_feed.get("feed_items", [])
                for item in items:
                    media_dict = item.get("media_or_ad")
                    if media_dict and "media_type" in media_dict:
                        try:
                            media = extract_media_v1(media_dict)
                            medias.append(media)
                        except Exception:
                            pass
                return medias
            return raw_feed

        patched_get_timeline_feed._patched = True
        cl.get_timeline_feed = patched_get_timeline_feed

def get_client(use_mock: bool = False, force_login: bool = False) -> Client:
    """
    Initializes and returns a client. 
    Loads cached session settings if available to avoid logging in again.
    """
    session_path = get_session_path(use_mock)
    
    if use_mock:
        cl = MockClient()
        if not force_login and session_path.exists():
            cl.load_settings(str(session_path))
        return cl

    cl = Client()
    patch_client(cl)
    setup_challenge_handler(cl)

    # Try to load existing session
    if not force_login and session_path.exists():
        try:
            cl.load_settings(str(session_path))
            # Restore username from settings file
            import json
            try:
                with open(session_path, "r") as f:
                    data = json.load(f)
                cl.username = data.get("username")
            except Exception:
                pass
            if not cl.username and cl.user_id:
                try:
                    cl.username = cl.username_from_user_id(cl.user_id)
                except Exception:
                    pass
            # Test if session is still valid
            cl.get_timeline_feed()
            return cl
        except Exception as e:
            from instagrapi.exceptions import LoginRequired
            is_login_err = isinstance(e, LoginRequired) or "login_required" in str(e).lower() or "please login" in str(e).lower() or "expired" in str(e).lower()
            if use_mock or is_login_err:
                console.print("[warning]Session expired. Re-authentication required.[/warning]")
                try:
                    session_path.unlink()
                except Exception:
                    pass
            else:
                console.print(f"[warning]⚠️ Connection error during session validation: {e}[/warning]")
                return cl
                
    return cl

def save_client_settings(cl, path, username):
    """Saves client settings and ensures username is persisted in the session file."""
    cl.dump_settings(str(path))
    import json
    try:
        with open(path, "r") as f:
            data = json.load(f)
        data["username"] = username
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def login_user(cl, username, password, use_mock=False):
    """Performs login and handles 2FA/challenges, saving the session upon success."""
    session_path = get_session_path(use_mock)
    
    try:
        console.print(f"[info]Attempting to log in as [username]@{username}[/username]...[/info]")
        cl.login(username, password)
        save_client_settings(cl, session_path, username)
        console.print("[success]✓ Login successful![/success]")
        return True
        
    except TwoFactorRequired:
        console.print("[warning]🔐 Two-Factor Authentication is enabled on this account.[/warning]")
        import questionary
        code = questionary.text("Enter your 2FA verification code:").ask()
        if not code:
            console.print("[error]✗ 2FA code is required to complete login.[/error]")
            return False
            
        try:
            cl.two_factor_login(code.strip())
            save_client_settings(cl, session_path, username)
            console.print("[success]✓ Login successful with 2FA![/success]")
            return True
        except Exception as e:
            console.print(f"[error]✗ 2FA Login failed: {e}[/error]")
            return False
            
    except ChallengeRequired as e:
        console.print(f"[warning]⚠️ Verification Challenge required: {e}[/warning]")
        # This will trigger challenge_code_handler automatically inside instagrapi
        # after which instagrapi automatically retries login.
        try:
            # Re-attempting login will trigger the challenge flow automatically
            cl.login(username, password)
            save_client_settings(cl, session_path, username)
            console.print("[success]✓ Login successful after challenge verification![/success]")
            return True
        except Exception as ex:
            console.print(f"[error]✗ Verification failed: {ex}[/error]")
            return False
            
    except Exception as e:
        console.print(f"[error]✗ Login failed: {e}[/error]")
        return False

def logout_user(use_mock=False):
    """Logs out and deletes session file."""
    session_path = get_session_path(use_mock)
    
    cl = get_client(use_mock=use_mock)
    try:
        cl.logout()
    except Exception:
        pass
        
    if session_path.exists():
        try:
            session_path.unlink()
            console.print("[success]✓ Successfully logged out and cleared session cache.[/success]")
        except Exception as e:
            console.print(f"[error]✗ Failed to clear session file: {e}[/error]")
    else:
        console.print("[info]No active session found.[/info]")
