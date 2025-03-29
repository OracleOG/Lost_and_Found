from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.item import Item
from app.models.claim import Claim
from app.models.match import Match
from app.models.db_storage import DBStorage
import json

quality_checker_bp = Blueprint('quality_checker_bp', __name__)
storage = DBStorage(db)

@quality_checker_bp.route('/qc/items', methods=['GET'])
@login_required
def list_items_for_qc():
    """List items with claims for quality checking"""
    '''if not current_user.has_role('quality_checker'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home_bp.home'))'''

    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = db.session.query(Item).join(Claim, Item.id == Claim.item_id).filter(
        Item.status == 'found', Claim.status == 'pending'
    )
    pagination = storage.paginate_query(query, page=page, per_page=per_page)
    return render_template('/v2/qc_list.html', items=pagination, page=page)

@quality_checker_bp.route('/qc/<int:item_id>', methods=['GET'])
@login_required
def perform_qc_on_item(item_id):
    """Perform quality check on an item
    
    requirements:
        - item must have at least one claim else return error; qc cant be done
        - show item and the various claims that are on that item
        - clicking on any claim will display claim details on a panel
        so you can cross-check with the item
        - you can approve or reject a claim
        - if you approve a claim, a match is created
        - only one claim can be approved per item"""
    #if not current_user.has_role('quality_checker'):
     #   flash('Unauthorized access', 'danger')
      #  return redirect(url_for('home_bp.home'))

    item = storage.get(Item, item_id)
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('quality_checker_bp.list_items_for_qc'))

    claims = storage.filter(Claim, item_id=item.id)
    if not claims:
        flash('No claims found for this item', 'danger')
        return redirect(url_for('quality_checker_bp.list_items_for_qc'))

    
    return render_template('/v2/perform_qc.html', item=item, claims=claims)

@quality_checker_bp.route('/qc/match', methods=['POST'])
@login_required
def confirm_claim():
    """Confirm a claim and create a match"""
    if not current_user.has_role('quality_checker'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home_bp.home'))

    # call api endpoint for creating a match
    from app.apis.v2.matches_routes import create_match
    try:
        claim_id = request.form.get('claim_id')
        item_id = request.form.get('item_id')
        response, status_code = create_match(json.dumps({'claim_id': claim_id, 'item_id': item_id}), content_type='application/json')

        flash('Claim confirmed and match created', 'success')
        return redirect(url_for('quality_checker_bp.list_items_for_qc'))
    except Exception as e:
        flash('Failed to confirm claim', 'danger')
        return redirect(url_for('quality_checker_bp.list_items_for_qc')), status_code

@quality_checker_bp.route('/qc/claim/<int:claim_id>/reject', methods=['POST'])
@login_required
def reject_claim(claim_id):
    """Reject a claim"""
    if not current_user.has_role('quality_checker'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home_bp.home'))

    claim = storage.get(Claim, claim_id)
    if not claim:
        flash('Claim not found', 'danger')
        return redirect(url_for('quality_checker_bp.list_items_for_qc'))

    claim.status = 'rejected'
    storage.save()
    flash('Claim rejected', 'success')
    return redirect(url_for('quality_checker_bp.list_items_for_qc'))

@quality_checker_bp.route('/qc/item_ids', methods=['GET'])
@login_required
def get_qc_item_ids():
    """Return a list of item IDs that need quality checking
    
    This endpoint returns only the IDs of items that have pending claims,
    which can be used for navigation between items in the QC interface.
    """
    try:
        # Same query as list_items_for_qc but without pagination
        query = db.session.query(Item.id).join(Claim, Item.id == Claim.item_id).filter(
            Item.status == 'found', 
            Claim.status == 'pending'
        ).distinct()
        
        # Execute query and get all IDs as a list
        item_ids = [item_id for item_id, in query.all()]
        
        return jsonify({
            'item_ids': item_ids,
            'count': len(item_ids)
        }), 200
        
    except Exception as e:
        flash('Error fetching item IDs', 'danger')
        return jsonify({'error': str(e)}), 500

