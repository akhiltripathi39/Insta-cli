import os
import sys
from datetime import datetime, timezone
from rich.console import Console
from rich.theme import Theme

# Define custom theme for Instagram-like colors
instagram_theme = Theme({
    "primary": "bold #C13584",      # Instagram Pink/Magenta
    "secondary": "#E1306C",        # Instagram Red-Pink
    "accent": "#405DE6",           # Instagram Blue
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "info": "italic cyan",
    "username": "bold magenta",    # Magenta
    "hashtag": "#833AB4",          # Purple
    "timestamp": "dim white",
})

console = Console(theme=instagram_theme)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_banner():
    """Returns a beautiful ASCII banner for Instagram CLI, loading from ascii.txt if available."""
    from rich.align import Align
    from rich.console import Group
    from rich.text import Text
    import os
    
    banner_text = None
    possible_paths = [
        "ascii.txt",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "ascii.txt")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    banner_text = f.read().rstrip()
                break
            except Exception:
                pass
                
    if not banner_text:
        banner_text = (
            "  _____           _                   _ _\n"
            "  \\_   \\_ __  ___| |_ __ _        ___| (_)\n"
            "   / /\\/ '_ \\/ __| __/ _` |_____ / __| | |\n"
            "/\\/ /_ | | | \\__ \\ || (_| |_____| (__| | |\n"
            "\\____/ |_| |_|___/\\__\\__,_|      \\___|_|_|"
        )
        
    lines = banner_text.splitlines()
    max_len = max(len(l) for l in lines) if lines else 0
    padded_lines = [l.ljust(max_len) for l in lines]
    banner_text_padded = "\n".join(padded_lines)
    
    g = Group(
        Align.center(Text(banner_text_padded, style="bold #C13584")),
        Align.center(Text("★ Brainrot free instagram ★", style="bold #E1306C"))
    )
    return g

def format_relative_time(dt: datetime) -> str:
    """Formats a datetime object to a friendly relative string (e.g., '2 hours ago')."""
    if not dt:
        return "unknown"
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = diff.total_seconds()
    
    if seconds < 0:
        return "just now"
    
    if seconds < 60:
        return "just now"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m ago"
    
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    
    days = hours / 24
    if days < 7:
        return f"{int(days)}d ago"
    
    weeks = days / 7
    if weeks < 52:
        return f"{int(weeks)}w ago"
        
    return dt.strftime("%b %d, %Y")

def exit_app(message="Goodbye!", code=0):
    """Exits the application cleanly."""
    console.print(f"\n[secondary]{message}[/secondary]")
    sys.exit(code)

class InlineClickable:
    """A renderable class that yields OSC 8 escape sequences to rich console."""
    def __init__(self, text: str, url: str, prefix: str = ""):
        self.text = text
        self.url = url
        self.prefix = prefix

    def __rich_console__(self, console, options):
        from rich.segment import Segment
        from rich.style import Style
        if self.prefix:
            yield Segment(self.prefix)
        yield Segment(f"\x1b]8;;{self.url}\x1b\\", control=True)
        yield Segment(self.text, style=Style.parse("bold #405DE6"))
        yield Segment("\x1b]8;;\x1b\\", control=True)

def get_plain_text(renderable) -> str:
    """Recursively gets plain text string from any rich renderable (Text, Group, etc)."""
    if not renderable:
        return ""
    if isinstance(renderable, str):
        return renderable
    if hasattr(renderable, "plain"):
        return renderable.plain
    # If it is a Group
    from rich.console import Group
    if isinstance(renderable, Group):
        parts = []
        for r in getattr(renderable, "renderables", []):
            parts.append(get_plain_text(r))
        return "".join(parts)
    return str(renderable)

