#!/usr/bin/python3
""" objects that handle all default RestFul API actions for Users """
from flask import Blueprint, request, jsonify, redirect, url_for,flash,current_app
from ..models.user import User
from ..models.match import Match
from ..models.role import Role
from flask import render_template,Blueprint, request, jsonify, abort
from app import db
from app.models.db_storage import DBStorage , db
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm

from flask_mail import Message
from app import db, mail
from ..utils.forms import *
from flask_login import login_required, current_user

# usecase for when username already exist
user_bp = Blueprint('user_bp', __name__)
storage = DBStorage(db)
bcrypt = Bcrypt()
# Initialize the URLSafeTimedSerializer
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])



@user_bp.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('main.login'))
    
    return render_template('register.html', title='Register', form=form)
# routes for the list all users page 
# using paginatioons to display 5 users per page
@user_bp.route('/users')
@login_required
def list_users():
    users = User.query.all()
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.paginate(page=page, per_page=5)  # Change per_page to the number of users you want per page
    return render_template('list_users.html', users_pagination=users_pagination)
 # issues 
@user_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
#@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    print("Entering edit_user route")
    form = EditUserForm()
    if request.method == 'POST':
        print("Form Submitted",form);
    if form.validate_on_submit():
        print(f"Form Submitted with username: {form.username.data}, email: {form.email.data}")
        user.username = form.username.data
        user.email = form.email.data
        print(f"User email: {user.email}")
        print(f"User username: {user.username}")
        try:
            storage.save()
            flash('User updated successfully', 'success')
            return redirect(url_for('user_bp.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {e}', 'danger')
        storage.save()
        flash('User has been updated!', 'success')
        return redirect(url_for('user_bp.list_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    return render_template('edit_user.html', title='Edit User', form=form, user=user)

@user_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id) #fix 
    matches = Match.query.filter_by(potential_owner_user_id=user_id).first()
    if matches:
        flash('Cannot delete user. There are related matches that need to be handled first.', 'danger')
        return redirect(url_for('user_bp.list_users'))
    storage.delete(user)
    storage.save()
    flash('User has been deleted!', 'success')
    return redirect(url_for('user_bp.list_users'))

# apis 
@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    role_id = data.get('role_id')
    role = Role.query.get(role_id)
    if role is None:
        return jsonify({ 'error': 'Role ID is missing' }), 400
    user = User(username=data['username'], email=data['email'],role=role, password=data['password'])
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
def delete_user_2(user_id):
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
            s = get_serializer()
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('user_bp.reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Please click the link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset email sent.', 'success')
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot_password.html')
    
@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()  # Instantiate your form here
    print(f"Received token: {token}")  # Debug: Print the received token
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=48*3600)  # Token valid for 1 hour
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('user_bp.forgot_password'))

    if request.method == 'POST':
        print(f"here  token: {token}")  # Debug2: Print the received token

        user = User.query.filter_by(email=email).first()
        password = request.form['password']
        user.password = password #issue fixed
        storage.save()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html',form=form, token=token)

