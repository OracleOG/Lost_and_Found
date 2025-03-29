from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.match import Match
from app.models.claim import Claim
from app.models.item import Item
from app.models.db_storage import DBStorage
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

match_bp_api = Blueprint('match_bp_api', __name__, url_prefix='/api/v2')
storage = DBStorage(db)

@match_bp_api.route('/matches', methods=['GET'])
@login_required
def get_matches():
    """Get all matches (QC or admin only)"""
    try:
        if not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        matches = storage.all(Match)
        return jsonify([{
            'id': match.id,
            'item_id': match.item_id,
            'claim_id': match.claim_id,
            'status': match.status
        } for match in matches.values()]), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to get matches: {e}")
        return jsonify({'error': 'Database error'}), 500

@match_bp_api.route('/matches', methods=['POST'])
@login_required
def create_match():
    """Create a new match (QC only, one per item)
        data = {
            'item_id': int,
            'claim_id': int
        }"""
    try:
        if not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        if not data or 'item_id' not in data or 'claim_id' not in data:
            return jsonify({'error': 'Missing item_id or claim_id'}), 400

        item = storage.get(Item, data['item_id'])
        claim = storage.get(Claim, data['claim_id'])
        if not item or not claim:
            return jsonify({'error': 'Item or Claim not found'}), 404
        if item.id != claim.item_id:
            return jsonify({'error': 'Claim does not match item'}), 400
        if storage.filter(Match, item_id=item.id):
            return jsonify({'error': 'Item already has a match'}), 400

        new_match = Match(
            item_id=data['item_id'],
            claim_id=data['claim_id'],
            status='confirmed'
        )
        storage.new(new_match)
        storage.save()

        # Update item status to resolved
        item.status = 'resolved'
        storage.save()

        return jsonify({
            'message': 'Match created successfully',
            'match_id': new_match.id
        }), 201
    except SQLAlchemyError as e:
        logger.error(f"Failed to create match: {e}")
        return jsonify({'error': 'Database error'}), 500

@match_bp_api.route('/matches/<int:match_id>', methods=['PUT'])
@login_required
def update_match(match_id):
    """Update a match (QC only)"""
    try:
        if not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        match = storage.get(Match, match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404

        data = request.get_json()
        match.status = data.get('status', match.status).lower()
        if match.status == 'confirmed':
            item = storage.get(Item, match.item_id)
            item.status = 'resolved'
            storage.save()

        storage.save()
        return jsonify({
            'message': 'Match updated successfully',
            'match_id': match.id
        }), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to update match: {e}")
        return jsonify({'error': 'Database error'}), 500

@match_bp_api.route('/matches/<int:match_id>', methods=['DELETE'])
@login_required
def delete_match(match_id):
    """Delete a match (QC only)"""
    try:
        if not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        match = storage.get(Match, match_id)
        if not match:
            return jsonify({'error': 'Match not found'}), 404

        storage.delete(match)
        storage.save()
        return jsonify({'message': 'Match deleted successfully'}), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete match: {e}")
        return jsonify({'error': 'Database error'}), 500