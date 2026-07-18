## D@in Corp

# InternetGuard

Blocks outbound internet access on this PC until a time-limited voucher
code is entered. Two account tiers manage it: a superadmin who controls
admin accounts, and admins who generate vouchers.

## Setup

```
pip install -r requirements.txt
```

Run as Administrator (firewall rules require elevated privileges):

```
python main.py
```

## How it works

- On start, InternetGuard blocks outbound traffic using a Windows Firewall
  rule (`netsh advfirewall`), labeled internally as
  `Microsoft Internet Service 2026 (MIS-26)`.
- A small popup appears centered on screen, always on top of every other
  window, asking for a voucher code. It is **not** fullscreen and can be
  closed (X button) -- but closing it does not unblock the network. The
  firewall rule is controlled independently, so dismissing the popup just
  hides the prompt; the person still has no internet until they reopen it
  and enter a valid code.
- The popup is brought back via the **tray icon** (left-click, or right-click
  for the menu: "Enter voucher code" / "Admin"). There is no Quit/Exit
  option on the plain tray menu by design.
- Launching the app again while it's already running (e.g. clicking the
  taskbar or Start Menu icon a second time) does not start a duplicate
  process -- it just brings the existing popup to the front.
- Logging in as **Admin** opens a panel to generate vouchers (by
  minutes/hours) and change your own password. Admins only see vouchers
  they personally created.
- Logging in as **Superadmin** additionally shows a "Manage Admins" tab:
  create/delete admin accounts, reset any account's password, and see
  every voucher regardless of who created it. Superadmin is also the only
  role that can quit the app entirely (button lives inside the panel, not
  on the tray).
- Once a voucher is redeemed, internet access is unblocked for that
  duration, with a small on-screen countdown. A warning appears 2 minutes
  before time runs out. At expiry, the firewall rule reapplies automatically
  and the popup reappears.

## Default superadmin login

```
Username: su
Password: su2026
```

Change this immediately after first login (My Account tab -> Change my
password). This is a short, guessable default -- fine as a seed value,
not something to leave in place long-term.

## Packaging with Nuitka

```
pip install nuitka
python -m nuitka --standalone --onefile --enable-plugin=pyqt6 ^
  --windows-console-mode=disable ^
  --windows-icon-from-ico=icon.ico ^
  --output-filename=main.exe main.py
```

Notes:
- `--windows-console-mode=disable` suppresses the console window.
- Needs a C compiler on the build machine (MinGW is fetched automatically
  by Nuitka if none is found, or point it at MSVC with `--msvc=latest`).
- Nuitka compiles to C rather than bundling raw bytecode (PyInstaller's
  approach), so the resulting binary is meaningfully harder to decompile
  back into readable Python than a PyInstaller build.
- If the executable name, Task Scheduler task name, and Task Manager
  process name should all read consistently with the firewall rule's
  "Microsoft Internet Service" naming, set `--output-filename` and the
  Task Scheduler task name to match -- the firewall rule name alone won't
  hold up if the exe is still called `InternetGuard.exe` in Task Manager.

## Running at startup, elevated

Use Task Scheduler, not the Startup folder -- the Startup folder does not
grant elevation, so `netsh` calls would silently fail.

1. Trigger: **At log on**, for the specific user account.
2. Action: path to the built `.exe`.
3. Check **"Run with highest privileges."**
4. Set **"Configure for"** to match the installed Windows version.

## Important notes

- This only controls this PC's outbound network traffic; it isn't a
  content filter and doesn't block access from other devices.
- Since the recipient uses the same admin account as you, a technically
  capable user could still disable this (Task Manager, Safe Mode, deleting
  the app). This is a friction/discipline tool for an ordinary user, not a
  defense against a deliberate technical bypass -- see prior project
  discussion.
- On upgrade from an older build that used the previous rule name
  (`InternetGuard_Block_Outbound`), that old rule is not automatically
  removed -- delete it manually via `netsh advfirewall firewall delete
  rule name="InternetGuard_Block_Outbound"` if you're updating an existing
  install rather than starting fresh.
