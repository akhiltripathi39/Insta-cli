import os
import questionary
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text

from src.utils import console, clear_screen, get_banner, format_relative_time, format_message_text, get_plain_text

def run_tui(cl, use_mock=False):
    """Main loop for the interactive Terminal User Interface (TUI)."""
    # Check if client is logged in
    # For mock, we check is_logged_in. For real, we check if cl.user_id exists.
    is_logged_in = False
    if use_mock:
        is_logged_in = cl.is_logged_in
    else:
        is_logged_in = bool(cl.user_id)

    if not is_logged_in:
        clear_screen()
        console.print(get_banner())
        console.print("[error]❌ No active session. Please log in first using 'login' command.[/error]")
        return

    # Cache own profile details to show in banner
    my_username = "Logged In"
    try:
        def is_invalid(val):
            if not val:
                return True
            s = str(val).strip().lower()
            return s in ("none", "null", "")

        curr_username = getattr(cl, "username", None)
        if is_invalid(curr_username):
            from src.client_manager import get_session_path, save_client_settings
            import json
            session_path = get_session_path(use_mock)
            cached_username = None
            if session_path.exists():
                try:
                    with open(session_path, "r") as f:
                        data = json.load(f)
                    cached_username = data.get("username")
                except Exception:
                    pass
            
            if not is_invalid(cached_username):
                cl.username = cached_username
            elif getattr(cl, "user_id", None):
                try:
                    resolved = cl.username_from_user_id(cl.user_id)
                    if not is_invalid(resolved):
                        cl.username = resolved
                        save_client_settings(cl, session_path, resolved)
                except Exception:
                    pass
        
        final_username = getattr(cl, "username", None)
        if is_invalid(final_username):
            my_username = "Logged In"
        else:
            my_username = final_username
    except Exception:
        my_username = "Logged In"

    while True:
        clear_screen()
        console.print(get_banner())
        console.print(Align.center(f"[accent]● Logged in as: @{my_username} ●[/accent]\n"))
        
        choice = questionary.select(
            "Select an action:",
            choices=[
                "👤 View Profile (Search/Own)",
                "💬 Direct Messages (Inbox)",
                "🚪 Logout",
                "❌ Exit"
            ],
            style=questionary.Style([
                ('pointer', 'fg:#C13584 bold'),
                ('highlighted', 'fg:#E1306C bold'),
                ('selected', 'fg:#405DE6'),
            ])
        ).ask()

        if not choice:
            break

        if "View Profile" in choice:
            browse_profiles(cl)
        elif "Direct Messages" in choice:
            browse_inbox(cl)
        elif "Logout" in choice:
            from src.client_manager import logout_user
            logout_user(use_mock)
            break
        elif "Exit" in choice:
            break

def browse_profiles(cl):
    """Allows searching a user and viewing their bio, stats, and posts."""
    clear_screen()
    username = questionary.text("Enter username (press Enter for your own):").ask()
    
    if username is None:
        return
        
    username = username.strip()
    if not username:
        # Default to logged-in user
        username = cl.username

    clear_screen()
    console.print(f"[info]Fetching profile of @{username}...[/info]")
    
    try:
        user = cl.user_info_by_username(username)
    except Exception as e:
        console.print(f"[error]Failed to fetch user profile: {e}[/error]")
        questionary.press_any_key_to_continue().ask()
        return

    clear_screen()
    
    # Profile Card
    title_text = Text(f"👤 {user.full_name} (@{user.username})", style="primary")
    
    # Stats table
    stats_table = Table.grid(padding=(0, 4))
    stats_table.add_column(style="bold white")
    stats_table.add_column(style="accent")
    
    stats_table.add_row("Posts:", f"{user.media_count}")
    stats_table.add_row("Followers:", f"{user.follower_count:,}")
    stats_table.add_row("Following:", f"{user.following_count:,}")
    
    bio_content = user.biography or "[dim italic]No bio[/dim italic]"
    
    profile_panel = Panel(
        f"{bio_content}\n\n"
        f"[bold]Stats:[/bold]\n"
        f"  • Posts: [accent]{user.media_count}[/accent]\n"
        f"  • Followers: [accent]{user.follower_count:,}[/accent]\n"
        f"  • Following: [accent]{user.following_count:,}[/accent]",
        title=title_text,
        title_align="left",
        border_style="accent",
        width=60
    )
    
    console.print(profile_panel)
    console.print("\n")

    # Options
    choices = ["🔙 Back to Menu"]
    if user.media_count > 0:
        choices.insert(0, "📸 View Posts")
        
    choice = questionary.select(
        "Profile Action:",
        choices=choices
    ).ask()

    if choice == "📸 View Posts":
        view_user_posts(cl, user)

