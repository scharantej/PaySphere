
# PayPal store Flask application

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import paypalrestsdk

# Configure the application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

# Define the Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    price = db.Column(db.Float)

# Define the Cart model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)

# Load the user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

# Products page
@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

# Product detail page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get(product_id)
    return render_template('product_detail.html', product=product)

# Cart page
@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Checkout page
@app.route('/checkout')
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum([item.quantity * item.product.price for item in cart_items])
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

# Payment page
@app.route('/payment', methods=['POST'])
@login_required
def payment():
    total_price = request.form['total_price']
    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {
            'payment_method': 'paypal'
        },
        'transactions': [{
            'amount': {
                'total': total_price,
                'currency': 'USD'
            }
        }]
    })
    if payment.create():
        for item in Cart.query.filter_by(user_id=current_user.id).all():
            item.delete()
        return redirect(url_for('confirmation'))
    else:
        flash('Payment failed')
        return redirect(url_for('checkout'))

# Confirmation page
@app.route('/confirmation')
@login_required
def confirmation():
    return render_template('confirmation.html')

# Run the application
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
