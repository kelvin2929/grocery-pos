from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

INVENTORY_FILE = 'inventory.json'
TRANSACTION_FILE = 'transactions.json'

def load_inventory():
    with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_inventory(inventory):
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)

def save_transaction(transaction):
    if not os.path.exists(TRANSACTION_FILE):
        transactions = []
    else:
        with open(TRANSACTION_FILE, 'r', encoding='utf-8') as f:
            transactions = json.load(f)
    total = sum(item['price'] * item['quantity'] for item in transaction['cart'].values())
    transaction['total'] = total
    transaction['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    transactions.append(transaction)
    with open(TRANSACTION_FILE, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    inventory = load_inventory()
    cart = session.get('cart', {})
    language = session.get('lang', 'en')
    query = request.args.get('q', '').strip().lower()
    if query:
        inventory = [
            item for item in inventory
            if query in item['name_en'].lower() or query in item['name_th'].lower()
        ]

    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('index.html', inventory=inventory, cart=cart, total=total, lang=language)
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('index.html', inventory=inventory, cart=cart, total=total, lang=language)

@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    inventory = load_inventory()
    product = next((item for item in inventory if item['id'] == product_id), None)
    if not product or product['stock'] <= 0:
        return redirect(url_for('index'))
    cart = session.get('cart', {})
    if product_id in cart:
        if cart[product_id]['quantity'] < product['stock']:
            cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name_en': product['name_en'],
            'name_th': product['name_th'],
            'price': product['price'],
            'quantity': 1
        }
    session['cart'] = cart
    return redirect(url_for('index'))

@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('index'))
    inventory = load_inventory()
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    for product_id, item in cart.items():
        product = next((p for p in inventory if p['id'] == product_id), None)
        if product:
            product['stock'] -= item['quantity']



    save_inventory(inventory)
    save_transaction({'cart': cart, 'total': total})
    session['cart'] = {}
    return render_template('checkout_success.html', total=total, lang=session.get('lang', 'en'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'th']:
        session['lang'] = lang
    return redirect(url_for('index'))

@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    inventory = load_inventory()
    language = session.get('lang', 'en')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update':
            for item in inventory:
                item_id = item['id']
                item['name_en'] = request.form.get(f'name_en_{item_id}')
                item['name_th'] = request.form.get(f'name_th_{item_id}')
                item['price'] = float(request.form.get(f'price_{item_id}'))
                item['stock'] = int(request.form.get(f'stock_{item_id}'))
        elif action == 'add':
            new_item = {
                'id': request.form['new_id'],
                'name_en': request.form['new_name_en'],
                'name_th': request.form['new_name_th'],
                'price': float(request.form['new_price']),
                'stock': int(request.form['new_stock'])
            }
            inventory.append(new_item)
        elif action.startswith('delete_'):
            delete_id = action.replace('delete_', '')
            inventory = [item for item in inventory if item['id'] != delete_id]

        save_inventory(inventory)
        return redirect(url_for('manage_inventory'))

    return render_template('manage_inventory.html', inventory=inventory, lang=language)

@app.route('/sales_records')
def sales_records():
    if not os.path.exists(TRANSACTION_FILE):
        transactions = []
    else:
        with open(TRANSACTION_FILE, 'r', encoding='utf-8') as f:
            transactions = json.load(f)
    language = session.get('lang', 'en')
    return render_template('sales_records.html', transactions=transactions, lang=language)


if __name__ == '__main__':
    app.run(debug=True)
