import os
from flask import Blueprint, request, jsonify, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models.item import Item
from app.models.claim import Claim
from app.models.match import Match
from app.models.user import User
from app.models.db_storage import DBStorage
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc  # Import desc for descending order
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

item_bp_api = Blueprint('item_bp_api', __name__, url_prefix='/api/v2')
storage = DBStorage(db)

@item_bp_api.route('/items', methods=['GET'])
@login_required
def get_items_with_claims():
    """Get items with their claims, filtered by status or item_id"""
    try:
        status = request.args.get('status')  # e.g., 'found', 'lost'
        item_id = request.args.get('item_id', type=int)

        query = storage.query(Item)
        if item_id:
            query = query.filter_by(id=item_id)
        elif status:
            query = query.filter_by(status=status.lower())
        else:
            query = query  # All items if no filter (restrict in prod?)

        items = query.all()
        if item_id and not items:
            return jsonify({'error': 'Item not found'}), 404

        def get_filename(path):
            return os.path.basename(path) if path else None

        item_data = []
        for item in items:
            claims = storage.filter(Claim, item_id=item.id)
            match = storage.filter(Match, item_id=item.id)  # Only one match allowed
            image_url = url_for('static', filename=f'images/{get_filename(item.image_url)}') if item.image_url else url_for('static', filename='default-item-image.jpg')

            item_data.append({
                'id': item.id,
                'item_name': item.item_name,
                'description': item.description,
                'item_category': item.item_category,
                'item_color': item.item_color,
                'item_brand': item.item_brand,
                'date_lost_found': item.date_lost_found.isoformat() if item.date_lost_found else None,
                'location_lost_found': item.location_lost_found,
                'image_url': image_url,
                'status': item.status,
                'user_id': item.user_id,
                'claims_count': len(claims),
                'match_id': match[0].id if match else None,
                'claims': [{
                    'id': claim.id,
                    'status': claim.status,
                    'additional_information': claim.additional_information,
                    'proof_image_url': claim.proof_image_url,
                    'user_id': claim.user_id
                } for claim in claims]
            })

        return jsonify({'items': item_data}), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to get items: {e}")
        return jsonify({'error': 'Database error'}), 500


@item_bp_api.route('/qc_items', methods=['POST'])
@login_required
def list_items_for_qc():
    """list items with claims that need quality checking
        REQUIREMENTS:
            - Allows filters for kind of items to be returned. i.e. status, category, date range etc.
            - if no filter is provided, return all items with claims of status 'pending'
            
        data:
            - Search input
            - Category
            - Date range (start)
            - Date range (end)
            - Page (optional, default)
            - per_page (optional, default)
            """
    
    if request.get_json() is None:
        abort(400, description="Not a JSON")

    data = request.get_json()

    # Extract filters and pagination parameters
    search_input = data.get('search_input', None)
    category = data.get('category', None)
    date_range_start = data.get('date_range_start', None)
    date_range_end = data.get('date_range_end', None)
    page = data.get('page', 1)
    per_page = data.get('per_page', 10)

    # base query for items with pending claims
    query = db.session.query(Item).join(Claim, Item.id == Claim.item_id).filter(
        Item.status == 'found',
        Claim.status == 'pending'
    )

    
    # Apply filters
    if search_input:
        query = query.filter(
            Item.item_name.ilike(f'%{search_input}%') |
            Item.item_category.ilike(f'%{search_input}%')
        )
    if category:
        query = query.filter(
            Item.item_category == category
        )
    if date_range_start:
        query = query.filter(
            Item.date_lost_found >= datetime.fromisoformat(date_range_start)
        )
    if date_range_end:
        query = query.filter(
            Item.date_lost_found <= datetime.fromisoformat(date_range_end)
        )
    print(f"search_input: {search_input}, category: {category}, date_range_start: {date_range_start}, date_range_end: {date_range_end}")
    print(f"Query: {query}")
    # execute query and convert to pagination
    pagination = storage.paginate_query(query, page=page, per_page=per_page)

    # convert items to dictionary
    items = []
    for item in pagination.items:
        item_dict = item.to_dict()
        item_dict['claims'] = [claim.to_dict() for claim in item.claims]
        items.append(item_dict)
    print(items)
    # build response dictionary
    response = {
        'items': items,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'total_items': pagination.total
    }

    return jsonify(response), 200



@item_bp_api.route('/items', methods=['POST'])
@login_required
def create_item():
    """Create a new item"""
    try:
        data = request.get_json()
        if not data or 'item_name' not in data or 'status' not in data:
            return jsonify({'error': 'Missing required fields (item_name, status)'}), 400

        new_item = Item(
            item_name=data['item_name'],
            description=data.get('description', ''),
            item_category=data.get('item_category', ''),
            item_color=data.get('item_color', ''),
            item_brand=data.get('item_brand'),
            date_lost_found=data.get('date_lost_found'),
            location_lost_found=data.get('location_lost_found', ''),
            image_url=data.get('image_url'),
            status=data['status'].lower(),
            user_id=current_user.id
        )
        storage.new(new_item)
        storage.save()

        return jsonify({
            'message': 'Item created successfully',
            'item_id': new_item.id
        }), 201
    except SQLAlchemyError as e:
        logger.error(f"Failed to create item: {e}")
        return jsonify({'error': 'Database error'}), 500

