import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from elasticsearch import Elasticsearch
from redis import Redis
import rq
from config import Config
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from urllib.parse import urlparse

def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    # elastic search config
    # Fixed Elasticsearch configuration
    app.elasticsearch = None  # Default to None

    es_url = app.config.get('ELASTICSEARCH_URL', '').strip()
    if es_url:  # Check if URL exists and is not empty
        try:
            parsed = urlparse(es_url)
            
            # For Heroku SearchBox/Elasticsearch
            if 'searchly.com' in es_url or 'searchbox.io' in es_url:
                if not all([parsed.scheme, parsed.hostname, parsed.port]):
                    raise ValueError("URL must include scheme, host, and port")
                print(parsed)
                
                app.elasticsearch = Elasticsearch(
                    [parsed.hostname],
                    http_auth=(parsed.username, parsed.password) if parsed.username and parsed.password else None,
                    scheme=parsed.scheme,
                    port=parsed.port,
                    max_retries=3,
                    retry_on_timeout=True,
                    request_timeout=30,
                    verify_certs=True  # Enable SSL for production
                )
            else:
                # For local development
                app.elasticsearch = Elasticsearch(
                    [es_url],
                    max_retries=3,
                    retry_on_timeout=True,
                    request_timeout=30,
                    verify_certs=False  # Disable SSL verification for local development
                )
            
            # Test the connection
            if not app.elasticsearch.ping():
                raise ConnectionError("Could not connect to Elasticsearch")
                
            info = app.elasticsearch.info()
            app.logger.info(f"Elasticsearch connection successful: {info.get('version', {}).get('number', 'unknown')}")
            
        except Exception as e:
            app.logger.warning(f"Elasticsearch initialization failed: {str(e)}")
            app.elasticsearch = None
    else:
        app.logger.info("Elasticsearch URL not configured, search functionality disabled")
    # Redis config
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/microblog.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app


from app import models
