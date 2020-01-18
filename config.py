from os import environ

# Create dummy secrey key so we can use sessions
# SECRET_KEY = environ.get('SECRET_KEY')
SQLALCHEMY_ECHO = False
# SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')


# Flask-Security config
SECURITY_URL_PREFIX = "/admin"
# SECURITY_PASSWORD_HASH = environ.get('SECURITY_PASSWORD_HASH')
# SECURITY_PASSWORD_SALT = environ.get('SECURITY_PASSWORD_SALT')

# Flask-Security URLs, overridden because they don't put a / at the end
SECURITY_LOGIN_URL = "/login/"
SECURITY_LOGOUT_URL = "/logout/"
SECURITY_REGISTER_URL = "/register/"

SECURITY_POST_LOGIN_VIEW = "/admin/"
SECURITY_POST_LOGOUT_VIEW = "/admin/"
SECURITY_POST_REGISTER_VIEW = "/admin/"

# Flask-Security features
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask Mail
# MAIL_SERVER = environ.get('MAIL_SERVER')
# MAIL_PORT = environ.get('MAIL_PORT')
# MAIL_USE_TLS = environ.get('MAIL_USE_TLS')
# MAIL_USERNAME = environ.get('MAIL_USERNAME')
# MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')
# MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
# 
# ADMIN_EMAIL = environ.get('ADMIN_EMAIL')

# Create dummy secret key so we can use sessions
SECRET_KEY="SU190839YSNAKIJEOIFONIx"

# Create in-memory database
SQLALCHEMY_DATABASE_URI="mysql://root:root@localhost/registry"

SECURITY_PASSWORD_HASH="pbkdf2_sha512"
SECURITY_PASSWORD_SALT="ATGUOH*020BYMspiubahiughaerGOJAEGj"

# for mail
MAIL_SERVER="smtp.office365.com"
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_DEBUG=True
MAIL_USERNAME="oduntan@live.com"
MAIL_DEFAULT_SENDER="oduntan@live.com"
MAIL_PASSWORD="dimeji@19"

ADMIN_EMAIL="oduntan@live.com"