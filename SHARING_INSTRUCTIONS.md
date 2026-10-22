# How to Share Display Buddy (Step-by-Step Guide)

Sharing **Display Buddy** with another person (partner, friend, or family) is designed to be **completely effortless** with zero technical barrier for them.

---

## 🎁 Recommended Way to Share: `DisplayBuddy_Portable.zip`

This is the **gold standard** for non-technical recipients:
- **No Python needed** on their computer.
- **No command line / terminal** needed.
- **No admin privileges** required.
- Works on Windows 10 & Windows 11 (64-bit).

### What They Do (Takes 5 seconds):
1. **Unzip** `DisplayBuddy_Portable.zip` to their Desktop or Documents folder.
2. **Double-click** `DisplayBuddy.exe`.
3. The companion immediately pops up on their taskbar, walking around and greeting them! ✨

---

## ✍️ Step 1: Personalize Before Sending (Optional)

If you want the companion to say specific inside jokes, nicknames, or personal notes when they open it, you can edit the dialogues before zipping or right inside the folder:

1. Open:
   `skins/default_companion/dialogues.json`
2. Open it in **Notepad** (or any text editor).
3. Customize:
   - **`initials`**:
     ```json
     "initials": {
       "companion": "HH",
       "visitor": "S"
     }
     ```
     *(Displays on the circular badge under each photo)*
   - **`click_quotes`**: What he says when they click on him.
   - **`idle_quotes`**: Spontaneous thoughts he shares while walking along the taskbar.
   - **`interaction_dialogues`**: What they say to each other during the kiss and hug actions!
4. Save the file.

---

## 📤 Step 2: How to Send the File

Because `DisplayBuddy_Portable.zip` contains the self-contained Python & Qt runtime, its file size is ~50–65 MB.

### Best Ways to Send:
1. **Google Drive / OneDrive / Dropbox**:
   - Upload `DisplayBuddy_Portable.zip`.
   - Right-click -> "Share" -> "Anyone with the link can view".
   - Send the link to your friend!
2. **Telegram / Discord / WhatsApp Web**:
   - Telegram supports files up to 2GB.
   - WhatsApp supports files up to 2GB (send as "Document").
3. **USB Flash Drive**:
   - Simply copy the folder directly onto a flash drive and hand it to them.

---

## 💡 What to Tell the Recipient (Copy & Paste Message)

You can copy and send them this exact message:

> *"Hey! I made this animated desktop companion for your Windows PC! 🐾✨*
>
> *Here is how to run it:*
> *1. Download and extract the ZIP file.*
> *2. Open the folder and double-click `DisplayBuddy.exe`.*
> *3. He’ll pop up on your taskbar!*
>
> *Fun things you can do:*
> *• **Click him** to hear what he has to say.*
> *• **Drag him** anywhere on your screen and watch him fall (or hang mid-air!).*
> *• **Right-click him** to hug him, get a kiss, or change his outfit!*
> *• Look for his icon in your taskbar tray (bottom-right near the clock) to mute or exit.*
>
> *Enjoy! ❤️"*

---

## ⚙️ FAQ & Tips for Recipients

### 1. Windows SmartScreen ("Windows protected your PC")
Because this is a personal custom-built application and not published via the Microsoft Store, Windows might display a blue SmartScreen prompt the very first time it runs:
- **How to bypass**: Simply click **"More info"** -> **"Run anyway"**. It will remember their choice and never prompt again.

### 2. Want it to start automatically when the computer turns on?
1. Right-click `DisplayBuddy.exe` -> **"Create shortcut"**.
2. Press `Win + R` on the keyboard, type `shell:startup`, and press Enter.
3. Paste the shortcut into that folder.

### 3. How to close or restart it?
- Look in the bottom-right corner of the Windows taskbar (system tray near the clock).
- Right-click the companion icon -> click **"Exit Display Buddy"**.
- Alternatively, double-click `Stop_DisplayBuddy.bat` in the folder.
