# app/main/v2/create_request.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.item import Item
from app.models.claim import Claim
from app.models.db_storage import DBStorage
from app.utils.forms import ItemUploadForm, ClaimForm
from werkzeug.utils import secure_filename
import os
import json

create_request_bp = Blueprint('create_request_bp', __name__)
storage = DBStorage(db)

@create_request_bp.route('/request', methods=['GET', 'POST'])
@login_required
def create_request():
    """Create a lost or found request"""
    form = ItemUploadForm()
    if form.validate_on_submit():
        file = form.image.data
        image_url = None
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = f"static/item_images/{filename}"  # Use filename directly for simplicity

        status = form.status.data.lower()  # 'lost' or 'found'

        # Convert date to string in ISO format
        date_lost_found = form.date_lost_found.data
        date_lost_found_str = date_lost_found.isoformat() if date_lost_found else None

        item_data = {
            'item_name': form.item_name.data,
            'description': form.description.data,
            'item_category': form.item_category.data,
            'item_color': form.item_color.data,
            'item_brand': form.item_brand.data,
            'date_lost_found': date_lost_found_str,
            'location_lost_found': form.location_lost_found.data,
            'image_url': image_url,
            'status': status,
            'user_id': current_user.id,
            'serial_number': form.serial_number.data if status == 'lost' else None,
            'warehouse_status': 'not_received' if status == 'found' else None
        }
        ''' 
        # would love to have an api call instead. but for now, i will just use the direct call
        
        # Call the API endpoint directly
        from app.apis.v2.items_route import create_item
        response, status_code = create_item(json.dumps(item_data), content_type='application/json')
        response_data = json.loads(response.get_data(as_text=True)) if response else {}

        if status_code == 201:
            item_id = response_data.get('id')  # Adjust based on your API response structure
            if status == 'lost':
                item = storage.get(Item, item_id)
                match_item = item.find_match() if item else None
                if match_item:
                    flash('Potential match item found! Please submit a claim.', 'info')
                    return redirect(url_for('create_request_bp.make_claim', item_id=match_item.id))
                elif not match_item:
                    related_items = item.find_related_items()
                    if related_items:
                        flash('Potential related items found! Please scroll & submit a claim where correct.', 'info')
                        return redirect(url_for('create_request_bp.related_items', items_id=[i.id for i in related_items]))
                    flash('No match found at this time. Please check back later.', 'info')
                flash(f'{status.capitalize()} item reported successfully!', 'success')
                return redirect(url_for('home_bp.home'))
        else:
            flash(f'Error creating item: {response_data.get("error", "unknown error")}', 'danger')
        '''

        # Directly create the item in the database 
        item = storage.create(Item, **item_data)

        if status == 'lost':
            match_item = item.find_match()
            if match_item:
                flash('Potential match item found! Please submit a claim.', 'info')
                return redirect(url_for('create_request_bp.make_claim', item_id=match_item.id))
            elif not match_item:
                related_items = item.find_related_items()
                if related_items:
                    flash('Potential related items found! Please scroll & submit a claim where correct.', 'info')
                    return redirect(url_for('create_request_bp.related_items', items_id=','.join([str(i[0].id) for i in related_items])))
                flash('No match found at this time. Please check back later.', 'info')
            flash(f'{status.capitalize()} item reported successfully!', 'success')
        return redirect(url_for('home_bp.home'))
        
    return render_template('/v2/upload_item.html', form=form, title='Report Item')

@create_request_bp.route('/make_claim/<item_id>', methods=['GET', 'POST'])
@login_required
def make_claim(item_id):
    """Create a claim for a found item"""
    # Get the item directly
    item = storage.get(Item, item_id)
    if not item or item.status != 'found':
        flash('Invalid or unclaimable item', 'danger')
        return redirect(url_for('home_bp.home'))

    form = ClaimForm()
    if form.validate_on_submit():
        # Handle file upload if present
        file = form.proof_image.data
        proof_image_url = None
        if file:
            # Generate unique filename with user ID and timestamp
            import time
            timestamp = int(time.time())
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{current_user.id}_{timestamp}{file_extension}"
            
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            proof_image_url = f"static/item_images/{unique_filename}"
        
        try:
            # Create claim directly
            new_claim = Claim(
                item_id=item.id,
                user_id=current_user.id,
                status='pending',
                additional_information=form.additional_information.data,
                proof_image_url=proof_image_url,
                # Fix here: use location_lost instead of location_lost_found
                location_lost=form.location_lost.data if hasattr(form, 'location_lost') else None,
                date_lost=form.date_lost.data if hasattr(form, 'date_lost') else None
            )
            
            # Add to database
            storage.new(new_claim)
            storage.save()
    
            
            flash(f'Claim submitted successfully! Claim ID: {new_claim.id}', 'success')
            return redirect(url_for('home_bp.home'))
            
        except Exception as e:
            flash(f'Error creating claim: {str(e)}', 'danger')
            return render_template('/v2/make_claim.html', item=item, form=form, title='Make Claim')

    return render_template('/v2/make_claim.html', item=item, form=form, title='Make Claim')

@create_request_bp.route('/related_items/<items_id>', methods=['GET'])  # Fixed route syntax
@login_required
def related_items(items_id):
    """View related items to potentially claim"""
    items = []
    if not items_id:
        flash('No related items found', 'info')
        return redirect(url_for('home_bp.home'))
    else:
        for item_id in items_id.split(','):  # Assuming items_id is a comma-separated string
            item = storage.get(Item, item_id)
            if item and item.status == 'found':
                items.append(item.to_dict())
        if not items:
            flash('No valid related items found', 'info')
            return redirect(url_for('home_bp.home'))
        return render_template('/v2/related_items.html', items=items, title='Related Items')