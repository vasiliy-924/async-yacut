from datetime import datetime

from yacut import db


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(256), nullable=False)
    short = db.Column(db.String(128), nullable=False)
    timestamp = db.Column(db.Datetime, index=True, default=datetime.utcnow)

    def to_dict(mapping):
        return dict(
            id = mapping.id,
            original = mapping.original,
            short = mapping.short,
            timestamp = mapping.short
        )
    
    def from_dict(self, data):
        for field in ['original', 'short', 'timestamp']:
            if field in data:
                settatr(self, field, data[field])