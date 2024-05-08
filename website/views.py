from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json, uuid

views = Blueprint('views', __name__)

from flask import request

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        amount = int(request.form.get('amount'))
        income_checkbox = request.form.get('type') == 'income'  # Check if 'Income' checkbox is selected
        expense_checkbox = request.form.get('type') == 'expense'  # Check if 'Expense' checkbox is selected
        comment = request.form.get('comment')

        if amount < 0:
            flash('Amount cannot be negative!', category='error')
        elif not (income_checkbox or expense_checkbox):
            flash('Please select at least one type (Income or Expense)!', category='error')
        else:
            # Determine the type based on the selected checkboxes
            if income_checkbox:
                type = 'income'
            else:
                type = 'expense'

            new_note = Note(user_id=current_user.id, amount=amount, type=type, comment=comment)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})
