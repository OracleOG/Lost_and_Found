from app import db
from app.models.base_model import BaseModel
from fuzzywuzzy import fuzz


class Item(BaseModel):
    """Represents lost or found items"""
    __tablename__ = 'items'
    item_name = db.Column(db.String(80), nullable=False)
    item_category = db.Column(db.String(50), nullable=False)
    item_color = db.Column(db.String(50), nullable=False)
    item_brand = db.Column(db.String(50), nullable=True)
    date_lost_found = db.Column(db.DateTime, nullable=True)
    location_lost_found = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    proof_image_url = db.Column(db.String(255), nullable=True)  # For receipts, etc.
    serial_number = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Enum('lost', 'found', 'claimed', 'resolved', name='item_status'), 
                       nullable=False, default='lost')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='items')
    claims = db.relationship('Claim', back_populates='item')
    matches = db.relationship('Match', back_populates='item')
    warehouse_status = db.Column(db.Enum('received', 'not_received', 'on_delivery',  name='warehouse_status'),
                                 nullable=True, default='not_received')

    def find_match(self):
        """Check for an exact match amoung 'found' items"""
        if self.status != 'lost':
            return None
        return db.session.query(Item).filter(
            Item.status =='found', 
            Item.item_category == self.item_category, 
            Item.serial_number == self.serial_number
        ).first()
    

    def find_related_items(self):
        """Find potential matches among 'found' items
        
            Algorithm:: Weighted Property Matching

            Logic:
                Compare multiple properties (item_name, item_category, location_lost_found, item_color, description) and assign weights to each.
                Use fuzzy string matching (e.g., with fuzzywuzzy) for fields like item_name and description.
                Rank items based on a cumulative score and return those above a threshold.

            steps:
                Query all found items.

                For each found item, calculate a similarity score:
                item_name: Fuzzy match (weight: 30%).
                item_category: Exact match (weight: 20%).
                location_lost_found: Fuzzy match (weight: 20%).
                item_color: Exact match (weight: 15%).
                description: Fuzzy match (weight: 15%).

            Return:
                list of items with a score above a threshold (e.g., 60%).
        """
        if self.status != 'lost':
            return []
        
        # Query all found items with the same category
        found_items = db.session.query(Item).filter(
                Item.status =='found',
            Item.item_category == self.item_category
        ).all()

        # Define weights for each property
        weights = {
            'item_name': 0.3,
            'item_category': 0.2,
            'location_lost_found': 0.2,
            'item_color': 0.15,
            'description': 0.15,
            'category': 0.2
        }

        threshold = 0.6  # Minimum score for a match

        potential_matches = []

        for item in found_items:
            score = 0

            # Calculate score for each property

            score += weights['category'] * 1.0

            # Fuzzy match for item_name
            name_similarity = fuzz.token_sort_ratio(self.item_name.lower(), item.item_name.lower()) / 100.0
            score += weights['item_name'] * name_similarity

            # fuzzy match for location_lost_found
            location_similarities = fuzz.token_sort_ratio(self.location_lost_found.lower(), item.location_lost_found.lower()) / 100.0
            score += weights['location_lost_found'] * location_similarities

            # match for item_color
            color_similarity = 1.0 if self.item_color.lower() == item.item_color.lower() else 0.0
            score += weights['item_color'] * color_similarity

            # fuzzy match for description
            description_similarity = fuzz.token_sort_ratio(self.description.lower(), item.description.lower()) / 100.0
            score += weights['description'] * description_similarity

            if score >= threshold:
                potential_matches.append((item, score))
            
        # Sort by score in descending order
        potential_matches.sort(key=lambda x: x[1], reverse=True)
        return potential_matches[:5]  # Return top 5 matches