def view_user_posts(cl, user):
    """Displays posts for a specific user."""
    clear_screen()
    console.print(f"[info]Fetching posts for @{user.username}...[/info]")
    
    try:
        posts = cl.user_medias(user.pk, amount=15)
    except Exception as e:
        console.print(f"[error]Failed to fetch posts: {e}[/error]")
        questionary.press_any_key_to_continue().ask()
        return

    if not posts:
        console.print(f"[info]@{user.username} has no posts.[/info]")
        questionary.press_any_key_to_continue().ask()
        return

    index = 0
    total = len(posts)

    while True:
        clear_screen()
        post = posts[index]
        posted_at = format_relative_time(post.taken_at)
        
        # Build post header
        header_text = Text()
        header_text.append(f"@{user.username}", style="username")
        header_text.append(f" • {posted_at}", style="timestamp")
        
        # Build stats text
        stats_text = Text()
        stats_text.append(f"❤️ {post.like_count} likes", style="primary")
        stats_text.append("   ")
        stats_text.append(f"💬 {post.comment_count} comments", style="accent")
        
        caption = post.caption_text or "[italic dim]No caption[/italic dim]"
        
        post_panel = Panel(
            f"{caption}\n\n{stats_text}",
            title=header_text,
            title_align="left",
            subtitle=f"[dim]Post {index + 1}/{total} (ID: {post.pk})[/dim]",
            subtitle_align="right",
            border_style="#E1306C"
        )
        
        console.print(post_panel)
        console.print("\n")

        # Options
        actions = []
        if index < total - 1:
            actions.append("▶ Next Post")
        if index > 0:
            actions.append("◀ Previous Post")
        actions.extend(["❤️ Like", "💬 Comment", "🔙 Back to Profile"])
        
        action = questionary.select(
            "Post Options:",
            choices=actions
        ).ask()

        if not action or "Back to Profile" in action:
            break
        elif "Next Post" in action:
            index += 1
        elif "Previous Post" in action:
            index -= 1
        elif "Like" in action:
            try:
                cl.media_like(post.id)
                post.like_count += 1
                console.print("[success]✓ Liked![/success]")
                import time
                time.sleep(1)
            except Exception as e:
                console.print(f"[error]Error liking post: {e}[/error]")
                time.sleep(1.5)
        elif "Comment" in action:
            text = questionary.text("Type your comment:").ask()
            if text:
                try:
                    cl.media_comment(post.id, text)
                    post.comment_count += 1
                    console.print("[success]✓ Comment posted![/success]")
                    import time
                    time.sleep(1)
                except Exception as e:
                    console.print(f"[error]Error commenting: {e}[/error]")
                    time.sleep(1.5)

