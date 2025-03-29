import os
from flask import Blueprint, request, jsonify, url_for
from ..models.claim import Claim
from ..models.match import Match
from ..models.item import Item 
from ..models.user import User
from flask import render_template,Blueprint, request, jsonify, abort
from app import db
from app.models.db_storage import DBStorage

item_bp_api = Blueprint('item_bp_api', __name__)
storage = DBStorage(db)

@item_bp_api.route('/api/items', methods=['GET'])
def get_items_with_claims():
    
    #items = Item.query.all()
    items = Item.query.filter_by(status='Found').all()
    item_data = []
    def get_filename(path):
        return os.path.basename(path)
    for item in items:
        claim_count = db.session.query(Claim).filter(Claim.item_id == item.id).count()
        match_count = db.session.query(Match).filter(Match.item_id == item.id).count()
        claims = Claim.query.filter(Claim.item_id == item.id).all()
        matches = Match.query.filter(Match.item_id == item.id).all()
        matches_data = [{
            'id': match.id,
            'status': match.status,
           
        } for match in matches]
        claims_data = [{
            'id': claim.id,
            'date_claimed': claim.date_claimed,
            'additional_information': claim.additional_information,
            'status': claim.status,
            'user_id': claim.user_id,
            'image_url': claim.image_url
        } for claim in claims]
        image_url = url_for('uploaded_file', filename=get_filename(item.image_url)) if item.image_url else url_for('static', filename='default-item-image.jpg')

        item_data.append({
            'id': item.id,
            'name': item.name,
            'email': item.email,
            'phone': item.phone,
            'item_name': item.item_name,
            'item_category': item.item_category,
            'item_color': item.item_color,
            'item_brand': item.item_brand,
            'date_lost_found': item.date_lost_found,
            'location_lost_found': item.location_lost_found,
            'image_url': image_url,
            'description': item.description,
            'category': item.category,
            'status': item.status,
            'date_reported': item.date_reported,
            'user_id': item.user_id,
            'claims_count': claim_count,
            'match_count': match_count,
            'claims': claims_data,
            'matches': matches_data
        })

    return jsonify({'items': item_data})

@item_bp_api.route('/items', methods=['POST'])
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
    #fix check if user exists
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

@item_bp_api.route('/items', methods=['GET'])
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

@item_bp_api.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@item_bp_api.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    storage.save()
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@item_bp_api.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    storage.delete(item)
    storage.save()
    return jsonify({'message': 'Item deleted'})

@item_bp_api.route('/upload', methods=['POST'])
def upload_file():
    """ routes when uploading images that is saved in the folder images"""
    None
