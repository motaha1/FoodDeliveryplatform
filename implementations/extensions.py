from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Shared extensions (singletons) used by all features

db = SQLAlchemy()
bcrypt = Bcrypt()