def browse_inbox(cl):
    """Shows active DM threads and enters real-time interactive chats."""
    from questionary import Choice
    while True:
        clear_screen()
        console.print("[info]Loading direct messages inbox...[/info]")
        
        try:
            threads = cl.direct_threads(amount=20)
        except Exception as e:
            console.print(f"[error]Failed to fetch direct messages: {e}[/error]")
            questionary.press_any_key_to_continue().ask()
            return

        if not threads:
            console.print("[info]Your inbox is empty. Start a chat with the search command![/info]")
            questionary.press_any_key_to_continue().ask()
            return

        # Map threads for selection list
        choices = []
        
        for t in threads:
            # Title of thread
            title = t.thread_title
            
            # Get last message snippet
            last_msg = ""
            if t.messages:
                msg_obj = t.messages[0]
                last_msg = format_message_text(msg_obj, single_line=True)
                # Truncate message snippet if long
                if len(last_msg) > 35:
                    last_msg = last_msg[:32] + "..."
            else:
                last_msg = "[No messages]"
                
            choices.append(Choice(
                title=[
                    ('fg:#C13584', '💬 '),
                    ('fg:magenta bold', f"@{title}"),
                    ('', f" - {last_msg}")
                ],
                value=t.id
            ))

        choices.append(Choice(title="🆕 Send Message to New User", value="new_user"))
        choices.append(Choice(title="🔙 Back to Main Menu", value="back"))

        choice = questionary.select(
            "Inbox - Select a chat thread:",
            choices=choices
        ).ask()

        if not choice or choice == "back":
            return
        elif choice == "new_user":
            send_new_message_interactive(cl)
        else:
            interactive_chat(cl, choice)

async def poll_for_updates(cl, thread_id, current_thread_container, stop_event, limit_container):
    from prompt_toolkit.application.current import get_app
    import asyncio
    from datetime import datetime, timezone
    while not stop_event.is_set():
        try:
            # Check stop_event every 100ms for total of 3 seconds
            for _ in range(30):
                if stop_event.is_set():
                    return
                await asyncio.sleep(0.1)
                
            # If mock mode, let's randomly append a reply from the other user to simulate a live chat
            if cl.__class__.__name__ == "MockClient":
                import random
                if random.random() < 0.25:
                    current_thread = current_thread_container[0]
                    recipient = current_thread.users[0]
                    replies = [
                        "That sounds awesome!",
                        "Indeed, Python terminal UI is super cool.",
                        "Are you testing the live refresh right now?",
                        "Let's grab a coffee later!",
                        "Haha that's funny!",
                        "Wow, look at this update!",
                    ]
                    from src.mock_client import MockDirectMessage
                    new_msg = MockDirectMessage(
                        id=f"msg_reply_{random.randint(10000, 99999)}",
                        user_id=recipient.pk,
                        text=random.choice(replies),
                        timestamp=datetime.now(timezone.utc)
                    )
                    cl._threads[thread_id].messages.insert(0, new_msg)

            # Fetch latest thread info in a background thread
            new_thread = await asyncio.to_thread(cl.direct_thread, thread_id, amount=limit_container[0])
            current_thread = current_thread_container[0]
            
            # Compare latest message
            new_ids = {m.id for m in new_thread.messages if getattr(m, "id", None) and m.id}
            curr_ids = {m.id for m in current_thread.messages if getattr(m, "id", None) and m.id}
            
            # 1. New messages from the other user (or server synced)
            has_incoming = bool(new_ids - curr_ids)
            
            # 2. Reactions changed
            new_reactions_count = sum(len(getattr(m.reactions, "emojis", []) or []) for m in new_thread.messages if getattr(m, "reactions", None))
            curr_reactions_count = sum(len(getattr(m.reactions, "emojis", []) or []) for m in current_thread.messages if getattr(m, "reactions", None))
            reactions_changed = (new_reactions_count != curr_reactions_count)
            
            should_update = has_incoming or reactions_changed
            
            # If the server has caught up with all our locally sent messages (so new_ids is a superset of curr_ids),
            # we sync our local thread list with the server's official state
            if not should_update and curr_ids and new_ids.issuperset(curr_ids):
                if new_ids != curr_ids:
                    should_update = True
                else:
                    # Keep local and server in sync anyway without redraw to update any internal state
                    current_thread_container[0] = new_thread
            
            if should_update:
                # Update the container
                current_thread_container[0] = new_thread
                # Force refresh of the active prompt
                try:
                    app = get_app()
                    current_text = app.current_buffer.text
                    app.exit(result=("/refresh", current_text))
                except Exception:
                    pass
        except Exception:
            pass

