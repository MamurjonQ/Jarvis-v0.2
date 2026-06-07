import os
import re
import subprocess
from pathlib import Path
from collections import deque

# --- SAFETY: YOU CONFIRM EVERY ACTION ---
CONFIRM_REQUIRED = True  # SET TO False ONLY IF YOU TRUST IT 100% (NOT RECOMMENDED)
BOT_NAME = "PathwayAssistant"

# --- PERSONALIZE THESE FOR YOUR WORKFLOW ---
COMMAND_MAP = {
    "download": {
        "trigger": ["download", "get", "fetch"],
        "action": lambda url: f"curl -L -o ~/Downloads/{url.split('/')[-1]} {url}",
        "confirm_msg": "Download this file? (y/n): "
    },
    "open": {
        "trigger": ["open", "launch", "start"],
        "action": lambda app: f"start {app}" if os.name == 'nt' else f"open {app}",
        "confirm_msg": "Open this application? (y/n): "
    },
    "list": {
        "trigger": ["list", "show", "ls"],
        "action": lambda path: f"dir {path}" if os.name == 'nt' else f"ls -la {path}",
        "confirm_msg": "List this directory? (y/n): "
    }
}
# --- END PERSONALIZATION ---

def normalize_text(text):
    return re.sub(r'[,.!?;:]', '', text.lower()).strip()

def understand_intent(user_input):
    """Figure out what the user wants to do"""
    norm = normalize_text(user_input)
    for cmd, config in COMMAND_MAP.items():
        if any(trigger in norm for trigger in config["trigger"]):
            # Extract target (simplified — real version would use NLP)
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in config["trigger"] and i+1 < len(words):
                    target = " ".join(words[i+1:])
                    return cmd, target
    return None, None

def get_response(user_input, history):
    """Generate response + suggest action (if any)"""
    norm = normalize_text(user_input)

    # Greetings/farewells (unchanged from before)
    if any(g in norm for g in ["hi", "hello", "hey"]):
        return f"👋 Hey! I'm {BOT_NAME}. What should I help you with?"
    if any(f in norm for f in ["bye", "exit"]):
        return "👋 Talk soon!"

    # Try to understand intent
    cmd, target = understand_intent(user_input)
    if cmd and target:
        action_cmd = COMMAND_MAP[cmd]["action"](target)
        return f"⚙️ I understand: You want to {cmd} '{target}'.\n" \
               f"This would run: `{action_cmd}`\n" \
               f"{COMMAND_MAP[cmd]['confirm_msg']}"

    # Fallback (context-aware)
    if len(history) > 0 and "thank" in normalize_text(history[-1][0]):
        return "Happy to help! What else?"
    return f"I'm not sure how to help with that. Try:\n" \
           f"• 'download [url]'\n" \
           f"• 'open [app]'\n" \
           f"• 'list [folder]'"

def chat_loop():
    print("\n" + "="*50)
    print(f"  🤖 {BOT_NAME} is online! Type 'bye' to exit.")
    print("  🔐 SAFETY: I'll ASK before running ANY command")
    print("  Try: 'download https://python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe'")
    print("="*50 + "\n")

    history = deque(maxlen=2)

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        history.append((user_input, ""))
        bot_response = get_response(user_input, [h[0] for h in history])
        history[-1] = (history[-1][0], bot_response)

        print(f"\n{BOT_NAME}: {bot_response}\n")

        # Handle confirmation flow
        if "⚙️ I understand:" in bot_response and CONFIRM_REQUIRED:
            user_confirm = input("Your choice (y/n): ").strip().lower()
            if user_confirm == 'y':
                cmd, target = understand_intent(user_input)
                if cmd and target:
                    action_cmd = COMMAND_MAP[cmd]["action"](target)
                    print(f"\n💻 Running: {action_cmd}")
                    try:
                        # REAL EXECUTION (only after YOUR confirmation)
                        result = subprocess.run(
                            action_cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        print(f"✅ Output:\n{result.stdout}")
                        if result.stderr:
                            print(f"⚠️ Stderr:\n{result.stderr}")
                    except Exception as e:
                        print(f"❌ Error: {str(e)}")
                print()  # New line for clarity
            else:
                print("👍 Action cancelled. What else?\n")

        # Check for exit
        if any(f in normalize_text(user_input) for f in ["bye", "exit"]):
            break

if __name__ == "__main__":
    chat_loop()