def format_message_text(msg, single_line: bool = False):
    """Formats a message body to show text, attachments, links, or action placeholders."""
    from rich.text import Text
    from rich.console import Group
    
    if not msg:
        return "" if single_line else Text("")
        
    text = getattr(msg, "text", None)
    if text:
        return text.replace('\n', ' ') if single_line else Text(text)
        
    # Check for direct media (Photo/Video sent in chat)
    media = getattr(msg, "media", None)
    if media:
        media_type = getattr(media, "media_type", 1) # 1 = Photo, 2 = Video
        media_name = "Video" if media_type == 2 else "Photo"
        emoji = "🎥" if media_type == 2 else "📷"
        
        if single_line:
            return f"{emoji} {media_name}"
        else:
            return Text.from_markup(f"{emoji} [bold]{media_name}[/bold]")

    # Check for visual_media (expiring/once viewable photos/videos)
    visual_media = getattr(msg, "visual_media", None)
    if visual_media:
        media_content = getattr(visual_media, "media", None)
        media_type = 1
        if media_content:
            media_type = getattr(media_content, "media_type", 1)
                
        media_name = "Visual Video" if media_type == 2 else "Visual Photo"
        emoji = "🎥" if media_type == 2 else "📷"
        
        if single_line:
            return f"{emoji} {media_name}"
        else:
            return Text.from_markup(f"{emoji} [bold]{media_name}[/bold]")

    # Check for clip (Shared Reel)
    clip = getattr(msg, "clip", None)
    if clip:
        creator = None
        user_obj = getattr(clip, "user", None)
        if user_obj:
            creator = getattr(user_obj, "username", None)
            
        caption = getattr(clip, "caption_text", "") or ""
        code = getattr(clip, "code", "") or ""
        
        if len(caption) > 30:
            caption = caption[:27] + "..."
            
        creator_str = f" from @{creator}" if creator else ""
        
        if single_line:
            caption_part = f': "{caption}"' if caption else ""
            return f"🎬 Shared Reel{creator_str}{caption_part}"
        else:
            t = Text.from_markup(f"🎬 [bold]Shared Reel{creator_str}[/bold]")
            if caption:
                t.append(f'\n"{caption}"')
                
            items = [t]
            if code:
                url = f"https://instagram.com/reel/{code}"
                items.append(InlineClickable("Reel", url, prefix="\n🔗 "))
            return Group(*items) if len(items) > 1 else t

    # Check for media_share (Shared Post)
    media_share = getattr(msg, "media_share", None)
    if media_share:
        creator = None
        user_obj = getattr(media_share, "user", None)
        if user_obj:
            creator = getattr(user_obj, "username", None)
            
        caption = getattr(media_share, "caption_text", "") or ""
        code = getattr(media_share, "code", "") or ""
        
        if len(caption) > 30:
            caption = caption[:27] + "..."
            
        creator_str = f" from @{creator}" if creator else ""
        
        if single_line:
            caption_part = f': "{caption}"' if caption else ""
            return f"📸 Shared Post{creator_str}{caption_part}"
        else:
            t = Text.from_markup(f"📸 [bold]Shared Post{creator_str}[/bold]")
            if caption:
                t.append(f'\n"{caption}"')
                
            items = [t]
            if code:
                url = f"https://instagram.com/p/{code}"
                items.append(InlineClickable("Post", url, prefix="\n🔗 "))
            return Group(*items) if len(items) > 1 else t

    # Check for xma_share (Shared external link or rich preview)
    xma_share = getattr(msg, "xma_share", None)
    if xma_share:
        title = getattr(xma_share, "title", None) or getattr(xma_share, "header_title_text", "Shared Link")
        video_url = getattr(xma_share, "video_url", None)
        preview_url = getattr(xma_share, "preview_url", None)
        
        display_link = video_url or preview_url
        
        if single_line:
            return f"🔗 Link: {title}"
        else:
            t = Text()
            t.append("🔗 ")
            t.append(title, style="bold")
            
            items = [t]
            if display_link:
                items.append(InlineClickable("Link", display_link, prefix="\n🔗 "))
            return Group(*items) if len(items) > 1 else t

    # Check for placeholder (often populated for action logs or call states)
    placeholder = getattr(msg, "placeholder", None)
    if isinstance(placeholder, dict):
        message = placeholder.get("message") or placeholder.get("title")
        if message:
            if single_line:
                return message
            else:
                from rich.markup import escape
                return Text.from_markup(f"[italic dim]{escape(message)}[/italic dim]")

    # Fallback to item_type
    item_type = getattr(msg, "item_type", None) or "attachment"
    if not item_type or item_type == "None":
        item_type = "attachment"
    fallback_text = f"[{item_type.replace('_', ' ').title()}]"
    return fallback_text if single_line else Text(fallback_text)
