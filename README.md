# AdVenture Capitalist Access

AdVenture Capitalist Access adds keyboard navigation and NVDA speech to the Windows Steam version of AdVenture Capitalist.

AdVenture Capitalist is an idle game about buying businesses, hiring managers, purchasing upgrades, and restarting planets with investors so the next run earns money more quickly. The original interface is built mainly for a mouse. This mod gives the main game screen, menus, dialogs, store, rewards, and several secondary panels a consistent keyboard interface.

## Download and install

[Download AdCapAccessPatcher.exe](https://github.com/ShotgunSpoon/adCapAccess/releases/download/v1.1/AdCapAccessPatcher.exe).

1. Close AdVenture Capitalist.
2. Start the patcher.
3. Check the game folder. The default Steam location is already filled in.
4. Choose **Install or Update**.
5. Start the game normally through Steam.

The patcher backs up the original game assembly before changing it. **Repair** downloads and installs the current mod files again. **Restore Original Game** removes the mod and restores the patcher-created backup.

The patcher executable is currently unsigned, so Windows may show a warning the first time it runs.

Patcher 1.1 fixes custom game folders. Selecting or typing a different installation path now checks that folder before installation, and an older check cannot replace the result for the newly selected folder.

## Keys

These keys work while the game window has focus.

| Key | Action |
| --- | --- |
| Left and Right Arrow | Move between businesses on the planet screen, or between items inside a menu. |
| Up and Down Arrow | Move between the fields or actions for the selected business or menu item. |
| Enter or Space | Activate the selected control. |
| Left Bracket and Right Bracket | Move backward or forward through the main tabs. |
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

## What the mod reads

Current coverage includes businesses, buy quantities and costs, production income and timers, Managers, Upgrades, Unlocks, Investors, Career and inventory items, the Shop, Gallery, AdVentures, Statistics, Exchange, Tickets, News, social links and rewards, Welcome Back information, reward celebrations, confirmation dialogs, and locked-planet information.

PlayFab account IDs are deliberately left out of focus announcements.

## Areas that need more testing

This is the first public release, and some late-game features were not unlocked in the saves used during development. Reports from players who can reach these areas are useful:

- Switching between Earth, Moon, Mars, and temporary event planets.
- The full Mega Ticket gilding flow, including the confirmation and success celebration.
- Long Upgrades and Managers lists, especially moving through several pages and then moving backward.
- Buying, inspecting, equipping, replacing, and unequipping cosmetics of different types and rarities.
- Store purchases using Gold, Mega Bucks, Mega Tickets, and real-money listings. Do not make a real-money purchase only for testing.
- Every Gallery category, including earned, claimed, and not-yet-earned unlocks.
- Event goals, leaderboard rewards, event result dialogs, and event-only gilding.
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
