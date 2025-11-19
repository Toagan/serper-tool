import subprocess
import sys

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error running: {command}")
        return False

print("\n--- 🔄 PUSHING V2 UPDATES TO GITHUB ---")

# 1. Stage all new changes (the new app.py)
print("[1/3] Staging changes...")
run_command("git add .")

# 2. Save the snapshot (Commit)
print("[2/3] Committing 'V2 Optimization'...")
# We use || true to prevent crashing if there are no new changes
subprocess.call('git commit -m "Upgrade: V2 UI and Performance Improvements"', shell=True)

# 3. Upload to Cloud (Push)
print("[3/3] Pushing to GitHub...")
success = run_command("git push origin main")

if success:
    print("\n✅ SUCCESS! Your V2 code is now live on GitHub.")
else:
    print("\n⚠️ Push failed. Try running 'git pull' first if you made changes online.")