def interactive_chat(cl, thread_id):
    """Real-time chat loop inside a DM thread."""
    clear_screen()
    console.print("[info]Loading chat history...[/info]")
    
    try:
        thread = cl.direct_thread(thread_id)
    except Exception as e:
        console.print(f"[error]Failed to load chat: {e}[/error]")
        questionary.press_any_key_to_continue().ask()
        return

    thread_container = [thread]
    typed_buffer = ""

    import asyncio

    async def chat_loop_async():
        nonlocal typed_buffer
        stop_event = asyncio.Event()
        limit_container = [15]
        
        # Start background polling task
        poll_task = asyncio.create_task(poll_for_updates(cl, thread_id, thread_container, stop_event, limit_container))
        
        try:
            while True:
                current_thread = thread_container[0]
                
                import io
                from rich.console import Console
                from src.utils import instagram_theme
                import os

                string_io = io.StringIO()
                temp_console = Console(file=string_io, theme=instagram_theme, width=console.width)
                
                # Chat banner
                temp_console.print(Panel(
                    Align.center(f"[bold #405DE6]Chatting with @{current_thread.thread_title}[/bold #405DE6]"),
                    border_style="accent"
                ))
                temp_console.print("")

                # Format and show messages (up to msg_limit last messages)
                filtered_messages = []
                for msg in current_thread.messages:
                    msg_text = format_message_text(msg, single_line=False)
                    msg_text_plain = get_plain_text(msg_text)
                    item_type = getattr(msg, "item_type", None)
                    if item_type == "action_log":
                        if msg_text_plain == "[Action Log]" or "liked" in msg_text_plain.lower() or "reacted" in msg_text_plain.lower():
                            continue
                    filtered_messages.append(msg)

                recent_messages = filtered_messages[:limit_container[0]]
                recent_messages = list(reversed(recent_messages))
                
                for msg in recent_messages:
                    sender_id = msg.user_id
                    
                    # Format time
                    time_str = format_relative_time(msg.timestamp)
                    
                    # Identify sender
                    is_me = (str(sender_id) == str(cl.user_id))
                    
                    if is_me:
                        sender_label = "[accent]You[/accent]"
                        align = "right"
                        border_color = "accent"
                    else:
                        sender_label = f"[username]@{current_thread.thread_title}[/username]"
                        align = "left"
                        border_color = "#C13584"
                        
                    msg_text = format_message_text(msg, single_line=False)

                    # Format reactions (emojis under message body)
                    reactions_str = ""
                    reactions = getattr(msg, "reactions", None)
                    if reactions:
                        emojis = getattr(reactions, "emojis", []) or []
                        reactions_list = []
                        for r in emojis:
                            emoji_val = getattr(r, "emoji", None)
                            if emoji_val:
                                reactions_list.append(emoji_val)
                        likes_count = getattr(reactions, "likes_count", 0) or 0
                        if likes_count > len(reactions_list):
                            for _ in range(likes_count - len(reactions_list)):
                                reactions_list.append("❤️")
                        if reactions_list:
                            reactions_str = "\n" + " ".join(reactions_list)

                    from rich.console import Group
                    components = [msg_text]
                    if reactions_str:
                        components.append(Text(reactions_str))
                    components.append(Text(time_str, style="dim"))

                    text_p = Panel(
                        Group(*components),
                        title=sender_label,
                        title_align=align,
                        border_style=border_color,
                        width=50
                    )
                    
                    # Use rich Align for styling DMs on left/right side of screen
                    if is_me:
                        temp_console.print(Align.right(text_p))
                    else:
                        temp_console.print(Align.left(text_p))
                
                # Retrieve the full rendered string
                rendered_text = string_io.getvalue()
                
                # Clear and print with bottom-anchoring padding
                clear_screen()
                console.print(rendered_text, end="")
                
                # Pad out empty space to push the prompt to the bottom
                try:
                    terminal_height = os.get_terminal_size().lines
                except Exception:
                    terminal_height = 24
                
                printed_lines = len(rendered_text.splitlines())
                input_area_height = 4  # Divider line + Prompt + Guidelines + spacing offset
                padding_lines = terminal_height - printed_lines - input_area_height
                
                if padding_lines > 0:
                    console.print("\n" * padding_lines, end="")
                
                # Setup escape key binding to exit the chat
                from prompt_toolkit.key_binding import KeyBindings
                from prompt_toolkit.keys import Keys

                kb = KeyBindings()
                @kb.add(Keys.Escape)
                def _(event):
                    event.app.exit(result="/exit")

                # Type Box Layout
                from rich.rule import Rule
                console.print(Rule(style="accent"))
                # User input prompt
                message_text = await questionary.text(
                    "",
                    qmark=">",
                    placeholder="Message...",
                    default=typed_buffer,
                    key_bindings=kb
                ).ask_async()
                console.print(" [dim]Esc = Go Back | Empty = Refresh | /load = Load Older Chats | /exit = Exit[/dim]")

                if message_text is None:
                    break
                    
                if isinstance(message_text, tuple) and message_text[0] == "/refresh":
                    typed_buffer = message_text[1]
                    continue
                    
                typed_buffer = ""
                message_text = message_text.strip()
                if not message_text:
                    # Refresh chat from server manually
                    clear_screen()
                    console.print("[info]Refreshing chat history from server...[/info]")
                    try:
                        new_thread = await asyncio.to_thread(cl.direct_thread, thread_id, amount=limit_container[0])
                        thread_container[0] = new_thread
                    except Exception as e:
                        console.print(f"[error]Failed to refresh chat: {e}[/error]")
                        await asyncio.sleep(1.5)
                    continue

                if message_text.lower() == "/load":
                    limit_container[0] += 15
                    clear_screen()
                    console.print(f"[info]Loading older messages (limit: {limit_container[0]})...[/info]")
                    try:
                        new_thread = await asyncio.to_thread(cl.direct_thread, thread_id, amount=limit_container[0])
                        thread_container[0] = new_thread
                    except Exception as e:
                        console.print(f"[error]Failed to load older messages: {e}[/error]")
                        await asyncio.sleep(1.5)
                    continue
                    
                if message_text.lower() in ["/exit", "/quit", "/q"]:
                    break
                    
                # Send message
                try:
                    sent_msg = await asyncio.to_thread(cl.direct_send, message_text, thread_ids=[current_thread.id])
                    # Fix Pydantic model text / item_type / user_id attributes if they are returned as None/empty
                    if not getattr(sent_msg, "text", None):
                        sent_msg.text = message_text
                    if not getattr(sent_msg, "item_type", None):
                        sent_msg.item_type = "text"
                    if not getattr(sent_msg, "user_id", None) or sent_msg.user_id == "":
                        sent_msg.user_id = str(cl.user_id)
                    # Update local container list instantly
                    thread_container[0].messages.insert(0, sent_msg)
                except Exception as e:
                    console.print(f"[error]Failed to send message: {e}[/error]")
                    await asyncio.sleep(1.5)
        finally:
            stop_event.set()
            poll_task.cancel()
            try:
                await poll_task
            except BaseException:
                pass

    try:
        asyncio.run(chat_loop_async())
    except KeyboardInterrupt:
        pass

def send_new_message_interactive(cl):
    """Allows searching a user and sending a direct message to start a new chat thread."""
    clear_screen()
    username = questionary.text("Enter username to message:").ask()
    if not username or not username.strip():
        return
        
    username = username.strip()
    
    # Try sending a message
    message_text = questionary.text(f"Type initial message to @{username}:").ask()
    if not message_text or not message_text.strip():
        return
        
    try:
        console.print(f"[info]Sending message to @{username}...[/info]")
        # instagrapi direct_send resolves username automatically if recipient_users contains username
        cl.direct_send(message_text.strip(), recipient_users=[username])
        console.print("[success]✓ Message sent successfully![/success]")
        import time
        time.sleep(1)
    except Exception as e:
        console.print(f"[error]Failed to send message: {e}[/error]")
        questionary.press_any_key_to_continue().ask()


