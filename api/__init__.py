from flask import Flask


def create_app():
    app = Flask(__name__)

    from . import pages  # noqa

    app.register_blueprint(pages.bp)

    return app
