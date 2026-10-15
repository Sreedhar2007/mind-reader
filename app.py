"""
Flask Application for Mind Reader AI — An Intelligent Number Prediction Game.
Provides web page routes and REST API endpoints for game sessions,
fair predictions, round evaluations, statistics, and model benchmarking.
"""

import os
from flask import Flask, jsonify, render_template, request
import database
from ai_model import ai_service
from game_logic import GameEngine, MODE_CONFIGS

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "mind-reader-secret-key-2026")

# Initialize database tables on startup
database.init_db()


# ---------------------------------------------------------
# Page Routes
# ---------------------------------------------------------

@app.route("/")
def index():
    """Home landing page."""
    return render_template("index.html")


@app.route("/game")
def game():
    """Main interactive gameplay page."""
    mode = request.args.get("mode", "classic")
    if mode not in MODE_CONFIGS:
        mode = "classic"
    return render_template("game.html", initial_mode=mode, mode_configs=MODE_CONFIGS)


@app.route("/statistics")
def statistics():
    """Comprehensive statistics dashboard."""
    return render_template("statistics.html")


@app.route("/about")
def about():
    """College presentation and technical architecture overview."""
    return render_template("about.html")


# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------

@app.route("/api/start-session", methods=["POST"])
def api_start_session():
    """
    Start or join a game session.
    Expects JSON: { "player_name": str, "game_mode": str }
    """
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "Player")).strip() or "Player"
    game_mode = str(data.get("game_mode", "classic")).strip().lower()

    if game_mode not in MODE_CONFIGS:
        game_mode = "classic"

    try:
        session_info = GameEngine.start_session(display_name=player_name, game_mode=game_mode)
        return jsonify({"success": True, **session_info}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Generate a fair AI prediction using ONLY prior session history.
    The secret choice is NOT known to the AI at this step.
    Expects JSON: { "session_id": int }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")

    if session_id is None or not isinstance(session_id, int):
        return jsonify({"success": False, "error": "Valid integer session_id is required."}), 400

    try:
        prediction = GameEngine.generate_prediction(session_id)
        return jsonify({"success": True, **prediction}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Prediction failed: {str(e)}"}), 500


@app.route("/api/submit-round", methods=["POST"])
def api_submit_round():
    """
    Submit player's actual choice to evaluate against the pre-locked AI prediction.
    Expects JSON: { "session_id": int, "actual_choice": int }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    actual_choice = data.get("actual_choice")

    if session_id is None or not isinstance(session_id, int):
        return jsonify({"success": False, "error": "Valid integer session_id is required."}), 400

    if actual_choice is None:
        return jsonify({"success": False, "error": "actual_choice is required."}), 400

    try:
        actual_choice_int = int(actual_choice)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "actual_choice must be a valid integer."}), 400

    try:
        result = GameEngine.submit_round(session_id=session_id, actual_choice=actual_choice_int)
        return jsonify({"success": True, **result}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Round submission failed: {str(e)}"}), 500


@app.route("/api/statistics", methods=["GET"])
def api_statistics():
    """Return aggregated live game statistics and benchmark info."""
    try:
        stats = database.get_overall_statistics()
        benchmark = ai_service.get_benchmark_info()
        return jsonify({"success": True, "statistics": stats, "benchmark": benchmark}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Return scikit-learn model benchmark and feature importances."""
    try:
        benchmark = ai_service.get_benchmark_info()
        return jsonify({"success": True, "benchmark": benchmark}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """
    Reset score and current streak for an active session.
    Expects JSON: { "session_id": int }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")

    if session_id is None or not isinstance(session_id, int):
        return jsonify({"success": False, "error": "Valid integer session_id is required."}), 400

    try:
        res = GameEngine.reset_session(session_id)
        return jsonify({"success": True, **res}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/math-trick", methods=["POST"])
def api_math_trick():
    """
    Compute step breakdown and pedagogical lesson for Mode C (Mathematical Mind Trick).
    Expects JSON: { "secret_number": int }
    """
    data = request.get_json(silent=True) or {}
    secret_number = data.get("secret_number")

    try:
        val = int(secret_number)
        if not (1 <= val <= 1000):
            return jsonify({"success": False, "error": "Please enter a whole number between 1 and 1000."}), 400
        trick_solution = GameEngine.solve_math_trick(val)
        return jsonify({"success": True, **trick_solution}), 200
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Valid integer secret_number is required."}), 400


@app.route("/api/reset-all-data", methods=["POST"])
def api_reset_all_data():
    """Reset all database records for presentation or testing purposes."""
    try:
        database.reset_all_data()
        return jsonify({"success": True, "message": "All database records have been reset."}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/interrogator/start", methods=["POST"])
def api_interrogator_start():
    """Start a Decision Tree Interrogator condition-based guessing session."""
    data = request.get_json(silent=True) or {}
    min_val = int(data.get("min_val", 1))
    max_val = int(data.get("max_val", 50))
    try:
        from game_logic import DecisionTreeInterrogator
        state = DecisionTreeInterrogator.start_game(min_val=min_val, max_val=max_val)
        return jsonify({"success": True, **state}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/interrogator/answer", methods=["POST"])
def api_interrogator_answer():
    """Evaluate Yes/No condition answer, filter candidates, and deduce next question or final number."""
    data = request.get_json(silent=True) or {}
    candidates = data.get("candidates")
    question_key = data.get("question_key")
    answer_yes = bool(data.get("answer_yes"))
    history = data.get("history", [])

    if not isinstance(candidates, list) or not question_key:
        return jsonify({"success": False, "error": "Invalid payload. candidates list and question_key required."}), 400

    try:
        from game_logic import DecisionTreeInterrogator
        result = DecisionTreeInterrogator.answer_question(
            candidates=candidates,
            question_key=question_key,
            answer_yes=answer_yes,
            history=history,
        )
        return jsonify({"success": True, **result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Mind Reader AI — Web Server Starting")
    print("Running locally at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
