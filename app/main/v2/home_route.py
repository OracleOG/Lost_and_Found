from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.item import Item
from app.models.db_storage import DBStorage
from app.models.claim import Claim
from app.models.match import Match

home_bp = Blueprint('home_bp', __name__)
storage = DBStorage(db)

@home_bp.route('/home', methods=['GET'])
@login_required
def home():
    """Home page with newsfeed"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    items = storage.paginate(Item, page=page, per_page=per_page)
    item_categories = ['electronics', 'clothing', 'accessories', 'documents', 'miscellaneous']
    return render_template('/v2/index.html', items=items, item_categories=item_categories, title='Home')


# deprecated route
@home_bp.route('/item/<int:item_id>', methods=['GET'])
@login_required
def item_detail(item_id):
    """View item details"""
    item = storage.get(Item, item_id)
    if item.status == 'lost':
        flash('Item not found: wrong status', 'danger')
        return redirect(url_for('home_bp.home'))
    if item.status == 'resolved':
        flash('Item has been returned to owner', 'danger')
        return redirect(url_for('home_bp.home'))
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('home_bp.home'))
    return render_template('/vi/item_detail.html', item_id=item_id, title=item.item_name)