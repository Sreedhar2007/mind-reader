/**
 * Mind Reader AI — Condition-Based Decision Tree Controller
 * Drives the interactive Yes/No condition interrogator, live candidate board,
 * difficulty level selection (Easy 1-20, Medium 1-50, Master 1-100),
 * Shannon Entropy tracking, and mind read deduction reveal.
 */

class ConditionMindReaderGame {
  constructor() {
    this.interrogatorIntro = document.getElementById("interrogator-intro");
    this.interrogatorActive = document.getElementById("interrogator-active");
    this.interrogatorReveal = document.getElementById("interrogator-reveal");

    this.interrogatorStartBtn = document.getElementById("interrogator-start-btn");
    this.interrogatorYesBtn = document.getElementById("interrogator-yes-btn");
    this.interrogatorNoBtn = document.getElementById("interrogator-no-btn");
    this.interrogatorRestartBtn = document.getElementById("interrogator-restart-btn");

    this.interrogatorQNum = document.getElementById("interrogator-q-num");
    this.interrogatorRemainingCount = document.getElementById("interrogator-remaining-count");
    this.interrogatorEntropyVal = document.getElementById("interrogator-entropy-val");
    this.interrogatorQText = document.getElementById("interrogator-q-text");
    this.interrogatorQSub = document.getElementById("interrogator-q-sub");
    this.interrogatorCandidatesGrid = document.getElementById("interrogator-candidates-grid");
    this.interrogatorFinalNumber = document.getElementById("interrogator-final-number");
    this.interrogatorPathList = document.getElementById("interrogator-path-list");

    this.targetHeading = document.getElementById("interrogator-target-heading");
    this.targetDesc = document.getElementById("interrogator-target-desc");
    this.hudDomain = document.getElementById("hud-target-domain");
    this.hudMaxQ = document.getElementById("hud-max-questions");

    // Default level: Medium (1 to 50)
    this.selectedMax = 50;
    this.selectedMaxQ = 6;
    this.selectedLevel = "medium";

    this.interrogatorState = null;
    this.allCandidates = Array.from({ length: this.selectedMax }, (_, i) => i + 1);

    this.bindEvents();
    this.updateLevelDisplay();
  }

