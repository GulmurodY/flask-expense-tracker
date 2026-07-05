from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect
from flask_login import login_required, current_user
from sqlalchemy import func
from collections import defaultdict
from datetime import datetime, time, date
from .models import Note, CATEGORIES
from . import db
import json, uuid
import io
import re
import pandas as pd


def _parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _filtered_notes():
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))
    query = Note.query.filter_by(user_id=current_user.id)
    if start:
        query = query.filter(Note.date >= datetime.combine(start, time.min))
    if end:
        query = query.filter(Note.date <= datetime.combine(end, time.max))
    return query.order_by(Note.id).all()

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    today = date.today()
    current_date = request.form.get('date') if request.method == 'POST' else today.strftime('%Y-%m-%d')
    if not current_date:
        current_date = today.strftime('%Y-%m-%d')

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except (TypeError, ValueError):
            amount = None

        transaction_date = _parse_date(request.form.get('date'))

        income_checkbox = request.form.get('type') == 'income'  
        expense_checkbox = request.form.get('type') == 'expense'  
        comment = request.form.get('comment')
        category = request.form.get('category')
        if category not in CATEGORIES:
            category = 'Other'

        if amount is None:
            flash('Please enter a valid number for the amount!', category='error')
        elif amount < 0:
            flash('Amount cannot be negative!', category='error')
        elif request.form.get('date') and transaction_date is None:
            flash('Please enter a valid transaction date!', category='error')
        elif transaction_date and transaction_date > today:
            flash('Transaction date cannot be in the future!', category='error')
        elif not (income_checkbox or expense_checkbox):
            flash('Please select at least one type (Income or Expense)!', category='error')
        else:
            if income_checkbox:
                type = 'income'
            else:
                type = 'expense'

            stored_date = transaction_date or today

            new_note = Note(user_id=current_user.id, amount=amount, type=type,
                            comment=comment, category=category,
                            date=datetime.combine(stored_date, time.min))
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    notes = _filtered_notes()

    income_total = sum(n.amount for n in notes if n.type == 'income')
    expense_total = sum(n.amount for n in notes if n.type == 'expense')

    by_category = defaultdict(lambda: {'total': 0.0, 'count': 0})
    for n in notes:
        if n.type == 'expense':
            key = n.category or 'Other'
            by_category[key]['total'] += n.amount
            by_category[key]['count'] += 1

    category_stats = sorted(({
        'category': cat,
        'total': v['total'],
        'count': v['count'],
        'percent': (v['total'] / expense_total * 100) if expense_total else 0,
    } for cat, v in by_category.items()), key=lambda s: s['total'], reverse=True)

    return render_template("home.html", user=current_user,
                           notes=notes,
                           categories=CATEGORIES,
                           category_stats=category_stats,
                           income_total=income_total,
                           expense_total=expense_total,
                           current_date=current_date,
                           today_date=today.strftime('%Y-%m-%d'),
                           start=request.args.get('start', ''),
                           end=request.args.get('end', ''))


@views.route('/dashboard')
@login_required
def dashboard():
    notes = Note.query.filter_by(user_id=current_user.id).all()

    by_category = defaultdict(float)
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    income_total = 0.0
    expense_total = 0.0

    for n in notes:
        month = n.date.strftime('%Y-%m') if n.date else 'Unknown'
        if n.type == 'income':
            monthly_income[month] += n.amount
            income_total += n.amount
        else:
            by_category[n.category or 'Other'] += n.amount
            monthly_expense[month] += n.amount
            expense_total += n.amount

    cat_sorted = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
    category_labels = [c for c, _ in cat_sorted]
    category_values = [round(v, 2) for _, v in cat_sorted]

    months = sorted(set(list(monthly_income) + list(monthly_expense)))
    income_series = [round(monthly_income[m], 2) for m in months]
    expense_series = [round(monthly_expense[m], 2) for m in months]

    balance = income_total - expense_total
    savings_rate = (balance / income_total * 100) if income_total else 0
    top_category = category_labels[0] if category_labels else '—'
    expense_count = sum(1 for n in notes if n.type == 'expense')
    avg_expense = (expense_total / expense_count) if expense_count else 0

    chart_data = {
        'category_labels': category_labels,
        'category_values': category_values,
        'months': months,
        'income_series': income_series,
        'expense_series': expense_series,
    }

    stats = {
        'income_total': income_total,
        'expense_total': expense_total,
        'balance': balance,
        'savings_rate': savings_rate,
        'top_category': top_category,
        'avg_expense': avg_expense,
        'transactions': len(notes),
    }

    return render_template("dashboard.html", user=current_user,
                           chart_data=chart_data, stats=stats)


@views.route('/export')
@login_required
def export():
    today = date.today()
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    start = _parse_date(start_raw)
    end = _parse_date(end_raw)

    if (start_raw and start is None) or (end_raw and end is None):
        flash('Please enter valid export dates!', category='error')
        return redirect('/')
    if (start and start > today) or (end and end > today):
        flash('Export dates cannot be in the future!', category='error')
        return redirect('/')

    notes = _filtered_notes()

    columns = ['date', 'type', 'category', 'amount', 'currency', 'comment']
    df = pd.DataFrame([{
        'date': n.date.strftime('%Y-%m-%d') if n.date else '',
        'type': n.type,
        'category': n.category or 'Other',
        'amount': n.amount,
        'currency': current_user.currency or 'USD',
        'comment': n.comment or '',
    } for n in notes], columns=columns)

    raw = (request.args.get('filename') or '').strip()
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', raw).strip('._')
    name = re.sub(r'\.(csv|xlsx)$', '', name, flags=re.IGNORECASE).strip('._') or 'transactions'

    buf = io.BytesIO()
    if request.args.get('format') == 'xlsx':
        df.to_excel(buf, index=False, sheet_name='Transactions')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        download_name = f'{name}.xlsx'
    else:
        buf.write(df.to_csv(index=False).encode('utf-8'))
        mimetype = 'text/csv'
        download_name = f'{name}.csv'
    buf.seek(0)

    return send_file(buf, as_attachment=True,
                     download_name=download_name, mimetype=mimetype)


@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})
