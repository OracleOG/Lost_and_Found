from flask import Blueprint, request, jsonify, send_from_directory

from app.models.claim import Claim
from app.utils.matching_process import find_potential_matches, find_potential_matches_for_lost_item
from ..models.item import Item 
from ..models.user import User
from flask import render_template,Blueprint, request, jsonify, abort
from app import db
from app.models.db_storage import DBStorage
from flask_wtf.csrf import generate_csrf

item_bp = Blueprint('item_bp', __name__)
storage = DBStorage(db)

import os
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..models.item import Item
from ..utils.forms import ItemUploadForm
from app import db

#item_bp = Blueprint('item_bp', __name__)

 
@item_bp.route('/upload_item', methods=['GET', 'POST'])
@login_required
def upload_item():
    form = ItemUploadForm()
    if form.validate_on_submit():
        file = form.image.data
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # status based on user role
            if current_user.has_role('USER') and form.status.data  == 'Found':
                item_status = 'Report'
            elif current_user.has_role('ADMIN') and form.status.data  == 'Found':
                item_status = 'Found'
            else:
                item_status = form.status.data  

            new_item = Item(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                item_name=form.item_name.data,
                item_category=form.item_category.data,
                item_color=form.item_color.data,
                item_brand=form.item_brand.data,
                date_lost_found=form.date_lost_found.data,
                location_lost_found=form.location_lost_found.data,
                description=form.description.data,
                status=item_status,
                image_url=file_path,
                user_id=current_user.id
            )
            storage.new(new_item)
            storage.save()
            
            if new_item.status == 'Lost':
                print("new_item",new_item.status)
                potential_matches = find_potential_matches_for_lost_item(new_item)
            flash('Item uploaded successfully!', 'success')
            return redirect(url_for('item_bp.list_items'))
    return render_template('upload_item.html', form=form)
@login_required
@item_bp.route('/items', methods=['GET'])
def list_items():
    page = request.args.get('page', 1, type=int)  
    items_per_page = 10  # Adjust this number to your needs  
    items = Item.query.paginate(page=page, per_page=items_per_page)  
    return render_template('list_items.html', items=items)  

@item_bp.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    new_item = Item(
            description=data['description'],
            category=data['category'],
            status=data['status'],
            name=data['name'],
            date_reported=data.get('date_reported'),
            user_id=data['user_id'])
    storage.new(new_item)
    storage.save()
    #fix check if user exists -- done 
    return jsonify({
        'message': 'Item created successfully',
        'item': {
            'id': new_item.id,
            'name': new_item.name,
            'description': new_item.description,
            'category': new_item.category,
            'status': new_item.status,
            'date_reported': new_item.date_reported.isoformat(),
            'user_id': new_item.user_id
        }
    }), 201
#@csrf_exempt   
@item_bp.route('/items/claim', methods=['POST'])
@login_required
def claim_item():
    item_id = request.form.get('item_id')
    item = Item.query.get_or_404(item_id)
    
    file = request.files.get('image')
    print("file is ",file)
    image_filename = None
    if file and file.filename:
        image_filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
        print("file is ",image_filename)
        new_claim = Claim(
            item_id=item.id,
            user_id=current_user.id,
            status='pending',
            additional_information=request.form.get('additional_information'),
            image_url=image_filename
         )
    
        storage.new(new_claim)
        storage.save()
        potential_matches = find_potential_matches(new_claim)

        flash('Item claimed successfully', 'success')
    return redirect(url_for('item_bp.list_items'))

@item_bp.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@item_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_details.html', item=item)

@item_bp.route('/items_pending', methods=['GET'])
#admin page
def list_items_admin():
    page = request.args.get('page', 1, type=int)
    items_per_page = 10   
    items = Item.query.filter_by(status='pending').paginate(page=page, per_page=items_per_page)
    return render_template('list_items.html', items_pagination=items)

@item_bp.route('/items/confirm_item', methods=['POST'])
def confirm_item():
    item_id = request.form.get('item_id')
    print("item_id",item_id)
    item = Item.query.get_or_404(item_id)
    item.status = 'Found'
    storage.save()
    flash('Item status updated to "found".', 'success')
    return redirect(url_for('item_bp.item_detail', item_id=item.id))

@item_bp.route('/items/delete_item', methods=['POST'])
def delete_item():
    item_id = request.form.get('item_id')
    item = Item.query.get_or_404(item_id)
    storage.delete(item)
    storage.save()
    flash('Item successfully deleted.', 'success')
    return redirect(url_for('item_bp.list_items'))

@item_bp.route('/items', methods=['GET'])
def search_items():
    status = request.args.get('status')
    category = request.args.get('category')
    keyword = request.args.get('keyword')

    query = Item.query
    if status:
        query = query.filter(Item.status == status)
    if category:
        query = query.filter(Item.category == category)
    if keyword:
        query = query.filter(Item.description.contains(keyword))

    items = query.all()
    return jsonify([{'id': item.id, 'description': item.description, 'category': item.category,
        'status': item.status, 'date_reported': item.date_reported.isoformat(),
        'name': item.name,
        'User': {
            'id': item.user.id,
            'username': item.user.username
            } if item.user else 'NO-user'# fix
        }for item in items])

@item_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@item_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    storage.save()
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@item_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item_api(item_id):
    item = Item.query.get_or_404(item_id)
    storage.delete(item)
    storage.save()
    return jsonify({'message': 'Item deleted'})

@item_bp.route('/upload', methods=['POST'])
def upload_file():
    """ routes when uploading images that is saved in the folder images"""
    None
