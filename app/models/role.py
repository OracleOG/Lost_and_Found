from app import db
from app.models.base_model import BaseModel


class Role(BaseModel):
    """Defines user roles (e.g., user, quality checker)"""
    __tablename__ = 'roles'
    name = db.Column(db.String(50), unique=True, nullable=False)
   
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"