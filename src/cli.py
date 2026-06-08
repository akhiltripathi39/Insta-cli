import argparse
import sys
import os

from src.utils import console, format_relative_time, format_message_text
from src.client_manager import get_client, login_user, logout_user
from src.interactive import run_tui

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

def cmd_login(args):
    """Executes the login command."""
    cl = get_client(use_mock=args.mock, force_login=True)
    
    username = args.username
    password = args.password
    
    if not username:
        import questionary
        username = questionary.text("Instagram Username:").ask()
        if not username:
            console.print("[error]Username is required.[/error]")
            return 1
            
    if not password:
        import questionary
        password = questionary.password("Instagram Password:").ask()
        if not password:
            console.print("[error]Password is required.[/error]")
            return 1
            
    success = login_user(cl, username, password, use_mock=args.mock)
    return 0 if success else 1

def cmd_logout(args):
    """Executes the logout command."""
    logout_user(use_mock=args.mock)
    return 0

def cmd_status(args):
    """Executes the status command to verify active session."""
    cl = get_client(use_mock=args.mock)
    
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[warning]⚠️ Not logged in. Run 'login' to authenticate.[/warning]")
        return 1
        
    try:
        if args.mock:
            user = cl._users["10001"]
        else:
            # Fetch own info
            user = cl.user_info_by_username(cl.username)
            
        status_table = Table(title="Session Status", border_style="accent")
        status_table.add_column("Property", style="bold white")
        status_table.add_column("Value", style="cyan")
        
        status_table.add_row("Username", f"@{user.username}")
        status_table.add_row("Full Name", user.full_name or "N/A")
        status_table.add_row("Followers", f"{user.follower_count:,}")
        status_table.add_row("Following", f"{user.following_count:,}")
        status_table.add_row("Posts Count", f"{user.media_count}")
        status_table.add_row("Mode", "Mock Mode (Offline)" if args.mock else "Real API (Online)")
        
        console.print(status_table)
    except Exception as e:
        console.print(f"[error]Error fetching status: {e}[/error]")
        return 1
    return 0

def cmd_feed(args):
    """Executes the feed command to view timeline posts."""
    cl = get_client(use_mock=args.mock)
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[error]❌ Authentication required. Please log in first.[/error]")
        return 1
        
    try:
        console.print(f"[info]Fetching last {args.limit} posts from feed...[/info]")
        feed = cl.get_timeline_feed() or []
        posts = feed[:args.limit]
        
        if not posts:
            console.print("[info]Your feed is empty.[/info]")
            return 0
            
        for i, post in enumerate(posts):
            posted_at = format_relative_time(post.taken_at)
            
            header_text = Text()
            header_text.append(f"@{post.user.username}", style="username")
            if post.user.full_name:
                header_text.append(f" ({post.user.full_name})", style="italic white")
            header_text.append(f" • {posted_at}", style="timestamp")
            
            stats_text = Text()
            stats_text.append(f"❤️ {post.like_count} likes", style="primary")
            stats_text.append("   ")
            stats_text.append(f"💬 {post.comment_count} comments", style="accent")
            
            media_type = "📸 Photo" if post.media_type == 1 else "🎥 Video"
            
            panel_content = f"{post.caption_text or '[italic dim]No caption[/italic dim]'}\n\n{stats_text}"
            panel = Panel(
                panel_content,
                title=header_text,
                title_align="left",
                subtitle=f"[dim]{media_type} | ID: {post.pk} | #{i+1}[/dim]",
                subtitle_align="right",
                border_style="#C13584"
            )
            console.print(panel)
            console.print("")
    except Exception as e:
        console.print(f"[error]Failed to fetch feed: {e}[/error]")
        return 1
    return 0

def cmd_profile(args):
    """Executes the profile command."""
    cl = get_client(use_mock=args.mock)
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[error]❌ Authentication required. Please log in first.[/error]")
        return 1
        
    username = args.username
    if not username:
        username = cl.username
        
    try:
        console.print(f"[info]Fetching profile for @{username}...[/info]")
        user = cl.user_info_by_username(username)
        
        bio = user.biography or "[italic dim]No biography[/italic dim]"
        profile_text = (
            f"[bold]@{user.username}[/bold]\n"
            f"👤 {user.full_name}\n\n"
            f"{bio}\n\n"
            f"📈 [bold]Stats:[/bold]\n"
            f"  • Followers: [accent]{user.follower_count:,}[/accent]\n"
            f"  • Following: [accent]{user.following_count:,}[/accent]\n"
            f"  • Posts: [accent]{user.media_count}[/accent]"
        )
        
        panel = Panel(
            profile_text,
            title="Instagram Profile Info",
            border_style="accent",
            expand=False
        )
        console.print(panel)
    except Exception as e:
        console.print(f"[error]Error fetching profile: {e}[/error]")
        return 1
    return 0

