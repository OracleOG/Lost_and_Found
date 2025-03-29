#!/usr/bin/python3
""" objects that handle all default RestFul API actions for Users """
from flask import Blueprint, request, jsonify, redirect, url_for,flash
from ..models.user import User
from ..models.role import Role
from flask import render_template,Blueprint, request, jsonify, abort
from app import db
from app.models.db_storage import DBStorage , db
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

# usecase for when username already exist
user_bp = Blueprint('user_bp', __name__)
storage = DBStorage(db)
bcrypt = Bcrypt()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    form.role_id.choices = [(role.id, role.name) for role in Role.query.order_by('name')]
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        role = Role.query.get(form.role_id.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        storage.new(user)
        storage.save()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', title='Register', form=form)

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    role_id = data.get('role_id')
    role = Role.query.get(role_id)
    if role is None:
        return jsonify({ 'error': 'Role ID is missing' }), 400
    user = User(username=data['username'], email=data['email'],role=role)
    user.set_password(data['password'])
    storage.new(user)
    storage.save()
    return jsonify({ 'message': 'User created successfully','id': user.id, 'username': user.username,
         'role': user.role.name
         ,'password': user.password,'email': user.email}), 201

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'email': user.email,
     'role': {'id': user.role.id, 'name': user.role.name} if user.role else None,   
        'password': user.password,} for user in users])

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.password = data.get('password', user.password)
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    storage.save()
    return jsonify({'message': 'User Updated successfully','id': user.id, 'username': user.username, 'email': user.email})

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    storage.delete(user)
    storage.save()
    return jsonify({'message': 'User deleted'})


@user_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Please click the link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset email sent.', 'success')
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot_password.html')
    
@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # Token valid for 1 hour
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        password = request.form['password']
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

