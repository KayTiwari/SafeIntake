from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .models import db
from .routes import audit, documents, entities


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(documents.bp)
    app.register_blueprint(entities.bp)
    app.register_blueprint(audit.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_error(err):
        return jsonify({"error": getattr(err, "description", str(err))}), err.code

    return app


app = create_app()
