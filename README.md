# AdVenture Capitalist Access

AdVenture Capitalist Access adds keyboard navigation and NVDA speech to the Windows Steam version of AdVenture Capitalist.

AdVenture Capitalist is an idle game about buying businesses, hiring managers, purchasing upgrades, and restarting planets with investors so the next run earns money more quickly. The original interface is built mainly for a mouse. This mod gives the main game screen, menus, dialogs, store, rewards, and several secondary panels a consistent keyboard interface.

## Download and install

[Download AdCapAccessPatcher.exe](https://github.com/ShotgunSpoon/adCapAccess/releases/download/v1.2.4.3/AdCapAccessPatcher.exe).

1. Close AdVenture Capitalist.
2. Start the patcher.
3. Check the game folder. The default Steam location is already filled in.
4. Choose **Install or Update**.
5. Start the game normally through Steam.

The patcher backs up the original game assembly before changing it. **Repair** downloads and installs the current mod files again. **Restore Original Game** removes the mod and restores the patcher-created backup.

The patcher executable is currently unsigned, so Windows may show a warning the first time it runs.

Patcher 1.2.4.3 retains the Version 1.2.1 self-update-loop fix and the Version 1.1 custom game folder fix.

Version 1.2.4.3 lets you hold Enter or Space on a business purchase row to buy repeatedly while retaining the game's native purchase sound. The mod announces the cumulative purchase result after you release the key. It also prevents Angel-investment dialogs from repeating when the projected value changes. It retains the event timing and return shortcuts, Managers navigation fixes, and the accessible event interface.

## Keys

These keys work while the game window has focus.

| Key | Action |
| --- | --- |
| Left and Right Arrow | Move between businesses on the planet screen, or between items inside a menu. |
| Up and Down Arrow | Move between the fields or actions for the selected business or menu item. |
| Enter or Space | Activate the selected control. Hold either key on a business purchase row to buy repeatedly. |
| E | On Earth, Moon, or Mars, enter the current active event. If no event is active, say that no event is currently active. On an event planet, open or close the accessible event interface. |
| T | Read the time until the active event ends, or until the next scheduled event starts when none is active. |
| Shift+E | While an event planet is open, save and return to the last normal planet: Earth, Moon, or Mars. |
| Left Bracket and Right Bracket | Move backward or forward through the main tabs. While the event interface is open, move through Details, Goals, Rewards, and Leaderboard. |
| F6 | Repeat the current business or menu item. |
| F7 | Read the current status while a menu or dialog is open. |
| F8 | Enter screen-text mode. Use Up and Down Arrow to read the text, then press Enter, Space, Escape, or F8 to return to controls. |
| C | Read cash, Gold, and Mega Bucks. |
| Home | Raise the music volume by 10 percent. |
| End | Lower the music volume by 10 percent. |
| G | Enter or leave Mega Ticket gilding mode on Earth, Moon, or Mars. |
| Escape | Leave Mega Ticket gilding mode. The game's normal Escape behavior still closes menus and dialogs. |

### Using a Mega Ticket

Press G on Earth, Moon, or Mars. The mod reads your ticket count and lists the owned investments that have not been gilded. Use the arrow keys to choose one, then press Enter or Space. The game's confirmation dialog opens before the ticket is spent.

Temporary event planets use a separate Gold-based gilding system, so the G menu is not used there.

### Using the event interface

From Earth, Moon, or Mars, press E to enter the current active temporary event through the game's own Go to Event action. If the event introduction appears, the mod announces it. Once the event planet has loaded, press E again to open the accessible event interface. Use Left Bracket and Right Bracket to move through Details, Goals, Rewards, and Leaderboard. Use Left and Right Arrow to move between items, and Up and Down Arrow to move between an item's name, description, progress, and available action. Enter or Space activates only an explicitly selected action such as continuing the introduction or claiming a completed goal or milestone reward. Press E again to return to normal business navigation.

Completed goals and milestone rewards are rechecked immediately before a claim. If the event ends, changes, or begins loading another planet, the event interface closes without performing the old action. Hidden active rewards are announced only as mystery rewards.

## What the mod reads

Current coverage includes businesses, buy quantities and costs, production income and timers, Managers, Upgrades, Unlocks, Investors, Career and inventory items, the Shop, Gallery, AdVentures, temporary event details and goals, milestone and leaderboard rewards, live event leaderboards, Statistics, Exchange, Tickets, News, social links and rewards, Welcome Back information, reward celebrations, confirmation dialogs, and locked-planet information.

PlayFab account IDs are deliberately left out of focus announcements.

## Areas that need more testing

Some late-game features were not unlocked in the saves used during development. Reports from players who can reach these areas are useful:

- Switching between Earth, Moon, Mars, and temporary event planets.
- The full Mega Ticket gilding flow, including the confirmation and success celebration.
- Long Upgrades and Managers lists, especially moving through several pages and then moving backward.
- Buying, inspecting, equipping, replacing, and unequipping cosmetics of different types and rarities.
- Store purchases using Gold, Mega Bucks, Mega Tickets, and real-money listings. Do not make a real-money purchase only for testing.
- Every Gallery category, including earned, claimed, and not-yet-earned unlocks.
- Events that use Angel progression, post-event result dialogs, and event-only gilding.
- Planet completion, hard-reset rewards, and the first visit to a newly unlocked planet.
- Reward dialogs containing several items or currencies at once.

When reporting a problem, include the exact words NVDA announced, what you expected, the current planet or event, and which keys you pressed.

## Safety and privacy

- Patcher updates are checked against the SHA-256 digest supplied by GitHub.
- Unsupported game assemblies are rejected before files are changed.
- The game must be closed during installation, repair, or restoration.
- The original assembly is backed up before the first installation.
- The runtime speaks through NVDA and writes a local diagnostic speech log to `%LOCALAPPDATA%\AdCapAccess\speech.log`.
- The runtime's development bridge listens only on `127.0.0.1`.
