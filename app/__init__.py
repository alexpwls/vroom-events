import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_babel import Babel, lazy_gettext as _l
from config import Config
import logging
from logging.handlers import SMTPHandler
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    mail.init_app(app)
    babel.init_app(app)

    from app.events import bp as events_bp
    app.register_blueprint(events_bp)

    # Email scheduel
    scheduler = BackgroundScheduler()
    from app.events.qteam.send_results import send_results_qteam
    from app.events.suzuki.send_results import send_results_suzuki

    # Schedule the send_email job, passing the app object
    scheduler.add_job(send_results_qteam, 'cron', args=[app], hour=14, minute=56)
    scheduler.add_job(send_results_suzuki, 'cron', args=[app], hour=14, minute=56)
    scheduler.start()

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
                toaddrs=app.config['ADMINS'], subject='VROOM Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

    return app

@babel.localeselector
def get_locale():
    locale = request.accept_languages.best_match(current_app.config['LANGUAGES'])
    
    if locale not in current_app.config['LANGUAGES']:
        locale = 'nl'
    
    return locale

