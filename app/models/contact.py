from app import db
from app.models.base_model import BaseModel


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    address = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=True, default='pending')

        
    def __repr__(self):
        return 'Contact: [id: {}, name: {}, address: {}]'.format(self.id, self.name, self.address)