  bindEvents() {
    // Level Selection Buttons
    document.querySelectorAll(".level-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        window.soundFx.playClick();
        document.querySelectorAll(".level-btn").forEach((b) => b.classList.remove("active"));
        const target = e.currentTarget;
        target.classList.add("active");

        this.selectedLevel = target.dataset.level || "medium";
        this.selectedMax = parseInt(target.dataset.max, 10) || 50;
        this.selectedMaxQ = parseInt(target.dataset.maxQ, 10) || 6;

        this.allCandidates = Array.from({ length: this.selectedMax }, (_, i) => i + 1);
        this.updateLevelDisplay();
      });
    });

    if (this.interrogatorStartBtn) {
      this.interrogatorStartBtn.addEventListener("click", () => this.startInterrogator());
    }
    if (this.interrogatorYesBtn) {
      this.interrogatorYesBtn.addEventListener("click", () => this.answerInterrogator(true));
    }
    if (this.interrogatorNoBtn) {
      this.interrogatorNoBtn.addEventListener("click", () => this.answerInterrogator(false));
    }
    if (this.interrogatorRestartBtn) {
      this.interrogatorRestartBtn.addEventListener("click", () => this.restartGame());
    }

    // Keyboard navigation (Y for Yes, N for No, Enter/Space for Start & Restart)
    document.addEventListener("keydown", (e) => {
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;

      if (this.interrogatorActive && this.interrogatorActive.style.display !== "none") {
        if (e.key === "y" || e.key === "Y") {
          e.preventDefault();
          this.answerInterrogator(true);
        } else if (e.key === "n" || e.key === "N") {
          e.preventDefault();
          this.answerInterrogator(false);
        }
      } else if (this.interrogatorIntro && this.interrogatorIntro.style.display !== "none") {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.startInterrogator();
        }
      } else if (this.interrogatorReveal && this.interrogatorReveal.style.display !== "none") {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.restartGame();
        }
      }
    });
  }

  updateLevelDisplay() {
    if (this.targetHeading) {
      this.targetHeading.textContent = `Think of ANY Number Between 1 and ${this.selectedMax}`;
    }
    if (this.targetDesc) {
      this.targetDesc.innerHTML = `Do <strong>NOT</strong> click it and do <strong>NOT</strong> type it!<br>Hold the number secretly in your head. The AI will ask you a few smart Yes/No condition questions and deduce your exact number in <strong>at most ${this.selectedMaxQ} questions</strong>!`;
    }
    if (this.hudDomain) {
      this.hudDomain.textContent = `1 to ${this.selectedMax}`;
    }
    if (this.hudMaxQ) {
      this.hudMaxQ.textContent = `≤ ${this.selectedMaxQ} Questions`;
    }
  }

  async startInterrogator() {
    window.soundFx.playScan();
    try {
      const res = await fetch("/api/interrogator/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ min_val: 1, max_val: this.selectedMax }),
      });
      const data = await res.json();
      if (data.success) {
        this.interrogatorState = data;
        this.allCandidates = [...data.candidates];

        if (this.interrogatorIntro) this.interrogatorIntro.style.display = "none";
        if (this.interrogatorReveal) this.interrogatorReveal.style.display = "none";
        if (this.interrogatorActive) this.interrogatorActive.style.display = "block";

        this.renderInterrogatorActive();
      }
    } catch (e) {
      console.error("Error starting interrogator:", e);
    }
  }

  restartGame() {
    window.soundFx.playClick();
    if (this.interrogatorActive) this.interrogatorActive.style.display = "none";
    if (this.interrogatorReveal) this.interrogatorReveal.style.display = "none";
    if (this.interrogatorIntro) this.interrogatorIntro.style.display = "block";
    this.updateLevelDisplay();
  }

  renderInterrogatorActive() {
    const s = this.interrogatorState;
    if (!s || !s.current_question) return;

    if (this.interrogatorQNum) {
      this.interrogatorQNum.textContent = `Condition ${s.question_number} of ${this.selectedMaxQ}`;
    }
    if (this.interrogatorRemainingCount) {
      this.interrogatorRemainingCount.textContent = `${s.remaining_count} / ${this.selectedMax}`;
    }
    if (this.interrogatorEntropyVal) {
      this.interrogatorEntropyVal.textContent = `${s.entropy} bits`;
    }

    if (this.interrogatorQText) {
      this.interrogatorQText.textContent = s.current_question.text;
    }
    if (this.interrogatorQSub) {
      this.interrogatorQSub.textContent = `Information Balance: ${s.current_question.split_ratio || "50% / 50%"}`;
    }

    this.renderInterrogatorCandidates();
  }

  renderInterrogatorCandidates() {
    if (!this.interrogatorCandidatesGrid) return;
    this.interrogatorCandidatesGrid.innerHTML = "";

    // Toggle compact style for 100 candidates
    if (this.selectedMax >= 100) {
      this.interrogatorCandidatesGrid.classList.add("compact-100");
    } else {
      this.interrogatorCandidatesGrid.classList.remove("compact-100");
    }

    const remainingSet = new Set(this.interrogatorState.candidates);

    this.allCandidates.forEach((num) => {
      const chip = document.createElement("div");
      const isAlive = remainingSet.has(num);
      chip.className = `candidate-chip ${isAlive ? "active" : "eliminated"}`;
      chip.textContent = num;
      this.interrogatorCandidatesGrid.appendChild(chip);
    });
  }

  async answerInterrogator(answerBool) {
    if (!this.interrogatorState || !this.interrogatorState.current_question) return;

    window.soundFx.playClick();
    const payload = {
      candidates: this.interrogatorState.candidates,
      question_key: this.interrogatorState.current_question.key,
      answer_yes: answerBool,
      history: this.interrogatorState.history || [],
    };

    try {
      const res = await fetch("/api/interrogator/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.success) {
        this.interrogatorState.candidates = data.candidates;
        this.interrogatorState.remaining_count = data.remaining_count;
        this.interrogatorState.entropy = data.entropy;
        this.interrogatorState.history = data.history;
        this.interrogatorState.current_question = data.current_question;
        this.interrogatorState.question_number = data.question_number;

        if (data.game_over) {
          window.soundFx.playSuccess();
          this.renderInterrogatorReveal(data);
        } else {
          window.soundFx.playScan();
          this.renderInterrogatorActive();
        }
      }
    } catch (e) {
      console.error("Error answering interrogator:", e);
    }
  }

  renderInterrogatorReveal(data) {
    if (this.interrogatorActive) this.interrogatorActive.style.display = "none";
    if (this.interrogatorReveal) this.interrogatorReveal.style.display = "block";

    if (this.interrogatorFinalNumber) {
      this.interrogatorFinalNumber.textContent = data.secret_number || "Found!";
    }

    if (this.interrogatorPathList && data.history) {
      this.interrogatorPathList.innerHTML = data.history
        .map((h, idx) => `
          <div style="display:flex; justify-content:space-between; padding:10px 14px; background:rgba(15,23,42,0.6); border-radius:6px; border:1px solid #1e293b;">
            <span><strong>Condition ${idx + 1}:</strong> <code>${h.question_key}</code></span>
            <span>Answer: <strong style="color:${h.answer === "Yes" ? "#67e8f9" : "#fda4af"};">${h.answer}</strong> (${h.candidates_left} left)</span>
          </div>
        `)
        .join("");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.gameApp = new ConditionMindReaderGame();
});
