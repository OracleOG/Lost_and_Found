import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.db_storage import DBStorage
from app.utils.forms import EditUserForm
from app.models.item import Item
from app.models.claim import Claim

user_profile_bp = Blueprint('user_profile_bp', __name__)
storage = DBStorage(db)

@user_profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile"""
    # Ensure profile image directory exists
    profile_image_dir = os.path.join(current_app.root_path, 'static/profile_images')
    if not os.path.exists(profile_image_dir):
        os.makedirs(profile_image_dir)
    
    form = EditUserForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Handle profile image upload
        if form.profile_image.data:
            file = form.profile_image.data
            # Generate unique filename with user ID
            filename = secure_filename(f"profile_{current_user.id}_{file.filename}")
            file_path = os.path.join(profile_image_dir, filename)
            file.save(file_path)
            current_user.profile_image_url = f"static/profile_images/{filename}"
        
        # Handle password change if provided
        if form.password.data:
            current_user.set_password(form.password.data)
        
        storage.save()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('user_profile_bp.profile'))

    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    # Get user's items and claims
    items = Item.query.filter_by(user_id=current_user.id).all()
    claims = Claim.query.filter_by(user_id=current_user.id).all()

    return render_template('v2/profile.html', form=form, title='My Profile', 
                          user=current_user, items=items, claims=claims)