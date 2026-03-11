from flask import Flask, render_template, jsonify, request
import main
from core.voice import get_web_updates
import threading

app = Flask(__name__)

# Global lock to prevent multiple requests from fighting for the microphone
vavi_lock = threading.Lock()
vavi_busy = False # We still keep this for quick status checks

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
    global vavi_busy
    
    # Wait up to 5 seconds to acquire the lock instead of instantly failing
    acquired = vavi_lock.acquire(timeout=5.0)
    if not acquired:
        return jsonify({"status": "error", "message": "VAVI is busy processing a previous command. Please wait."}), 400
    
    vavi_busy = True
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
        vavi_busy = False
        vavi_lock.release()

@app.route('/reset', methods=['POST'])
def reset():
    """Manually clear the lock and busy state if it gets stuck"""
    global vavi_busy
    try:
        # Check if held and release
        if vavi_lock.locked():
            vavi_lock.release()
        vavi_busy = False
        return jsonify({"status": "success", "message": "Assistant state has been reset."})
    except Exception as e:
        # If release errors (e.g. not owned by thread), just proceed
        vavi_busy = False
        return jsonify({"status": "success", "message": "Attempted to reset state."})

if __name__ == '__main__':
    import sys

    port = 5000
    use_ngrok = '--public' in sys.argv

    if use_ngrok:
        try:
            from pyngrok import ngrok
            public_url = ngrok.connect(port)
            print(f"\n{'='*50}")
            print(f"  VAVI is live! Share this URL:")
            print(f"  {public_url}")
            print(f"{'='*50}\n")
        except ImportError:
            print("pyngrok not installed. Run: pip install pyngrok")
            sys.exit(1)

    app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
