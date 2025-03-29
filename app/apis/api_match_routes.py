from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models.match import Match
from ..models.quality import QualityCheck
from app import db
from app.models.db_storage import DBStorage

match_bp = Blueprint('match_bp', __name__)
storage = DBStorage(db)

# Get all matches
@match_bp.route('/matches', methods=['GET'])
#@login_required
def get_matches():
    matches = Match.query.all()
    return jsonify([{
        'id': match.id,
        'item_id': match.item_id,
        'potential_owner_user_id': match.potential_owner_user_id,
        'status': match.status
    } for match in matches])

@match_bp.route('/matches/<int:match_id>/confirm', methods=['POST'])
@login_required
def confirm_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    #if current_user.role.name != 'QualityChecker':
    #    return jsonify({'error': 'Unauthorized access'}), 403

    # Create a new QualityCheck record
    quality_check = QualityCheck(
        match_id=match.id,
        quality_checker_user_id=current_user.id,
        confirmed_owner_user_id=match.potential_owner_user_id,
        verified='confirmed'
    )
    storage.new(quality_check)
    
    # Update the match status
    match.status = 'confirmed'
    storage.save()

    return jsonify({'message': 'Match confirmed successfully', 'match_id': match.id}), 200

# Create a new match
@match_bp.route('/matches', methods=['POST'])
@login_required
def create_match():
    data = request.get_json()
    new_match = Match(
        item_id=data['item_id'],
        potential_owner_user_id=data['potential_owner_user_id'],
        status='pending'
    )
    storage.new(new_match)
    storage.save()
    return jsonify({
        'message': 'Match created successfully',
        'match_id': new_match.id
    }), 201

# Update an existing match
@match_bp.route('/matches/<int:match_id>', methods=['PUT'])
@login_required
def update_match(match_id):
    data = request.get_json()
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    match.item_id = data.get('item_id', match.item_id)
    match.potential_owner_user_id = data.get('potential_owner_user_id', match.potential_owner_user_id)
    match.status = data.get('status', match.status)
    storage.save()

    return jsonify({'message': 'Match updated successfully'})

# Delete an existing match
@match_bp.route('/matches/<int:match_id>', methods=['DELETE'])
@login_required
def delete_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    storage.delete(match)
    storage.save()

    return jsonify({'message': 'Match deleted successfully'})

