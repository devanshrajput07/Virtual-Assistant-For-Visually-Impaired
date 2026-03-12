import threading
import sys
from flask import Flask, render_template, jsonify, request
import main
from core.voice import get_web_updates

app = Flask(__name__)

# Global lock to prevent multiple requests from fighting for the microphone
aura_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/updates', methods=['GET'])
def updates():
    """Poll for pending speech updates from the backend"""
    msgs = get_web_updates()
    return jsonify({"messages": msgs})

@app.route('/listen', methods=['POST'])
def listen():
    # Wait up to 5 seconds to acquire the lock instead of instantly failing
    acquired = aura_lock.acquire(timeout=5.0)
    if not acquired:
        return jsonify({"status": "error", "message": "AURA is busy processing a previous command. Please wait."}), 400
    
    try:
        result = main.handle_single_command()
        return jsonify({
            "status": "success",
            "command": result["command"],
            "lang_code": result.get("lang_code", "en-US"),
            "response": result["response"]
        })
    except Exception:
        return jsonify({"status": "error", "message": "Something went wrong processing your request."}), 500
    finally:
        aura_lock.release()

@app.route('/reset', methods=['POST'])
def reset():
    """Manually clear the lock state if it gets stuck"""
    try:
        if aura_lock.locked():
            aura_lock.release()
        return jsonify({"status": "success", "message": "Assistant state has been reset."})
    except Exception:
        return jsonify({"status": "success", "message": "Attempted to reset state."})

if __name__ == '__main__':
    port = 5000
    use_ngrok = '--public' in sys.argv

    if use_ngrok:
        try:
            from pyngrok import ngrok
            public_url = ngrok.connect(port)
            print(f"\n{'='*50}")
            print(f"  AURA is live! Share this URL:")
            print(f"  {public_url}")
            print(f"{'='*50}\n")
        except ImportError:
            print("pyngrok not installed. Run: pip install pyngrok")
            sys.exit(1)

    app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
