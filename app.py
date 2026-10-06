import os

from flask import Flask

import models
from routes.browse import bp as browse_bp
from routes.coursework import bp as coursework_bp
from routes.search import bp as search_bp


def create_app():
    app = Flask(__name__)
    app.config["DATABASE"] = os.path.join(app.root_path, "revision.db")
    app.teardown_appcontext(models.close_db)

    @app.context_processor
    def inject_levels():
        return {"LEVELS": models.LEVELS}

    app.register_blueprint(browse_bp)
    app.register_blueprint(coursework_bp)
    app.register_blueprint(search_bp)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
