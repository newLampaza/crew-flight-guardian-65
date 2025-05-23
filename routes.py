
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import logging
from datetime import timedelta

# Import blueprints
from blueprints.auth import auth_bp, AuthError, handle_auth_error
from blueprints.fatigue_analysis import fatigue_bp
from blueprints.cognitive_tests import cognitive_bp
from blueprints.user_data import user_bp
from blueprints.feedback import feedback_bp
from blueprints.debug import debug_bp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'app.log',
            maxBytes=1024*1024*5,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app, 
     supports_credentials=True, 
     expose_headers=['Authorization'], 
     resources={r"/api/*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Register error handlers
@app.errorhandler(AuthError)
def handle_auth_error_app(ex):
    return handle_auth_error(ex)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(fatigue_bp)
app.register_blueprint(cognitive_bp)
app.register_blueprint(user_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(debug_bp)

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Проверяем существование директории для статических файлов
    static_dir = 'site/dist'
    if not os.path.exists(static_dir):
        logger.error(f"Static directory '{static_dir}' does not exist")
        return jsonify({"error": "Static files directory not found"}), 500
        
    if path and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    elif os.path.exists(os.path.join(static_dir, 'index.html')):
        return send_from_directory(static_dir, 'index.html')
    else:
        logger.error(f"index.html not found in {static_dir}")
        return jsonify({"error": "Frontend not built. Please run 'npm run build' first."}), 500

# Обработка запросов к /api/videos для корректного доступа к видеофайлам
@app.route('/api/videos/<path:filename>')
def serve_video(filename):
    video_dir = os.path.join('neural_network', 'data', 'video')
    if os.path.exists(os.path.join(video_dir, filename)):
        return send_from_directory(video_dir, filename, mimetype='video/mp4')
    else:
        return jsonify({"error": "Video file not found"}), 404

# Test sessions storage for cognitive tests
test_sessions = {}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
