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


def _filtered_query():
    start = _parse_date(request.args.get('start'))
    end = _parse_date(request.args.get('end'))
    query = Note.query.filter_by(user_id=current_user.id)
    if start:
        query = query.filter(Note.date >= datetime.combine(start, time.min))
    if end:
        query = query.filter(Note.date <= datetime.combine(end, time.max))
    return query


def _filtered_notes():
    return _filtered_query().order_by(Note.id).all()

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

        types = request.form.getlist('type')
        income_checkbox = types == ['income']
        expense_checkbox = types == ['expense']
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
            flash('Please select exactly one type (Income or Expense)!', category='error')
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

    all_notes = _filtered_notes()

    income_total = sum(n.amount for n in all_notes if n.type == 'income')
    expense_total = sum(n.amount for n in all_notes if n.type == 'expense')

    page = request.args.get('page', 1, type=int)
    pagination = _filtered_query().order_by(Note.id.desc()) \
        .paginate(page=page, per_page=10, error_out=False)

    return render_template("home.html", user=current_user,
                           notes=pagination.items,
                           page=pagination.page,
                           pages=pagination.pages,
                           has_prev=pagination.has_prev,
                           has_next=pagination.has_next,
                           offset=(pagination.page - 1) * pagination.per_page,
                           total=pagination.total,
                           categories=CATEGORIES,
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
    category_counts = defaultdict(int)
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
            key = n.category or 'Other'
            by_category[key] += n.amount
            category_counts[key] += 1
            monthly_expense[month] += n.amount
            expense_total += n.amount

    cat_sorted = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
    category_labels = [c for c, _ in cat_sorted]
    category_values = [round(v, 2) for _, v in cat_sorted]

    category_stats = [{
        'category': cat,
        'total': total,
        'count': category_counts[cat],
        'percent': (total / expense_total * 100) if expense_total else 0,
    } for cat, total in cat_sorted]

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
                           chart_data=chart_data, stats=stats,
                           category_stats=category_stats)


@views.route('/export')
@login_required
def export():
    today = date.today()
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    start = _parse_date(start_raw)
    end = _parse_date(end_raw)

    default_name = f'transactions_{today.strftime("%Y-%m-%d")}'

    if 'format' not in request.args:
        return render_template("export.html", user=current_user,
                               start=start_raw or '', end=end_raw or '',
                               default_name=default_name)

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
    name = re.sub(r'\.(csv|xlsx)$', '', name, flags=re.IGNORECASE).strip('._') or default_name

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


@views.route('/import', methods=['GET', 'POST'])
@login_required
def import_transactions():
    if request.method == 'GET':
        return render_template("import.html", user=current_user)

    file = request.files.get('file')
    if file is None or not file.filename:
        flash('Please choose a file to import!', category='error')
        return redirect('/')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    try:
        if ext == 'xlsx':
            df = pd.read_excel(file)
        elif ext == 'csv':
            df = pd.read_csv(file)
        else:
            flash('Unsupported file type — please upload a .csv or .xlsx file!', category='error')
            return redirect('/')
    except Exception:
        flash('Could not read the file — make sure it is a valid CSV or Excel file!', category='error')
        return redirect('/')

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in ('amount', 'type') if c not in df.columns]
    if missing:
        flash(f'Missing required column(s): {", ".join(missing)}!', category='error')
        return redirect('/')

    today = date.today()
    category_lookup = {c.lower(): c for c in CATEGORIES}
    imported = 0
    errors = []

    for i, row in df.iterrows():
        rownum = i + 2  # +1 for the header row, +1 for 1-based numbering

        try:
            amount = float(row['amount'])
        except (TypeError, ValueError):
            amount = None
        if amount is None or pd.isna(amount):
            errors.append(f'row {rownum}: invalid amount')
            continue
        if amount < 0:
            errors.append(f'row {rownum}: negative amount')
            continue

        type = str(row['type']).strip().lower()
        if type not in ('income', 'expense'):
            errors.append(f'row {rownum}: type must be income or expense')
            continue

        raw_date = row.get('date')
        if raw_date is None or pd.isna(raw_date) or str(raw_date).strip() == '':
            transaction_date = today
        elif isinstance(raw_date, datetime):
            transaction_date = raw_date.date()
        else:
            transaction_date = _parse_date(str(raw_date).strip())
        if transaction_date is None:
            errors.append(f'row {rownum}: invalid date (use YYYY-MM-DD)')
            continue
        if transaction_date > today:
            errors.append(f'row {rownum}: date is in the future')
            continue

        raw_category = row.get('category')
        if raw_category is None or pd.isna(raw_category):
            category = 'Other'
        else:
            category = category_lookup.get(str(raw_category).strip().lower(), 'Other')

        raw_comment = row.get('comment')
        comment = '' if raw_comment is None or pd.isna(raw_comment) else str(raw_comment)

        new_note = Note(user_id=current_user.id, amount=amount, type=type,
                        comment=comment, category=category,
                        date=datetime.combine(transaction_date, time.min))
        db.session.add(new_note)
        imported += 1

    if imported:
        db.session.commit()
        flash(f'Imported {imported} transaction(s)!', category='success')
    if errors:
        shown = '; '.join(errors[:3])
        more = f' (+{len(errors) - 3} more)' if len(errors) > 3 else ''
        flash(f'Skipped {len(errors)} row(s): {shown}{more}', category='error')
    if not imported and not errors:
        flash('The file has no rows to import!', category='error')

    return redirect('/')


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
