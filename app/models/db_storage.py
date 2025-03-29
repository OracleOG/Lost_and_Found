# app/models/db_storage.py
from flask import current_app
from flask_sqlalchemy import SQLAlchemy, pagination
from app.models.base_model import BaseModel
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.models.item import Item
from app.models.claim import Claim

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class DBStorage:
    """Interacts with the database using Flask-SQLAlchemy"""
    def __init__(self, db):
        """Initialize with Flask-SQLAlchemy instance"""
        self.db = db

    def all(self, cls=None):
        """Query on the current database session"""
        new_dict = {}
        if cls:
            objs = self.db.session.query(cls).all()
            for obj in objs:
                key = f'{obj.__class__.__name__}.{obj.id}'
                new_dict[key] = obj
        else:
            for cls in self.db.Model.__subclasses__():
                if hasattr(cls, '__tablename__'):
                    objs = self.db.session.query(cls).all()
                    for obj in objs:
                        key = obj.__class__.__name__ + '.' + str(obj.id)
                        new_dict[key] = obj
        return new_dict

    def alli(self, cls=None):
        """Query on the current database session (alternative implementation)"""
        new_dict = {}
        if cls:
            objs = self.db.session.query(cls).all()
            for obj in objs:
                key = obj.__class__.__name__ + '.' + obj.id
                new_dict[key] = obj
        else:
            for cls in self.db.Model._decl_class_registry.values():
                if hasattr(cls, '__tablename__'):
                    objs = self.db.session.query(cls).all()
                    for obj in objs:
                        key = obj.__class__.__name__ + '.' + str(obj.id)
                        new_dict[key] = obj
        return new_dict
    
    def create(self,  cls, **kwargs):
        """create and save a new instance"""
        instance = cls(**kwargs)
        self.new(instance)
        self.save()
        return instance

    def new(self, obj):
        """Add the object to the current database session"""
        self.db.session.add(obj)

    def save(self):
        """Commit all changes of the current database session"""
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Database commit failed: {e}")
            raise

    def query(self, cls):
        """Return a query for the specified class"""
        return self.db.session.query(cls)

    def filter(self, cls, **kwargs):
        """Query with filters"""
        return self.db.session.query(cls).filter_by(**kwargs).all()

    def delete(self, obj=None):
        """Delete from the current database session obj if not None"""
        if obj is not None:
            try:
                self.db.session.delete(obj)
                self.db.session.commit()
            except SQLAlchemyError as e:
                self.db.session.rollback()
                logger.error(f"Delete failed: {e}")
                raise

    def get_items_with_claims(self):
        """Query for items with at least one claim"""
        return self.db.session.query(Item).filter(Item.claims.any()).all()

    def get(self, cls, id):
        """Get obj from DB by id"""
        return self.db.session.query(cls).get(id)

    def reload(self):
        """Reloads data from the database"""
        self.db.create_all()

    def paginate(self, cls, page=1, per_page=10, filters=None):
        """Paginate query results"""
        query = self.db.session.query(cls)
        if filters:
            query = query.filter_by(**filters)
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def paginate_query(self, query, page=1, per_page=10):
        """Paginate a custom SQLAlchemy query"""
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def to_dict(self, save_fs=None):
        """Returns a dictionary containing all keys/values of the instance"""
        new_dict = self.__dict__.copy()
        if "created_at" in new_dict:
            new_dict["created_at"] = new_dict["created_at"].strftime("%Y-%m-%dT%H:%M:%S")
        if "updated_at" in new_dict:
            new_dict["updated_at"] = new_dict["updated_at"].strftime("%Y-%m-%dT%H:%M:%S")
        new_dict["__class__"] = self.__class__.__name__
        if "_sa_instance_state" in new_dict:
            del new_dict["_sa_instance_state"]
        if save_fs is None:
            if "password" in new_dict:
                del new_dict["password"]
        return new_dict

    def close(self):
        """Call remove() method on the private session attribute"""
        self.db.session.remove()