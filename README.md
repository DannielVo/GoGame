# Go Game – 9×9 Board with Adversarial Search

This project is a **Python** application implementing a simplified **Go** game on a **9×9 board**.  
The game supports **Human vs Human** mode and **Human vs AI** mode using a **Heuristic Minimax Search** bot.
The system provides a friendly UI, organized OOP structure.

---

## Key Features

### 1. Human vs Human Mode

- Two players take turns placing stones using the mouse.
- Fully interactive board with click sounds and win overlay.
- Clear highlight of turns and game state.

### 2. Human vs AI Mode (Heuristic Minimax Search)

- Implemented **Heuristic Minimax Search** with alpha–beta pruning.
- A custom heuristic evaluates board strength based on territory, liberties, influence, and local patterns.
- Configurable search depth **L**, with explanation and justification included in the code/report.

### 3. Heuristic Function

- Designed specifically for 9×9 Go:
  - Encourages capturing groups with low liberties.
  - Rewards stable shapes and strong influence zones.
  - Penalizes unsafe stones and bad shapes.
- Efficient enough for responsive gameplay.

### 4. Well-Organized OOP Structure

- Clear separation between **core game logic**, **AI bots**, and **UI screens**.
- Easy to maintain, extend, and read.

### 5. Friendly Pygame UI

- Wooden Go board background.
- Smooth animations and sound effects (click, victory).
- Separate screens: Home, Game Mode Setup, Guide, Game Screen.

---

## Tech Stack

- **Language:** Python
- **Game Engine:** pygame-ce
- **Graphics:** Pillow (PIL) for image handling
- **Architecture:** Object-Oriented Programming (OOP) with modular file structure

---

## Project Structure

```bash
task_2/
├─ main.py                # Entry point – launches Pygame and screen navigation
├─ config.py              # Constants: colors, sizes, fonts, asset paths
├─ assets/                # Images, sounds, fonts
├─ core/
│   ├─ board.py           # Board representation, grid logic, player model
│   └─ game.py            # GoGame: rules, turns, captures, scoring
├─ bots/
│   └─ minimax_bot.py     # Heuristic Minimax + Alpha-Beta + evaluation
├─ ui/
│   ├─ widgets.py         # General UI widgets: buttons, labels, layout
│   ├─ home_screen.py     # Main menu
│   ├─ setup_screen.py    # Game mode selection
│   ├─ guide_screen.py    # Rules and instructions
│   └─ game_screen.py     # Main gameplay UI (board, input, overlay)
└─ README.md              # Project documentation
```

## Getting started

### 1. Install dependencies

Ensure you have Python installed (3.10+ recommended).

```bash
pip install pillow
pip install pygame-ce
```

### 2. Run the application

From the project directory:

```bash
python main.py
```

The game will open in a Pygame window with the Home Screen.

## Notes

### Recommended Editor

- Visual Studio Code with Python extension

- Good support for debugging, running Pygame apps, and editing structured projects.
