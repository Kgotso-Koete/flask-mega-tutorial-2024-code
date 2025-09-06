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
    sb_url = app.config.get('SEARCHBOX_URL', es_url).strip()
    
    if sb_url:  # Check if URL exists and is not empty
        try:
            parsed = urlparse(sb_url)
            
            # For Heroku SearchBox/Elasticsearch
            if 'searchly.com' in sb_url or 'searchbox.io' in sb_url:
                app.logger.info(f"Initializing Heroku SearchBox with: {sb_url.replace(parsed.password, '*****') if parsed.password else sb_url}")
                
                # Explicit parameter approach for Heroku SearchBox
                app.elasticsearch = Elasticsearch(
                    [parsed.hostname],
                    http_auth=(parsed.username, parsed.password),
                    scheme=parsed.scheme,
                    port=parsed.port or 443,  # Default to 443 for HTTPS
                    verify_certs=True,
                    ssl_show_warn=True,
                    max_retries=3,
                    retry_on_timeout=True,
                    request_timeout=30
                )
            else:
                # For local development
                app.logger.info(f"Initializing local Elasticsearch with URL: {sb_url}")
                app.elasticsearch = Elasticsearch(
                    [sb_url],
                    verify_certs=False,
                    ssl_show_warn=False,
                    max_retries=3,
                    retry_on_timeout=True,
                    request_timeout=30
                )
            
            # Test the connection with more detailed error handling
            try:
                if not app.elasticsearch.ping():
                    raise ConnectionError("Ping to Elasticsearch failed")
                    
                info = app.elasticsearch.info()
                app.logger.info(f"Elasticsearch connection successful. Version: {info.get('version', {}).get('number', 'unknown')}")
                app.logger.info(f"Cluster name: {info.get('cluster_name')}")
                app.logger.info(f"Cluster status: {info.get('status')}")
                
            except Exception as e:
                error_msg = f"Failed to connect to Elasticsearch: {str(e)}"
                if hasattr(e, 'info') and isinstance(e.info, dict):
                    error_msg += f"\nError details: {e.info}"
                app.logger.error(error_msg)
                raise ConnectionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Elasticsearch initialization failed: {str(e)}"
            if hasattr(e, 'info') and isinstance(e.info, dict):
                error_msg += f"\nError details: {e.info}"
            app.logger.error(error_msg)
            app.elasticsearch = None
            
            # For Heroku, try to log the exact URL being used (with password masked)
            if 'searchly.com' in sb_url or 'searchbox.io' in sb_url:
                masked_url = sb_url.replace(parsed.password, '*****') if parsed.password else sb_url
                app.logger.error(f"Connection attempt was made to: {masked_url}")
                app.logger.error(f"Host: {parsed.hostname}, Port: {parsed.port or 443}, Scheme: {parsed.scheme}")
                
            # Re-raise to ensure the app knows initialization failed
            raise
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
