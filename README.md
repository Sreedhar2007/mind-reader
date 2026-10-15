# Mind Reader AI — An Intelligent Number Prediction Game

[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An interactive, production-ready, and visually stunning web-based AI game that demonstrates how artificial intelligence and machine learning can identify patterns in human sequential decision-making.

Built specifically for college AI demonstrations, laboratory presentations, and coursework submissions. Mind Reader AI operates **100% locally** without paid APIs or external services.

---

## Table of Contents
1. [Project Overview & Problem Statement](#1-project-overview--problem-statement)
2. [Key Features](#2-key-features)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture & Data Flow](#4-system-architecture--data-flow)
5. [Machine Learning Implementation](#5-machine-learning-implementation)
6. [Game Modes](#6-game-modes)
7. [Step-by-Step Setup Guide (Windows & VS Code)](#7-step-by-step-setup-guide-windows--vs-code)
8. [Automated Testing](#8-automated-testing)
9. [College Presentation & Lecturer Guide](#9-college-presentation--lecturer-guide)
10. [Limitations & Future Enhancements](#10-limitations--future-enhancements)

---

## 1. Project Overview & Problem Statement

### The Problem
When humans are asked to generate "random" numbers or make arbitrary choices, psychological research demonstrates that we are inherently biased random number generators. Subconsciously, people exhibit predictable habits:
- **Clustering**: Over-selecting "lucky" numbers (e.g., 7 or 3).
- **Gambler’s Fallacy**: Avoiding previous choices believing they won't repeat immediately.
- **Sequential Stepping**: Choosing numbers adjacent to recent picks (+1, -1, +2).
- **Parity Rhythm**: Oscillating between odd and even numbers or high and low ranges.

### The Solution
**Mind Reader AI** creates the illusion of telepathy by exploiting these subconscious behavioral patterns using a multi-class **Random Forest Classifier** trained on human sequential behavior models. 

The application adheres to strict academic honesty:
- It **never cheats** by peeking at secret choices before generating predictions.
- It displays genuine **scikit-learn** model probabilities and feature importances.
- It provides transparent **Explainable AI (XAI)** reasoning for every prediction.
- It explicitly contrasts statistical machine learning with deterministic mathematical tricks.

---

## 2. Key Features

- **Fair Two-Phase Prediction Protocol**: The server generates and locks its prediction *before* the player reveals their actual choice.
- **Explainable AI (XAI)**: Displays model confidence percentage, detected pattern categories (e.g., *Sequential Progression*, *Pendulum Oscillation*, *Parity Clustering*), and chronological feature history.
- **4 Distinct Game Modes**: Classic Prediction (1-10), Pattern Learning Challenge, Mathematical Mind Trick, and Expert Challenge (1-25).
- **Dual-Track Statistics Dashboard**: Keeps live player gameplay accuracy separate from offline synthetic machine learning benchmark evaluation.
- **Synthetic Human Archetype Dataset**: 7,000 synthetic player choices simulating counters, repeaters, alternators, and uniform random noise.
- **Baseline Dummy Comparison**: Evaluated against a most-frequent baseline dummy classifier to prove genuine predictive learning.
- **Modern Cyberpunk UI**: Dark navy theme (`#070b14`), glowing neon accents, ambient particle network canvas, and Web Audio API synthesized sound effects.
- **Zero External Dependencies**: Operates offline without external CDNs or commercial API keys.

---

## 3. Technology Stack

| Layer | Technologies Used | Description |
|---|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+) | Modern cyberpunk UI, responsive layout, particle canvas, Web Audio sound synthesis |
| **Backend** | Python 3.9+, Flask 3.x | REST API routes, session management, fair protocol verification |
| **Artificial Intelligence** | scikit-learn, NumPy, pandas, joblib | RandomForestClassifier (75 trees), feature extraction, synthetic generator, baseline dummy |
| **Database** | SQLite3 | Relational schema with `players`, `game_sessions`, and `game_rounds` tables |
| **Testing** | unittest | Automated test suite verifying database, AI engine, and game rules |

---

## 4. System Architecture & Data Flow

```mermaid
flowchart TD
    User([Player in Browser]) -->|1. Chooses Secret Number Privately| UI[Frontend UI / game.js]
    UI -->|2. POST /api/predict (session_id)| Flask[Flask REST API / app.py]
    Flask -->|3. Fetch Past Choices| DB[(SQLite Database)]
    Flask -->|4. Extract Lags & Parity Features| ML[Random Forest Classifier / ai_model.py]
    ML -->|5. Return Prediction & Explanation| Flask
    Flask -->|6. Cache Pending Prediction & Return JSON| UI
    UI -->|7. Display Locked AI Prediction| User
    User -->|8. Reveal Secret Choice| UI
    UI -->|9. POST /api/submit-round (session_id, actual_choice)| Flask
    Flask -->|10. Compare & Compute Points/Streaks| Logic[Game Engine / game_logic.py]
    Logic -->|11. Persist Round Result| DB
    Logic -->|12. Return Evaluation Banner| UI
```

### Detailed File Structure
```
mind-reader/
├── app.py                   # Flask server, routing, and REST API endpoints
├── ai_model.py              # Machine learning engine, feature extraction, training
├── game_logic.py            # Session management, fair scoring, math trick solver
├── database.py              # SQLite connection, schema initialization, parameterized queries
├── requirements.txt         # Project dependencies
├── README.md                # Comprehensive documentation & setup instructions
├── templates/
│   ├── base.html            # Base template with navbar, particle canvas, Web Audio
│   ├── index.html           # Landing page with glowing neural brain hero
│   ├── game.html            # Main game arena (Modes A, B, C, D)
│   ├── statistics.html      # Statistics & scikit-learn model benchmark dashboard
│   └── about.html           # Architecture diagrams, ML details, presentation guide
├── static/
│   ├── css/
│   │   └── style.css        # Cyberpunk styling, glowing cards, responsive layout
│   ├── js/
│   │   ├── main.js          # Particle canvas & Web Audio synthesizer
│   │   ├── game.js          # Gameplay controller & two-phase prediction protocol
│   │   └── statistics.js    # Metric counters, feature importance bars, audit table
│   └── images/
│       └── neural_brain.svg # Glowing vector neural brain illustration
├── data/
│   ├── mind_reader.db       # SQLite database (auto-created on startup)
│   ├── trained_model.joblib # Serialized scikit-learn model
│   └── benchmark_metrics.joblib # Offline test evaluation metrics
└── tests/
    ├── test_database.py     # SQLite schema, CRUD, and zero-division handling
    ├── test_ai_model.py     # Feature extraction, synthetic data, predictions
    └── test_game_logic.py   # Protocol lifecycle, scoring, streak bonuses, math trick
```

---

## 5. Machine Learning Implementation

### Feature Engineering
From each player's chronological sequence of choices, the model extracts 10 features before generating a prediction:
1. `prev_1`: Most recent choice (lag 1).
2. `prev_2`: Choice 2 rounds ago (lag 2).
3. `prev_3`: Choice 3 rounds ago (lag 3).
4. `diff_1_2`: Step difference (`prev_1 - prev_2`).
5. `diff_2_3`: Step difference (`prev_2 - prev_3`).
6. `last_is_odd`: Binary parity flag (1 if odd, 0 if even).
7. `repeat_streak`: Consecutive count of identical choices.
8. `recent_mean`: Rolling average of recent choices.
9. `recent_span`: Spread (`max - min`) of recent choices.
10. `round_num`: Chronological round counter.

### Synthetic Training Data & Behavioral Archetypes
To train without requiring thousands of human trials beforehand, the system generates a reproducible synthetic dataset of 7,000 choices simulating human decision archetypes:
- **Cyclers / Counters (30%)**: Players who increment or decrement numbers (+1, +2, -1).
- **Repeaters / Sticky (25%)**: Players who linger around favored digits.
- **Alternators (25%)**: Players oscillating between high/low or odd/even.
- **Random / Gambler's Fallacy (20%)**: Uniform noise or deliberate avoidance of recent numbers.

### Unseen Test Split Evaluation
The data is partitioned using an 80/20 train-test split:
- **Training Samples**: 5,600
- **Unseen Test Samples**: 1,400
- **Random Forest Test Accuracy**: **~37.1%** (on a 10-class problem)
- **Baseline Dummy Classifier Accuracy**: **11.1%**
- **Random Chance**: **10.0%** ($1/10$)

The model achieves over **3.7x the accuracy of random chance** and more than **3.3x the baseline predictor** on unseen test data.

---

## 6. Game Modes

### Mode A: Classic Number Prediction (1 to 10)
1. Player chooses a secret number from 1 to 10.
2. Player clicks **Lock Secret Choice & Read My Mind**.
3. The AI generates its prediction from historical features *without* knowing the player's secret.
4. Player clicks **Reveal My Choice & Compare**.
5. Server evaluates the match: +10 points for correct predictions with streak bonuses (+5 every 3 streak milestones).

### Mode B: Pattern Learning Challenge
Designed to demonstrate online pattern recognition:
- Try entering predictable patterns (e.g., $1, 3, 5, 7, 9$ or $2, 4, 6, 8$).
- Observe how the AI explanation card recognizes parity clustering and sequential step trends.
- Test randomized inputs to see how prediction confidence adjusts.

### Mode C: Mathematical Mind Trick (Deterministic Identity)
A guided step-by-step arithmetic trick:
1. Think of any number $x$ between 1 and 1000.
2. Multiply by 2 $\rightarrow 2x$.
3. Add 14 $\rightarrow 2x + 14$.
4. Divide by 2 $\rightarrow x + 7$.
5. Subtract your original number $x \rightarrow 7$.
- **The Lesson**: The result is *always* 7 due to the invariant identity:
  $$\frac{2x + 14}{2} - x = x + 7 - x = 7$$
- Explicitly demonstrates the difference between **deterministic mathematical identities** (100% predictable) and **probabilistic machine learning** (data-driven hypothesis generation).

### Mode D: Expert Challenge (1 to 25)
Expanded choice range from 1 to 25. Random baseline chance drops to only **4.0%**, testing multi-lag feature extraction under high entropy.

### Mode E: Condition Mind Reader (Binary Decision Tree Interrogator)
Think of any secret number between 1 and 30 in your head. Do **not** type or click it!
- The AI asks you 4–5 strategic Yes/No condition questions (e.g., *"Is it even?"*, *"Is it greater than 15?"*, *"Is it a multiple of 3?"*, *"Is it prime?"*).
- Uses **Shannon Information Entropy** to pick conditions that split the remaining candidate space closest to 50/50 ($O(\log_2 N)$).
- A live candidate board visually eliminates numbers with each answer.
- The AI deduces your exact secret number with 100% accuracy!

---

## 7. Step-by-Step Setup Guide (Windows & VS Code)

Follow these exact steps to set up and run the application locally on Windows.

### Prerequisites
- Python 3.9 or newer installed ([python.org](https://www.python.org/downloads/)). Check **"Add python.exe to PATH"** during installation.
- Visual Studio Code installed ([code.visualstudio.com](https://code.visualstudio.com/)).

### Step 1: Open Terminal in VS Code
1. Open the project folder in VS Code:
   ```powershell
   code c:\Users\hp\Desktop\mind-reader
   ```
2. Open the built-in terminal (`Ctrl + ~` or `Terminal -> New Terminal`).

### Step 2: Create and Activate a Virtual Environment
```powershell
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment on Windows PowerShell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and reactivate).*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Automated Unit Tests
```powershell
python -m unittest discover -s tests -p "test_*.py"
```
You should see all 16 tests pass with `OK`.

### Step 5: Start the Flask Application
```powershell
python app.py
```

### Step 6: Open the Application in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 8. Automated Testing

The project includes unit tests covering every subsystem:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Test Coverage Highlights:
- `tests/test_database.py`: Table creation, player retrieval, session tracking, round recording, and empty statistics handling (prevents division by zero).
- `tests/test_ai_model.py`: Feature extraction with 0, 1, and 3+ choices, synthetic dataset generation, Random Forest predictions, and confidence bound checks.
- `tests/test_game_logic.py`: Fair two-phase prediction protocol, rejection of choice submissions without a pre-locked prediction, invalid range rejection, and mathematical trick invariant validation.

---

## 9. College Presentation & Lecturer Guide

When presenting this project to your college professor or examiner, use this structured roadmap:

### 1. The Core Scientific Hook (1 Minute)
> *"Can a machine read your mind? Psychologists have proven that humans are poor random number generators. When asked for a random choice, people instinctively follow subconscious patterns. Mind Reader AI demonstrates how machine learning identifies these patterns."*

### 2. Live Fair Protocol Demonstration (2 Minutes)
1. Go to **Play Game -> Mode A (Classic)**.
2. Select number `7` privately. Point out that the secret number is **not** transmitted to the server.
3. Click **Lock Secret Choice & Read My Mind**. Show the scanner animation and the AI's locked prediction.
4. Click **Reveal My Choice & Compare**. Point to the explanation panel explaining why the model predicted that number.

### 3. The Pattern Adaptation Test (2 Minutes)
1. Switch to **Mode B (Pattern Learning)**.
2. Choose an alternating sequence like `2, 8, 2, 8, 2`.
3. Highlight how the AI detects **Pendulum Oscillation** and correctly anticipates the return swing.
4. Now choose random numbers like `1, 9, 4, 7` to show how the confidence score drops and the AI reports high pattern entropy.

### 4. Contrasting Math vs Machine Learning (2 Minutes)
1. Switch to **Mode C (Math Mind Trick)**.
2. Enter any large number (e.g., `854`).
3. Show that the answer is always `7`.
4. Explain the key distinction: **Mode C is deterministic symbolic algebra** ($x$ cancels out), whereas **Modes A, B, and D are inductive machine learning** models predicting human behavior.

### 5. Statistics & Academic Metrics (1 Minute)
1. Open the **Statistics** tab.
2. Show the real-time SQLite database audit log.
3. Present the **Scikit-Learn Model Benchmark Card**:
   - Random Forest accuracy (~37.1%) vs Baseline dummy classifier (11.1%) vs Chance (10.0%).
   - Show the Gini feature importance breakdown.

---

## 10. Limitations & Future Enhancements

### Limitations
- **Cold-Start Bias**: During round 1, no prior history exists; the model must rely on psychological heuristics (e.g., number 7) until sufficient history is gathered.
- **Intentional True Randomness**: If a player uses an external physical random number generator (like a coin flip or dice), prediction accuracy will converge toward random chance ($1/N$).

### Future Enhancements
- **Continuous Online Learning**: Incremental model updates using warm-start tree retraining as a player completes more rounds.
- **Deep Sequence Models**: Implementing an LSTM (Long Short-Term Memory) or Transformer network for multi-step temporal dependencies.
- **Multiplayer Duel**: Two players attempting to out-predict both each other and the AI simultaneously.

---

## License
This project is open-source and available under the [MIT License](LICENSE).
