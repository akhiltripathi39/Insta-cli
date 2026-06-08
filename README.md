# Instagram CLI & TUI 📸 💻

A beautiful, functional, and robust Command Line Interface (CLI) and Terminal User Interface (TUI) for Instagram, written in Python.

This project is a modern, stable alternative to older Node.js-based CLI clients (which often fail due to outdated private API wrappers). By utilizing the actively maintained `instagrapi` library and styling the output with `rich` and `questionary`, it delivers a premium, keyboard-driven Instagram experience directly inside your terminal.

---

## Features

- 🔐 **Secure & Robust Authentication**: Handles 2FA/MFA verification codes and suspicious login security challenges (SMS/Email code prompts) interactively.
- 🍪 **Session Caching**: Saves cookies and session states to `~/.config/instagram_cli/` so you only have to log in once.
- 📖 **Timeline Feed Browser**: Scroll through your feed post-by-post, view captions/likes/comments, and interact (like/comment) directly.
- 👤 **Profile Inspector**: Search for any user to check their bio, follower/following count, and browse their recent posts.
- 💬 **DM Chat Engine**: Real-time conversational interface for reading, refreshing, and replying to Direct Messages.
- 📸 **Photo Uploader**: Post local JPG/PNG images straight to your feed with custom captions.
- 🛠 **Offline Mock Mode**: A fully-featured simulated database that runs offline without any Instagram credentials (perfect for testing and demonstrations!).

---

## Installation & Setup

### 1. Clone or copy this repository
Ensure you are in the project root directory:
```bash
cd /home/akhil/declutter/Gemini_chats/instagram_cli
```

### 2. Set up virtual environment and install dependencies
Use the newly created `requirements.txt` to install the pinned dependencies:
```bash
# Create the virtual environment
python3 -m venv venv

# Activate and install dependencies
./venv/bin/pip install -r requirements.txt
```

### 3. Run the CLI
The main wrapper script `instagram-cli` runs the application using the local virtual environment:
```bash
./instagram-cli
```

---

## How to Use the CLI

### 1. Offline Demonstration (Try it first!)
You can test the entire client offline without inputting any real Instagram details by appending the `-m` or `--mock` flag to any command.

```bash
# Start the interactive TUI in mock mode
./instagram-cli --mock

# Check login status (will say not logged in initially)
./instagram-cli --mock status

# Log in using dummy details
./instagram-cli --mock login -u test_user -p test_password

# View status now
./instagram-cli --mock status

# Read your feed
./instagram-cli --mock feed --limit 2

# Search a user profile (e.g. nasa)
./instagram-cli --mock profile nasa

# View your DMs inbox
./instagram-cli --mock inbox

# Send a quick direct message
./instagram-cli --mock dm alice "Hey Alice, this is sent from the terminal!"

# Upload a mock image
./instagram-cli --mock post mock_path.jpg "Cruising through space"

# Logout and clear cache
./instagram-cli --mock logout
```

### 2. Live Mode (Using your real Instagram Account)
To connect to your real account, omit the `--mock` flag.

#### Step 1: Login
```bash
./instagram-cli login
```
*You will be prompted to securely type your Username and Password. If your account has 2FA enabled, it will prompt you for the verification code. If Instagram triggers a verification check, you will be prompted for the code sent to your SMS/Email.*

#### Step 2: Run the Interactive TUI
Once logged in, running the CLI with no arguments starts the full terminal application:
```bash
./instagram-cli
```
Use the arrow keys and **Enter** to navigate menus, read DMs, send messages, search profiles, and browse your feed!

#### Step 3: Run single-command CLI utilities
You can also perform quick actions directly from your shell without loading the full menu:
```bash
# Print last 10 posts from feed
./instagram-cli feed --limit 10

# Search user stats
./instagram-cli profile natgeo

# Send a message to a friend
./instagram-cli dm my_friend_username "Are you free today?"

# Upload an image file
./instagram-cli post /path/to/my_photo.jpg "Check out this shot! #nature"

# Clear session cookies & logout
./instagram-cli logout
```

---

## Safety and Guidelines

> [!WARNING]
> This CLI uses an unofficial wrapper (`instagrapi`) around Instagram's private mobile API. 
> - **Avoid aggressive automation**: Sending too many requests, likes, comments, or DMs in a short span can trigger rate limits or flag your account.
> - **Use a stable connection**: Logging in from frequently changing IPs or VPNs may trigger security verification challenges.
> - **Account Risk**: While `instagrapi` is built to look like a real mobile app client, Meta does not officially support third-party apps. Use responsibly.

---

## File Structure

- `instagram-cli`: Main executable entry-point shell script.
- [src/cli.py](file:///home/akhil/declutter/Gemini_chats/instagram_cli/src/cli.py): Main command line argument parser and dispatcher.
- [src/interactive.py](file:///home/akhil/declutter/Gemini_chats/instagram_cli/src/interactive.py): Interactive TUI engine (feed browser, chat client, profile view).
- [src/client_manager.py](file:///home/akhil/declutter/Gemini_chats/instagram_cli/src/client_manager.py): Session cache manager, 2FA, and verification challenge handler.
- [src/mock_client.py](file:///home/akhil/declutter/Gemini_chats/instagram_cli/src/mock_client.py): Offline Instagram Client mock database.
- [src/utils.py](file:///home/akhil/declutter/Gemini_chats/instagram_cli/src/utils.py): Console styling, custom themes, ASCII arts, and helpers.
