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
    # Elasticsearch configuration - made optional
    app.elasticsearch = None
    es_url = app.config.get('ELASTICSEARCH_URL', '').strip()
    
    if es_url:  # Only try to initialize if URL is provided
        try:
            app.logger.info(f"Attempting to connect to Elasticsearch at: {es_url}")
            
            # Initialize with timeout and retry settings
            es = Elasticsearch(
                [es_url],
                verify_certs=False,  # Disable SSL verification for simplicity
                max_retries=3,
                retry_on_timeout=True,
                request_timeout=10  # 10 second timeout
            )
            
            # Test connection
            if es.ping():
                app.elasticsearch = es
                info = es.info()
                app.logger.info(f"Successfully connected to Elasticsearch. Version: {info.get('version', {}).get('number', 'unknown')}")
                app.logger.info(f"Cluster name: {info.get('cluster_name')}")
                app.logger.info(f"Cluster status: {info.get('status')}")
            else:
                app.logger.warning("Could not connect to Elasticsearch: Ping failed")
                
        except Exception as e:
            app.logger.warning(f"Elasticsearch connection failed: {str(e)}")
            app.logger.info("Application will continue without search functionality")
    else:
        app.logger.info("ELASTICSEARCH_URL not configured. Search functionality will be disabled.")

    # Redis config
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)

    # Register blueprints
    from app.errors import bp as errors_bp
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.api import bp as api_bp
    from app.cli import bp as cli_bp
    
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(cli_bp)

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