@item_bp_api.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    """Delete an item"""
    try:
        item = storage.get(Item, item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        if item.user_id != current_user.id and not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        # Check if item has a match (only one allowed)
        if storage.filter(Match, item_id=item_id):
            return jsonify({'error': 'Cannot delete item with an active match'}), 400

        storage.delete(item)
        storage.save()
        return jsonify({'message': 'Item deleted successfully'}), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete item: {e}")
        return jsonify({'error': 'Database error'}), 500

@item_bp_api.route('/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    """Update an item"""
    try:
        item = storage.get(Item, item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        if item.user_id != current_user.id and not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        item.item_name = data.get('item_name', item.item_name)
        item.description = data.get('description', item.description)
        item.item_category = data.get('item_category', item.item_category)
        item.item_color = data.get('item_color', item.item_color)
        item.item_brand = data.get('item_brand', item.item_brand)
        item.date_lost_found = data.get('date_lost_found', item.date_lost_found)
        item.location_lost_found = data.get('location_lost_found', item.location_lost_found)
        item.image_url = data.get('image_url', item.image_url)
        item.status = data.get('status', item.status).lower() if data.get('status') else item.status
        storage.save()

        return jsonify({
            'message': 'Item updated successfully',
            'item_id': item.id
        }), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to update item: {e}")
        return jsonify({'error': 'Database error'}), 500
    

@item_bp_api.route('/found_items', methods=['GET'])
@login_required
def found_items():
    """Get all found items based on filter submitted
    Requirements:
        - Carry out fuzzy search to match names and descriptions
        - If no filter, return all items with status 'found', sorted by latest items first, paginated response
        - If query filters added, then filter your query results, paginated response
        - For each item append: item_name, time_created, number of claims, user_profile_image, item_image, location_found
    """
    # Extract query param
    search_query = request.args.get('search_query', None)
    category = request.args.get('category', None)
    date_start = request.args.get('date_start', None)
    date_end = request.args.get('date_end', None)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Base query for items with status 'found'
    query = db.session.query(Item).filter(Item.status == 'found')
    
    if search_query:
        query = query.filter(
        (Item.item_name.ilike(f'%{search_query}')) |
        (Item.description.ilike(f'%{search_query}'))
        )
        
        
    if category:
        query = query.filter(Item.item_category == category)
        
    if date_start:
        query = query.filter(Item.date_lost_found >= date_start)
    if date_end:
        query = query.filter(Item.date_lost_found <= date_end)

    # Sort by latest item first
    query = query.order_by(desc(Item.date_lost_found))

    # paginate the query
    pagination = storage.paginate_query(query, page=page, per_page=per_page)

    # Build response with additional fields
    items = []

    for item in pagination.items:
        number_of_claims = db.session.query(Claim).filter(
            Claim.item_id == item.id
        ).count()

        # get user profile image (assuming User has profile_image field)
        user = db.session.query(User).get(item.user_id)
        user_profile_image = user.profile_image if user and hasattr(user, 'profile_image') else None
        
        
        item_dict = {
            'id': item.id,
            'item_name': item.item_name,
            'time_created': item.date_lost_found.isoformat() if item.date_lost_found else None,
            'number_of_claims': number_of_claims,
            'user_profile_image': user_profile_image,
            'item_image': item.image_url,
            'location_found': item.location_lost_found
        }

        items.append(item_dict)
    
    response = {
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': per_page
    }

    return jsonify(response), 200

    

@item_bp_api.route('/item/<item_id>', methods=['GET'])
@login_required
def describe_item(item_id):
    """Get item details
    Requirements:
        - Return item details: item_name, item_category, item_color, item_brand, date_lost_found, location_lost_found, image_url
        - Amount of details returned depends on user role
        - If user is admin or QC, return all details
        - If user role is basic, return only: item_name, item_image, location_found
    """
    # Fetch the item
    
    item = storage.get(Item, item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Determine user role (assuming User model has has_role method)
    if current_user.has_role('admin') or current_user.has_role('quality_checker'):
        # Full details for admin or QC


        item_details = {
            'item_name': item.item_name,
            'item_category': item.item_category,
            'item_color': item.item_color,
            'item_brand': item.item_brand,
            'date_lost_found': item.date_lost_found.isoformat() if item.date_lost_found else None,
            'location_lost_found': item.location_lost_found,
            'image_url': item.image_url
        }
    else:
        # Limited details for basic users
        item_details = {
            'item_name': item.item_name,
            'item_image': item.image_url,
            'location_found': item.location_lost_found
        }

    return jsonify(item_details), 200