from flask import Blueprint, request, jsonify
from ..models.claim import Claim 
from flask import render_template,Blueprint, request, jsonify, abort
from app import db
from app.models.db_storage import DBStorage
from flask_login import login_required, current_user
from ..utils.matching_process import *
claim_bp = Blueprint('claim_bp', __name__)
storage = DBStorage(db)

@claim_bp.route('/claims', methods=['POST'])
@login_required
def create_claim():
    data = request.get_json()
    status = 'pending'
    new_claim = Claim(item_id=data['item_id'], user_id=current_user.id, status=status,additional_information=data['additional_information'])
    storage.new(new_claim)
    # calling matching process
    storage.save()
    potential_matches = find_potential_matches(new_claim)
    return jsonify({
        'message': 'Claim created successfully',
        'claim_id': new_claim.id,
        'potential_matches': [{'id': item.id, 'description': item.description, 'category': item.category} for item in potential_matches]
    }), 201    
    #return jsonify({'message': 'Claim created successfully', 'claim_id': new_claim.id}), 201

@claim_bp.route('/claims', methods=['GET'])
def get_claims():
    claims = Claim.query.all()
    return jsonify([{'id': claim.id, 'item_id': claim.item_id, 'user_id': claim.user_id, 'status': claim.status} 
        for claim in claims])

@claim_bp.route('/claims/<int:claim_id>', methods=['PUT'])
@login_required
def update_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    data = request.get_json()
    claim.status = data.get('status', claim.status)
    storage.save()
    return jsonify({'message': 'Claim updated successfully', 'claim_id': claim.id})

@claim_bp.route('/claims/<int:claim_id>', methods=['DELETE'])
@login_required
def delete_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    storage.delete(claim)
    storage.save()
    return jsonify({'message': 'Claim deleted successfully'})
