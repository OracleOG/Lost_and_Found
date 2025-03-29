import os
from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from app import db
from app.models.claim import Claim
from app.models.item import Item
from app.models.user import User
from app.models.db_storage import DBStorage
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

claim_bp_api = Blueprint('claim_bp_api', __name__, url_prefix='/api/v2')
storage = DBStorage(db)

@claim_bp_api.route('/claims', methods=['POST'])
@login_required
def create_claim():
    """Create a new claim for a verified lost item"""
    try:
        data = request.get_json()
        if not data or 'item_id' not in data:
            return jsonify({'error': 'Missing item_id'}), 400
        
        # Verify the item exists and is claimable (e.g., status='found')
        item = storage.get(Item, data['item_id'])
        if not item or item.status != 'found':
            return jsonify({'error': 'Invalid or unclaimable item'}), 400

        # Create claim
        new_claim = Claim(
            item_id=data['item_id'],
            user_id=current_user.id,
            status='pending',
            additional_information=data.get('additional_information'),
            proof_image_url=data.get('proof_image_url')
        )
        storage.new(new_claim)
        storage.save()

        # Update item status to 'claimed'
        item.status = 'claimed'
        storage.save()

        return jsonify({
            'message': 'Claim created successfully',
            'claim_id': new_claim.id
        }), 201
    except SQLAlchemyError as e:
        logger.error(f"Failed to create claim: {e}")
        return jsonify({'error': 'Database error'}), 500

@claim_bp_api.route('/claims/search', methods=['POST'])
@login_required
def search_claims():
    """Search for claims by description"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({'error': 'Missing description'}), 400

        # Search claims by additional_information (or extend to item description)
        claims = storage.filter(Claim, additional_information=data['description'])
        if not claims:
            # Fallback: search items if no direct claim match
            items = storage.filter(Item, description=data['description'])
            claims = [claim for item in items for claim in item.claims] if items else []

        return jsonify([{
            'id': claim.id,
            'item_id': claim.item_id,
            'user_id': claim.user_id,
            'status': claim.status,
            'additional_information': claim.additional_information,
            'proof_image_url': claim.proof_image_url
        } for claim in claims]), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to search claims: {e}")
        return jsonify({'error': 'Database error'}), 500

@claim_bp_api.route('/claims/<int:claim_id>', methods=['PUT'])
@login_required
def update_claim(claim_id):
    """Update an existing claim"""
    try:
        claim = storage.get(Claim, claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        if claim.user_id != current_user.id and not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400
        if 'status' in data and data['status'] not in ['pending', 'approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        claim.status = data.get('status', claim.status)
        claim.additional_information = data.get('additional_information', claim.additional_information)
        claim.proof_image_url = data.get('proof_image_url', claim.proof_image_url)
        storage.save()

        return jsonify({
            'message': 'Claim updated successfully',
            'claim_id': claim.id
        }), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to update claim: {e}")
        return jsonify({'error': 'Database error'}), 500

@claim_bp_api.route('/claims/<int:claim_id>', methods=['DELETE'])
@login_required
def delete_claim(claim_id):
    """Delete an existing claim"""
    try:
        claim = storage.get(Claim, claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        if claim.user_id != current_user.id and not current_user.has_role('quality_checker'):
            return jsonify({'error': 'Unauthorized'}), 403

        storage.delete(claim)
        storage.save()
        return jsonify({'message': 'Claim deleted successfully'}), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete claim: {e}")
        return jsonify({'error': 'Database error'}), 500

# Retained from v1 for detailed claim view (optional)
@claim_bp_api.route('/claims/<int:claim_id>', methods=['GET'])
@login_required
def get_claim(claim_id):
    """Retrieve detailed info about a specific claim"""
    try:
        claim = storage.get(Claim, claim_id)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        user = storage.get(User, claim.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        

        def get_filename(path):
            return os.path.basename(path) if path else None
        item_image_url = url_for('static', filename=f'images/{get_filename(item.image_url)}') if item.image_url else url_for('static', filename='default-item-image.jpg')

        return jsonify({
            'claim_id': claim.id,
            'status': claim.status,
            'additional_information': claim.additional_information,
            'proof_image_url': claim.proof_image_url,
            'user_id': claim.user_id,
            'user_name': user.name,
            'user_email': user.email,
            'date_lost': claim.date_lost,
            'location_lost': claim.location_lost,
            'claim_date': claim.created_at,
            'item_id': claim.item_id,
        }), 200
    except SQLAlchemyError as e:
        logger.error(f"Failed to get claim: {e}")
        return jsonify({'error': 'Database error'}), 500