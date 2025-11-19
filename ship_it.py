import os
import subprocess
import sys

def run_command(command):
    """Runs a terminal command and prints output."""
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        print(f"⚠️ Error running: {command}")
        return False

print("\n--- 🚀 STARTING GITHUB UPLOAD ---")

# 1. Create .gitignore (CRITICAL for security)
print("[1/5] Creating .gitignore safety file...")
gitignore_content = """
venv/
__pycache__/
.DS_Store
.env
*.pyc
"""
with open(".gitignore", "w") as f:
    f.write(gitignore_content)

# 2. Initialize Git
print("[2/5] Initializing Git repository...")
if not os.path.exists(".git"):
    run_command("git init")
    # Mac often defaults to 'master', we want 'main'
    run_command("git branch -M main") 

# 3. Add and Commit
print("[3/5] Snapshotting code...")
run_command("git add .")
run_command('git commit -m "Initial release: Serper Intelligence Hub"')

# 4. Create Repo on GitHub
print("[4/5] Creating remote repository...")
repo_name = input("👉 Enter a name for your repo (e.g. serper-tool): ").strip()
if not repo_name:
    repo_name = "serper-tool"

# This command uses the GitHub CLI you installed earlier
create_cmd = f"gh repo create {repo_name} --public --source=. --remote=origin"
success = run_command(create_cmd)

if success:
    # 5. Push
    print("[5/5] Pushing to GitHub...")
    push_success = run_command("git push -u origin main")
    
    if push_success:
        print(f"\n✅ SUCCESS! Your code is live at: https://github.com/{os.environ.get('USER', 'your-username')}/{repo_name}")
    else:
        print("\n⚠️ Push failed. You might need to run 'gh auth login' again.")
else:
    print("\n⚠️ Repo creation failed.")
    print("Try running 'gh auth login' in the terminal, then run this script again.")