#!venv/bin/python
import os
from flask import Flask, url_for
from flask_admin import helpers as admin_helpers
from flask_migrate import Migrate
from database import db
from flask_ckeditor import CKEditor
from frontend import frontend


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('config.py')
# db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)
ckeditor = CKEditor(app)


if __name__ == '__main__':
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))

    # Start app
    from admin import admin
    from security import security, user_datastore

    admin.init_app(app)
    app.register_blueprint(frontend)
    security._state = security.init_app(app, datastore=user_datastore)

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )
    app.run(host='0.0.0.0', debug=True)
