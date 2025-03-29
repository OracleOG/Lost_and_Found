#!/usr/bin/python3
""" objects that handle all default RestFul API actions for Users """
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app, render_template
from app.models.user import User
from app.models.role import Role
from flask import render_template, Blueprint, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.db_storage import DBStorage
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm

from flask_mail import Message
from app import db, mail
from app.utils.forms import *
from urllib.parse import urlparse

# usecase for when username already exist
auth_bp = Blueprint('auth_bp', __name__)
storage = DBStorage(db)
bcrypt = Bcrypt()
# Initialize the URLSafeTimedSerializer
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    #form.role_id.choices = [(role.id, role.name) for role in Role.query.order_by('name')]
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        default_role = Role.query.filter_by(name='User').first()
        default_role_name = "User"
        if not default_role:
            # Create the default role if it doesn't exist
            default_role = Role(name=default_role_name)
            storage.new(default_role)
            storage.save()    
        
        user = User(username=form.username.data, email=form.email.data, password=form.password.data, role=default_role)
        storage.new(user)
        storage.save()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth_bp.login'))
    
    return render_template('/v2/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    # Redirect already logged in users
    if current_user.is_authenticated:
        return redirect(url_for('home_bp.home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # More efficient user lookup - only query once
            user = User.query.filter_by(username=form.username.data).first()
            
            # Check if user exists and password is correct
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                
                # Get the page the user was trying to access
                next_page = request.args.get('next')
                
                # Only redirect to 'next' if it's a relative path (security)
                if next_page and not urlparse(next_page).netloc:
                    flash('Logged in successfully!', 'success')
                    return redirect(next_page)
                else:
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('home_bp.home'))
            else:
                # Generic error - don't reveal whether username or password was incorrect
                flash('Invalid username or password', 'danger')
                
        except Exception as e:
            # Log the actual error for debugging
            current_app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('/v2/login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            s = get_serializer()
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Please click the link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset email sent.', 'success')
        else:
            flash('Email address not found.', 'error')
    return render_template('/v2/forgot_password.html')
    
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()  # Instantiate your form here
    print(f"Received token: {token}")  # Debug: Print the received token
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=48*3600)  # Token valid for 1 hour
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth_bp.forgot_password'))

    if request.method == 'POST':
        print(f"here  token: {token}")  # Debug2: Print the received token

        user = User.query.filter_by(email=email).first()
        password = request.form['password']
        user.password = password #issue fixed
        storage.save()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth_bp.login'))

    return render_template('/v2/reset_password.html',form=form, token=token)

