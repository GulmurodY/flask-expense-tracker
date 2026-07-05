from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

CURRENCIES = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'SAR': 'SR ',
    'AED': 'AED ',
    'RUB': '₽',
    'TJS': 'ЅМ ',
    'UZS': 'UZS ',
    'KZT': '₸',
    'CNY': '¥',
    'JPY': '¥',
    'INR': '₹',
    'TRY': '₺',
}

CATEGORIES = [
    "Food",
    "Transport",
    "Housing",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Salary",
    "Other",
]


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, default=0)
    type = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(150), default="Other")
    comment = db.Column(db.String(1500), default="No comment")
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    currency = db.Column(db.String(10), default='USD')
    notes = db.relationship('Note')
