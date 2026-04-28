import sys
import threading
import logging
from flask import Flask, render_template, jsonify, request, abort
from config.logging_config import setup_logging
from config.settings import LOG_LEVEL

setup_logging(LOG_LEVEL)
logger = logging.getLogger("aura.app")

from core.voice import get_web_updates, talk

app = Flask(__name__)

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri="memory://",
    )
    logger.info("Rate limiter enabled.")
except ImportError:
    limiter = None
    logger.warning("flask-limiter not installed — rate limiting disabled.")

try:
    from flask_talisman import Talisman
    Talisman(
        app,
        content_security_policy=False,
        force_https=False,
        strict_transport_security=False,
    )
    logger.info("Talisman security headers enabled.")
except ImportError:
    logger.warning("flask-talisman not installed — security headers disabled.")

_aura_lock = threading.Lock()
_monitor_started = False

@app.before_request
def _ensure_monitor():
    global _monitor_started
    if not _monitor_started:
        _monitor_started = True
        try:
            from core.alerts import start_proactive_monitor
            start_proactive_monitor(talk)
        except Exception as exc:
            logger.warning("Could not start proactive monitor: %s", exc)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    from core.db import ping as db_ping
    db_ok = db_ping()
    return jsonify({
        "status": "ok",
        "db": "connected" if db_ok else "disconnected",
        "lock_held": _aura_lock.locked(),
    })

@app.route("/updates", methods=["GET"])
def updates():
    msgs = get_web_updates()
    return jsonify({"messages": msgs})

def _process_and_capture(command: str, lat=None, lon=None) -> str:
    import core.voice as _voice_mod
    import commands.dispatcher as _disp_mod
    import commands.communication as _comm_mod
    import commands.information as _info_mod
    import commands.system as _sys_mod
    import commands.productivity as _prod_mod
    import commands.fun as _fun_mod
    responses: list[str] = []
    _orig_talk = _voice_mod.talk

    def _capture_talk(text):
        responses.append(text)
        _voice_mod._web_message_queue.append(text)

    for _mod in (_voice_mod, _disp_mod, _comm_mod, _info_mod, _sys_mod, _prod_mod, _fun_mod):
        try:
            _mod.talk = _capture_talk
        except AttributeError:
            pass
    _voice_mod.set_talk_handler(_capture_talk)

    try:
        from commands.dispatcher import process_command
        process_command(command, gps_lat=lat, gps_lon=lon)
    except Exception as exc:
        logger.error("Command processing error for '%s': %s", command, exc)
    finally:
        for _mod in (_voice_mod, _disp_mod, _comm_mod, _info_mod, _sys_mod, _prod_mod, _fun_mod):
            try:
                _mod.talk = _orig_talk
            except AttributeError:
                pass
        _voice_mod.set_talk_handler(None)

    return " ".join(dict.fromkeys(responses)).strip() or "Done."

