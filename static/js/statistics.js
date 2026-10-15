/**
 * Mind Reader AI — Statistics & Benchmark Dashboard
 * Displays live gameplay metrics, machine learning benchmark comparisons,
 * feature importances, and recent round logs.
 */

async function loadStatistics() {
  try {
    const res = await fetch("/api/statistics");
    const data = await res.json();
    if (!data.success) {
      console.error("Failed to load statistics:", data.error);
      return;
    }

    renderMetrics(data.statistics);
    renderBenchmark(data.benchmark);
    renderModeStats(data.statistics.mode_stats);
    renderRecentRounds(data.statistics.recent_rounds);
  } catch (err) {
    console.error("Error loading statistics:", err);
  }
}

function renderMetrics(stats) {
  const totalRoundsEl = document.getElementById("stat-total-rounds");
  const correctEl = document.getElementById("stat-correct");
  const incorrectEl = document.getElementById("stat-incorrect");
  const accuracyEl = document.getElementById("stat-accuracy");
  const avgConfEl = document.getElementById("stat-avg-conf");
  const longestStreakEl = document.getElementById("stat-longest-streak");
  const highestScoreEl = document.getElementById("stat-highest-score");

  if (totalRoundsEl) totalRoundsEl.textContent = stats.total_rounds;
  if (correctEl) correctEl.textContent = stats.correct_predictions;
  if (incorrectEl) incorrectEl.textContent = stats.incorrect_predictions;

  if (accuracyEl) {
    if (stats.accuracy_rate !== null) {
      accuracyEl.textContent = `${stats.accuracy_rate}%`;
      accuracyEl.className = stats.accuracy_rate >= 20 ? "metric-number highlight-cyan" : "metric-number";
    } else {
      accuracyEl.textContent = "Not enough data";
      accuracyEl.style.fontSize = "1.3rem";
    }
  }

  if (avgConfEl) {
    avgConfEl.textContent = stats.average_confidence !== null ? `${stats.average_confidence}%` : "N/A";
  }

  if (longestStreakEl) longestStreakEl.textContent = stats.longest_streak;
  if (highestScoreEl) highestScoreEl.textContent = stats.highest_score;
}

function renderBenchmark(bench) {
  if (!bench) return;

  const modelTypeEl = document.getElementById("bench-model-type");
  const samplesEl = document.getElementById("bench-samples");
  const accEl = document.getElementById("bench-test-acc");
  const baseEl = document.getElementById("bench-baseline-acc");
  const chanceEl = document.getElementById("bench-chance");
  const featuresContainer = document.getElementById("bench-features");

  if (modelTypeEl) modelTypeEl.textContent = bench.model_type;
  if (samplesEl) samplesEl.textContent = `${bench.test_samples} unseen test examples (${bench.total_synthetic_samples} total)`;
  if (accEl) accEl.textContent = `${bench.test_accuracy_percentage}%`;
  if (baseEl) baseEl.textContent = `${bench.baseline_accuracy_percentage}%`;
  if (chanceEl) chanceEl.textContent = `${bench.random_chance_percentage}%`;

  if (featuresContainer && bench.feature_importances) {
    featuresContainer.innerHTML = "";
    const sortedFeatures = Object.entries(bench.feature_importances).slice(0, 5);

    sortedFeatures.forEach(([feat, imp]) => {
      const pct = Math.round(imp * 100);
      const item = document.createElement("div");
      item.className = "feature-bar-item";
      item.innerHTML = `
        <div class="feature-bar-label">
          <span>${feat}</span>
          <span>${(imp * 100).toFixed(1)}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${pct * 2.5}%;"></div>
        </div>
      `;
      featuresContainer.appendChild(item);
    });
  }
}

function renderModeStats(modeStats) {
  const container = document.getElementById("mode-stats-container");
  if (!container || !modeStats) return;

  container.innerHTML = "";
  const modes = [
    { key: "classic", title: "Classic Number Prediction" },
    { key: "pattern", title: "Pattern Learning Challenge" },
    { key: "expert", title: "Expert Challenge" },
  ];

  modes.forEach((m) => {
    const data = modeStats[m.key] || { rounds: 0, correct: 0, accuracy: null };
    const accDisplay = data.accuracy !== null ? `${data.accuracy}%` : "Not enough data";

    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h4 style="font-size:1.1rem; margin-bottom:12px; color:#38bdf8;">${m.title}</h4>
      <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;">
        <span style="color:#94a3b8;">Rounds Played:</span>
        <strong style="color:#f8fafc;">${data.rounds}</strong>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;">
        <span style="color:#94a3b8;">Correct Predictions:</span>
        <strong style="color:#10b981;">${data.correct}</strong>
      </div>
      <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
        <span style="color:#94a3b8;">Prediction Accuracy:</span>
        <strong style="color:#c084fc;">${accDisplay}</strong>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderRecentRounds(rounds) {
  const tbody = document.getElementById("recent-rounds-tbody");
  if (!tbody) return;

  if (!rounds || rounds.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#64748b; padding:24px;">No evaluated rounds recorded yet. Play a game to see data!</td></tr>`;
    return;
  }

  tbody.innerHTML = rounds
    .map(
      (r) => `
    <tr>
      <td>#${r.round_number}</td>
      <td><span class="badge badge-purple">${r.game_mode}</span></td>
      <td><strong>${r.predicted_choice}</strong></td>
      <td><strong>${r.actual_choice}</strong></td>
      <td>
        ${
          r.prediction_correct === 1
            ? '<span class="badge badge-green">Correct</span>'
            : '<span class="badge badge-red">Miss</span>'
        }
      </td>
      <td>${Math.round(r.confidence * 100)}%</td>
      <td style="color:#94a3b8; font-size:0.85rem; max-width:280px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;" title="${r.explanation}">
        ${r.explanation}
      </td>
    </tr>
  `
    )
    .join("");
}

// Reset data handler
function initResetButton() {
  const btn = document.getElementById("reset-all-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    if (confirm("Are you sure you want to reset all game history and statistics? This cannot be undone.")) {
      try {
        const res = await fetch("/api/reset-all-data", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          alert("All statistics have been reset successfully.");
          loadStatistics();
        }
      } catch (e) {
        console.error(e);
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadStatistics();
  initResetButton();
});
