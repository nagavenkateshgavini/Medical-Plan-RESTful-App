from flask import Flask

from config import Config

from extensions import redis_client


def create_app():
    app = Flask(__name__)
    app.config_class(Config)

    redis_client.init_app(app)

    from medical_plan_bp import bp as api_bp
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
