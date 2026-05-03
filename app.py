from flask import Flask, redirect, url_for, render_template, jsonify
from flask_login import LoginManager
from dotenv import load_dotenv
from models.user import db, User
from models.task import Task
from urllib.parse import quote_plus
import os

load_dotenv()

def create_app():
    app = Flask(__name__)

    db_password = quote_plus(os.getenv('DB_PASSWORD', ''))

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{db_password}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Debug: Confirm DB connection
    print("CONNECTED DB:", app.config['SQLALCHEMY_DATABASE_URI'])

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth
    from routes.tasks import tasks
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(tasks, url_prefix='/tasks')

    @app.route('/')
    def index():
        return redirect(url_for('tasks.dashboard'))

    # ✅ DEBUG ROUTE 1
    @app.route('/check')
    def check():
        users = User.query.all()
        tasks = Task.query.all()
        return jsonify({
            "users_count": len(users),
            "tasks_count": len(tasks)
        })

    # ✅ DEBUG ROUTE 2 (deep check)
    @app.route('/deep-check')
    def deep_check():
        users = User.query.all()
        tasks = Task.query.all()
        return jsonify({
            "users": [u.username for u in users],
            "tasks": [t.title for t in tasks]
        })

    # ── Error Handlers ─────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html',
                               code=404,
                               title='Page not found',
                               message='The page you are looking for does not exist.'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html',
                               code=500,
                               title='Server error',
                               message='Something went wrong on our end. Please try again.'), 500

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables ready")

    app.run(debug=True)