@app.route("/listen", methods=["POST"])
def listen():
    acquired = _aura_lock.acquire(timeout=5.0)
    if not acquired:
        logger.warning("Lock busy — rejected /listen request.")
        return jsonify({"status": "error", "message": "AURA is busy. Please wait a moment."}), 429

    try:
        from core.voice import accept_command
        command = accept_command()
        if not command:
            return jsonify({
                "status": "error",
                "message": "I didn't catch that. Please try again."
            }), 400

        data = request.get_json(force=True, silent=True) or {}
        lat = data.get("lat")
        lon = data.get("lon")

        combined = _process_and_capture(command, lat, lon)
        logger.info("/listen '%s' -> '%s'", command, combined[:80])
        return jsonify({
            "status": "success",
            "command": command,
            "response": "Command processed.",
            "lang_code": "en-US",
        })

    except Exception as exc:
        import traceback
        logger.error("listen() error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"status": "error", "message": f"Something went wrong: {exc}"}), 500
    finally:
        if _aura_lock.locked():
            _aura_lock.release()

@app.route("/command", methods=["POST"])
def text_command():
    data = request.get_json(force=True, silent=True) or {}
    command = data.get("command", "").strip()
    if not command:
        return jsonify({"status": "error", "message": "command field is required"}), 400

    lat = data.get("lat")
    lon = data.get("lon")

    combined = _process_and_capture(command, lat, lon)
    logger.info("/command '%s' -> '%s'", command, combined[:80])
    return jsonify({
        "status": "success",
        "command": command,
        "response": "Command processed.",
        "lang_code": "en-US",
    })

@app.route("/sos", methods=["POST"])
def sos():
    data = request.get_json(force=True, silent=True) or {}
    lat = data.get("lat")
    lon = data.get("lon")

    import core.voice as _voice_mod
    import commands.communication as _comm_mod
    responses: list[str] = []
    _orig_talk = _voice_mod.talk
    _orig_comm_talk = getattr(_comm_mod, "talk", None)

    def _capture(text):
        responses.append(text)

    _voice_mod.talk = _capture
    _comm_mod.talk = _capture
    _voice_mod.set_talk_handler(_capture)

    try:
        from commands.communication import command_emergency_sos
        command_emergency_sos(gps_lat=lat, gps_lon=lon)
    except Exception as exc:
        logger.error("/sos error: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500
    finally:
        _voice_mod.talk = _orig_talk
        if _orig_comm_talk:
            _comm_mod.talk = _orig_comm_talk
        _voice_mod.set_talk_handler(None)

    combined = " ".join(responses).strip()
    logger.warning("/sos activated -> %s", combined[:100])
    return jsonify({"status": "ok", "response": combined})

@app.route("/reset", methods=["POST"])
def reset():
    released = False
    try:
        if _aura_lock.locked():
            _aura_lock.release()
            released = True
    except RuntimeError:
        pass
    logger.info("Reset called — released: %s", released)
    return jsonify({"status": "success", "message": "Assistant state has been reset."})

@app.route("/contacts", methods=["GET"])
def get_contacts():
    try:
        from core.db import get_all_contacts
        return jsonify({"status": "ok", "contacts": get_all_contacts()})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route("/contacts", methods=["POST"])
def add_contact():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    if not name or not phone:
        return jsonify({"status": "error", "message": "name and phone are required"}), 400
    try:
        from core.db import save_contact
        save_contact(name, phone)
        return jsonify({"status": "ok", "message": f"Contact {name} saved."})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route("/contacts/<name>", methods=["DELETE"])
def remove_contact(name: str):
    try:
        from core.db import delete_contact
        deleted = delete_contact(name)
        if deleted:
            return jsonify({"status": "ok", "message": f"Contact {name} deleted."})
        return jsonify({"status": "not_found"}), 404
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route("/history", methods=["GET"])
def history():
    try:
        from core.ai_chat import get_conversation_history
        return jsonify({"status": "ok", "history": get_conversation_history()})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route("/history", methods=["DELETE"])
def clear_history():
    try:
        from core.ai_chat import clear_conversation
        clear_conversation()
        return jsonify({"status": "ok", "message": "Conversation cleared."})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

if __name__ == "__main__":
    port = int(next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--port"), 5000))
    use_ngrok = "--public" in sys.argv
    debug_mode = "--debug" in sys.argv

    if use_ngrok:
        try:
            from pyngrok import ngrok
            public_url = ngrok.connect(port)
            logger.info("AURA public URL: %s", public_url)
            print(f"\n{'=' * 55}")
            print(f"  ✅ AURA is live at: {public_url}")
            print(f"{'=' * 55}\n")
        except ImportError:
            print("pyngrok not installed. Run: pip install pyngrok")
            sys.exit(1)

    logger.info("Starting AURA on http://localhost:%d (debug=%s)", port, debug_mode)
    app.run(debug=debug_mode, port=port, host="0.0.0.0", threaded=True)
