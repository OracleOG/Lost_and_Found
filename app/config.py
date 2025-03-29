# /app/config.py
import os
import secrets
from dotenv import load_dotenv

load_dotenv()




class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(16))
    #the below code is bad practice
    #SECRET_KEY = 'e8be6c76f90f01893eedc58ee07c65fcc1e4339b1a854dc1edc9969402a84bc2'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'images') 
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/item_images')
    # In your app configuration
   
    #UPLOAD_FOLDER = os.path.join(app.root_path, 'static/item_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'marwaasabon@gmail.com'
    MAIL_PASSWORD = 'kcybbulukyxkdxzo' #ge
    MAIL_DEFAULT_SENDER = 'marwasabon@gmail.com'
    
