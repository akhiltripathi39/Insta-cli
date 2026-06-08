# GitHub Repository Setup Guide 🚀

Follow these step-by-step terminal instructions to initialize a local Git repository, commit your files, and push them to a new GitHub repository.

---

## Step 1: Create a Repository on GitHub
1. Go to [GitHub](https://github.com) and log in.
2. In the top-right corner, click the **`+`** dropdown and select **New repository**.
3. Name your repository (e.g., `instagram-cli`).
4. Keep the repository public/private as per your preference.
5. **CRITICAL**: Do **NOT** initialize the repository with a README, `.gitignore`, or license. We already have these files locally.
6. Click **Create repository**.

---

## Step 2: Initialize Git Locally
Open your terminal, navigate to your project root, and initialize Git:

```bash
cd /home/akhil/declutter/Gemini_chats/instagram_cli
git init
```

---

## Step 3: Configure Git (Optional but Recommended)
If you haven't configured your global Git user identity, do so now:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 4: Verify Exclusions in `.gitignore`
Make sure the `.gitignore` file is in place at the root directory so local virtual environments, OS files, and session cookie caches are not tracked:

```bash
cat .gitignore
```
*You should see `venv/`, `__pycache__/`, `session.json`, `*session.json`, and `.DS_Store` listed.*

---

## Step 5: Stage Files
Stage all files to be tracked by Git:

```bash
git add .
```

To verify which files are staged for commit, run:
```bash
git status
```

---

## Step 6: Commit Staged Files
Commit the files with an initial commit message:

```bash
git commit -m "Initial commit: CLI and TUI for Instagram with OSC 8 support"
```

---

## Step 7: Set the Main Branch Name
Rename the default branch to `main` (if not already default):

```bash
git branch -M main
```

---

## Step 8: Link to GitHub Remote
Copy the repository URL from your newly created GitHub page (choose HTTPS or SSH) and run:

```bash
# Using HTTPS (replace with your username/repo):
git remote add origin https://github.com/your-username/instagram-cli.git

# OR using SSH:
# git remote add origin git@github.com:your-username/instagram-cli.git
```

---

## Step 9: Push the Repository to GitHub
Push your commits to the `main` branch of the remote repository:

```bash
git push -u origin main
```

Your code is now published on GitHub! 🌟
