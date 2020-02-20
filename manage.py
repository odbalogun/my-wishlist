from flask_script import Manager
from app import app, db
from models import Role

manager = Manager(app)


@manager.command
def seed():
    check = Role.query.filter_by(name='basic').all()
    if check:
        print('Roles already exist')
    else:
        role_1 = Role(name='basic', description="Basic User")
        role_2 = Role(name='superuser', description="Super User")
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.commit()
        print("Completed successfully...")

if __name__ == "__main__":
    manager.run()