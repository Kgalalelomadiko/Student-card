import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-change-in-production")

# In-memory storage for transactions (will reset when server restarts)
transactions = []

# Predefined categories
CATEGORIES = [
    'Food & Dining',
    'Transportation',
    'Utilities',
    'Entertainment',
    'Healthcare',
    'Shopping',
    'Travel',
    'Education',
    'Salary',
    'Freelance',
    'Investment',
    'Gift',
    'Other'
]

@app.route('/')
def index():
    """Dashboard view showing budget summary and recent transactions"""
    # Calculate totals
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = total_income - total_expenses
    
    # Get recent transactions (last 5)
    recent_transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)[:5]
    
    return render_template('index.html', 
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance,
                         recent_transactions=recent_transactions)

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    """Add new income or expense transaction"""
    if request.method == 'POST':
        # Get form data
        transaction_type = request.form.get('type')
        description = request.form.get('description', '').strip()
        amount = request.form.get('amount')
        category = request.form.get('category')
        date = request.form.get('date')
        
        # Validate form data
        if not all([transaction_type, description, amount, category, date]):
            flash('All fields are required.', 'error')
            return redirect(url_for('add_transaction'))
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0.', 'error')
                return redirect(url_for('add_transaction'))
        except ValueError:
            flash('Invalid amount. Please enter a valid number.', 'error')
            return redirect(url_for('add_transaction'))
        
        if transaction_type not in ['income', 'expense']:
            flash('Invalid transaction type.', 'error')
            return redirect(url_for('add_transaction'))
        
        if category not in CATEGORIES:
            flash('Invalid category.', 'error')
            return redirect(url_for('add_transaction'))
        
        # Create transaction
        transaction = {
            'id': len(transactions) + 1,
            'type': transaction_type,
            'description': description,
            'amount': round(amount, 2),
            'category': category,
            'date': date,
            'created_at': datetime.now()
        }
        
        transactions.append(transaction)
        flash(f'{transaction_type.capitalize()} of ${amount:.2f} added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_transaction.html', categories=CATEGORIES)

@app.route('/history')
def history():
    """View all transactions with filtering options"""
    # Get filter parameters
    category_filter = request.args.get('category', 'all')
    type_filter = request.args.get('type', 'all')
    
    # Filter transactions
    filtered_transactions = transactions.copy()
    
    if category_filter != 'all':
        filtered_transactions = [t for t in filtered_transactions if t['category'] == category_filter]
    
    if type_filter != 'all':
        filtered_transactions = [t for t in filtered_transactions if t['type'] == type_filter]
    
    # Sort by date (most recent first)
    filtered_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('history.html', 
                         transactions=filtered_transactions,
                         categories=CATEGORIES,
                         selected_category=category_filter,
                         selected_type=type_filter)

@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    """Delete a transaction"""
    global transactions
    
    # Find and remove transaction
    transactions = [t for t in transactions if t['id'] != transaction_id]
    flash('Transaction deleted successfully!', 'success')
    
    # Redirect back to the referring page or history
    return redirect(request.referrer or url_for('history'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('base.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('base.html', error_message="Internal server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