def cmd_post(args):
    """Executes the photo upload command."""
    cl = get_client(use_mock=args.mock)
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[error]❌ Authentication required. Please log in first.[/error]")
        return 1
        
    image_path = args.image_path
    if not args.mock and not os.path.exists(image_path):
        console.print(f"[error]❌ File not found: {image_path}[/error]")
        return 1
        
    caption = args.caption or ""
    
    try:
        console.print(f"[info]Uploading {image_path} to Instagram feed...[/info]")
        media = cl.photo_upload(image_path, caption)
        console.print(f"[success]✓ Upload successful! Code: {media.code} (ID: {media.pk})[/success]")
    except Exception as e:
        console.print(f"[error]Upload failed: {e}[/error]")
        return 1
    return 0

def cmd_inbox(args):
    """Executes the inbox command to show active DM threads."""
    cl = get_client(use_mock=args.mock)
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[error]❌ Authentication required. Please log in first.[/error]")
        return 1
        
    try:
        console.print(f"[info]Fetching inbox threads (limit: {args.limit})...[/info]")
        threads = cl.direct_threads(args.limit)
        
        if not threads:
            console.print("[info]Your direct inbox is empty.[/info]")
            return 0
            
        inbox_table = Table(title="Direct Messages Inbox", border_style="accent")
        inbox_table.add_column("Chat Thread", style="username")
        inbox_table.add_column("Last Message Preview", style="white")
        inbox_table.add_column("Thread ID", style="dim cyan")
        
        for t in threads:
            last_msg = "[No messages]"
            if t.messages:
                msg_obj = t.messages[0]
                last_msg = format_message_text(msg_obj, single_line=True)
                if len(last_msg) > 40:
                    last_msg = last_msg[:37] + "..."
                    
            inbox_table.add_row(f"@{t.thread_title}", last_msg, t.id)
            
        console.print(inbox_table)
    except Exception as e:
        console.print(f"[error]Error fetching inbox: {e}[/error]")
        return 1
    return 0

def cmd_dm(args):
    """Executes the command to send a direct message to a user."""
    cl = get_client(use_mock=args.mock)
    is_logged_in = cl.is_logged_in if args.mock else bool(cl.user_id)
    
    if not is_logged_in:
        console.print("[error]❌ Authentication required. Please log in first.[/error]")
        return 1
        
    username = args.username
    message = args.message
    
    try:
        console.print(f"[info]Sending DM to @{username}...[/info]")
        cl.direct_send(message, recipient_users=[username])
        console.print(f"[success]✓ Message sent to @{username} successfully![/success]")
    except Exception as e:
        console.print(f"[error]Failed to send DM: {e}[/error]")
        return 1
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Instagram Command Line Interface (CLI) & Terminal User Interface (TUI)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "-m", "--mock",
        action="store_true",
        help="Run in offline mock mode using simulated database (perfect for testing/offline runs)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # login command
    login_parser = subparsers.add_parser("login", help="Log in to your Instagram account")
    login_parser.add_argument("-u", "--username", help="Instagram username")
    login_parser.add_argument("-p", "--password", help="Instagram password")
    
    # logout command
    subparsers.add_parser("logout", help="Log out from Instagram (clears sessions)")
    
    # status command
    subparsers.add_parser("status", help="Show current login status and profile info")
    
    # feed command
    feed_parser = subparsers.add_parser("feed", help="Show your home timeline feed")
    feed_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=5,
        help="Number of posts to display (default: 5)"
    )
    
    # profile command
    profile_parser = subparsers.add_parser("profile", help="View a user's profile info")
    profile_parser.add_argument(
        "username",
        nargs="?",
        help="Username of profile to view (defaults to logged-in user)"
    )
    
    # post command
    post_parser = subparsers.add_parser("post", help="Upload a photo to your feed")
    post_parser.add_argument("image_path", help="Path to local image file")
    post_parser.add_argument("caption", nargs="?", help="Caption for the post")
    
    # inbox command
    inbox_parser = subparsers.add_parser("inbox", help="Show recent DM threads in your inbox")
    inbox_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of threads to list (default: 10)"
    )
    
    # dm command
    dm_parser = subparsers.add_parser("dm", help="Send a quick direct message to a user")
    dm_parser.add_argument("username", help="Recipient username")
    dm_parser.add_argument("message", help="Message text content")
    
    # interactive command (TUI)
    subparsers.add_parser("interactive", help="Start the interactive menu (TUI)")
    subparsers.add_parser("tui", help="Start the interactive menu (TUI)")

    # Parse args
    args = parser.parse_args()
    
    # Default to interactive if no subcommand is given
    if not args.command or args.command in ["interactive", "tui"]:
        cl = get_client(use_mock=args.mock)
        run_tui(cl, use_mock=args.mock)
        return 0
        
    # Dispatch commands
    commands_map = {
        "login": cmd_login,
        "logout": cmd_logout,
        "status": cmd_status,
        "feed": cmd_feed,
        "profile": cmd_profile,
        "post": cmd_post,
        "inbox": cmd_inbox,
        "dm": cmd_dm
    }
    
    if args.command in commands_map:
        return commands_map[args.command](args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
