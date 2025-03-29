from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from app.models.item import Item
from app.models.user import User
from app.models.claim import Claim
from app.utils.send_notification import send_email
from ..models.match import Match
from ..models.quality import QualityCheck
from app import db
from app.models.db_storage import DBStorage

quality_bp = Blueprint('quality_bp', __name__)
storage = DBStorage(db)

@quality_bp.route('/quality-list', methods=['GET'])
@login_required
def Q_list():
    return render_template('Q_checker_list.html')

@quality_bp.route('/quality-checker', methods=['GET'])
@login_required
def quality_checker():
    page = request.args.get('page', 1, type=int)
    per_page = 1

    # Get items sorted by the number of claims
    items_with_claims = db.session.query(Item, func.count(Match.id).label('claim_count'))\
        .join(Match, Item.id == Match.item_id)\
        .group_by(Item.id)\
        .order_by(func.count(Match.id).desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
        
    items = {item.id: item for item, _ in items_with_claims.items}
    matches = {
    item_id: Match.query.filter(
        item_id == item_id,
        Match.status.in_(['potential', 'pending'])
    ).all()
    for item_id in items.keys()
    }
    return render_template(
        'quality_checker.html',
        items=items,
        matches=matches,
        page=page,
        total_pages=items_with_claims.pages
    )

@quality_bp.route('/quality-checker2', methods=['GET'])
@login_required
def quality_checker2():
    # Fetch all matches and associated items
    matches = Match.query.all()
    items = {match.item_id: Item.query.get(match.item_id) for match in matches}

    return render_template('quality_checker copy.html', matches=matches, items=items)


@quality_bp.route('/quality-checker/<int:item_id>', methods=['GET'])
@login_required
def quality_checker3(item_id):
    # Fetch the item with the given item_id
    item = Item.query.get_or_404(item_id)
    
    # Fetch all matches for the item
    matches = Match.query.filter_by(item_id=item_id).all()
    
    # Extract claim_ids from matches
    claim_ids = [match.claim_id for match in matches]
    
    # Fetch all claims whose IDs are in the list of claim_ids
    claims = Claim.query.filter(Claim.id.in_(claim_ids)).all()
    
    # Create a list of matches with relevant attributes
    matches_data = [
        {
            'match_id': match.id,
            'claim_id': match.claim_id,
            'claim_description': next((claim.additional_information for claim in claims if claim.id == match.claim_id), None)
        }
        for match in matches
    ]
    
    return render_template('q_checker.html', item=item, claims=claims, matches=matches_data)