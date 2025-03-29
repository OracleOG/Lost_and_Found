from app import db
from app.models.base_model import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.role import Role
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from flask_login import UserMixin


class User(BaseModel, UserMixin):
    """User model with authentication and roles"""
    __tablename__ = 'users'

    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(String(100), nullable=False)
    items = db.relationship('Item', back_populates='user')
    claims = db.relationship('Claim', back_populates='user')
    role_id = db.Column(Integer, ForeignKey('roles.id'))
    role = db.relationship('Role', backref='users')
    profile_image = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return 'User: [id: {}, username: {}, Email: {}, role: {}'.format(self.id, self.username, self.email,self.role)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.id)
    
    def has_role(self, role_name):
        return self.role and self.role.name == role_name    
    @property
    def is_active(self):
        return True  # Example: Always return True for simplicity
   
    def __setattr__(self, name, value):
        """sets a password with md5 encryption"""
        if name == "password":
            value = generate_password_hash(value)
        super().__setattr__(name, value)
        '''
class User(BaseModel, UserMixin):
    """User model with authentication and roles"""
    __tablename__ = 'users'
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    items = db.relationship('Item', back_populates='user')
    claims = db.relationship('Claim', back_populates='user')

    def __repr__(self):
        return f"User: [id: {self.id}, username: {self.username}, Email: {self.email}, role: {self.role}]"

    def set_password(self, password):
        """Set password with hashing"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)

    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return str(self.id)

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.role and self.role.name == role_name

    @property
    def is_active(self):
        """Mark user as active (for Flask-Login)"""
        return True  # Adjust logic if needed (e.g., account status)

    def __setattr__(self, name, value):
        """Override setattr to hash password"""
        if name == "password":
            value = generate_password_hash(value)
        super().__setattr__(name, value)'
        '''