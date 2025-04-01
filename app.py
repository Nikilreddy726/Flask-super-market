from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import mysql.connector as connector
import os
import datetime
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
conn = connector.connect(host="localhost", user="root", passwd="Nikilreddy@317", database="AAmart")
cursor = conn.cursor()

# Ensure bills directory exists
if not os.path.exists('Bills'):
    os.makedirs('Bills')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/price_list')
def price_list():
    cursor.execute("SELECT * FROM items")
    data = cursor.fetchall()
    return render_template('price_list.html', items=data)

@app.route('/update_price', methods=['GET', 'POST'])
def update_price():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            item_name = request.form.get('item_name')
            price = request.form.get('price')
            if item_name and price:
                try:
                    query = "INSERT INTO items(ProductName, Price) VALUES(%s, %s)"
                    cursor.execute(query, (item_name.title(), price))
                    conn.commit()
                    flash(f"{item_name} with {price} Rs price is added!", 'success')
                except Exception as e:
                    flash(f"Error adding item: {str(e)}", 'danger')
        
        elif action == 'update':
            item_name = request.form.get('update_item_name')
            price = request.form.get('update_price')
            if item_name and price:
                try:
                    query = "UPDATE items SET Price = %s WHERE ProductName = %s"
                    cursor.execute(query, (price, item_name.title()))
                    conn.commit()
                    flash(f"Price of {item_name} updated to {price} Rs", 'success')
                except Exception as e:
                    flash(f"Error updating item: {str(e)}", 'danger')
        
        elif action == 'remove':
            item_name = request.form.get('remove_item_name')
            if item_name:
                try:
                    # Get current count before deletion
                    cursor.execute("SELECT COUNT(SNO) FROM items")
                    count = cursor.fetchone()[0]
                    
                    query = "DELETE FROM items WHERE ProductName = %s"
                    cursor.execute(query, (item_name.title(),))
                    conn.commit()
                    
                    # Reset auto increment
                    query2 = "ALTER TABLE items AUTO_INCREMENT = %s"
                    cursor.execute(query2, (count,))
                    conn.commit()
                    
                    flash(f"{item_name} removed from price list!", 'success')
                except Exception as e:
                    flash(f"Error removing item: {str(e)}", 'danger')
        
        return redirect(url_for('update_price'))
    
    cursor.execute("SELECT * FROM items")
    data = cursor.fetchall()
    return render_template('update_price.html', items=data)

@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        if 'generate_bill' in request.form:
            customer_name = request.form.get('customer_name')
            phone = request.form.get('phone')
            
            if len(phone) != 10 or not phone.isdigit():
                flash("Mobile number should be exactly 10 digits", 'danger')
                return redirect(url_for('create_bill'))
            
            # Process the bill items
            items = []
            total = 0
            i = 0
            while True:
                product_name = request.form.get(f'product_name_{i}')
                if not product_name:
                    break
                quantity = float(request.form.get(f'quantity_{i}', 0))
                
                # Get price from database
                cursor.execute("SELECT Price FROM items WHERE ProductName = %s", (product_name.title(),))
                result = cursor.fetchone()
                if result:
                    price = result[0]
                    item_total = price * quantity
                    items.append({
                        'name': product_name,
                        'quantity': quantity,
                        'price': price,
                        'total': item_total
                    })
                    total += item_total
                i += 1
            
            if not items:
                flash("No items added to the bill", 'danger')
                return redirect(url_for('create_bill'))
            
            # Generate bill content
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            bill_no = random.randint(2112, 18325)
            
            bill_content = f"Customer Name   : {customer_name}\n"
            bill_content += f"Phone Number    : {phone}\n"
            bill_content += f"Purchase Time   : {current_time}\n"
            bill_content += f"Bill Number     : {bill_no}\n"
            bill_content += "="*80 + "\n"
            bill_content += f"\t\tProduct Name\t\tQuantity(kgs)\t\tPrice\n"
            bill_content += "="*80 + "\n"
            
            for item in items:
                bill_content += f"\t\t{item['name']}\t\t\t{item['quantity']}\t\t\t{item['total']} Rs\n"
            
            bill_content += "\n\n" + "="*80 + "\n"
            bill_content += f"\t\t\t\t      Total : {total} Rs\n"
            bill_content += "="*80 + "\n"
            bill_content += "\n\n\t\t\t\tThanks For Visiting Us !!"
            
            # Save bill to file
            filename = secure_filename(f"{bill_no}.txt")
            filepath = os.path.join('Bills', filename)
            with open(filepath, 'w') as f:
                f.write(bill_content)
            
            return render_template('bill_preview.html', 
                                 bill_content=bill_content.split('\n'),
                                 bill_no=bill_no,
                                 customer_name=customer_name,
                                 phone=phone,
                                 current_time=current_time,
                                 total=total)
    
    cursor.execute("SELECT ProductName FROM items")
    products = [item[0] for item in cursor.fetchall()]
    return render_template('create_bill.html', products=products)

@app.route('/download_bill/<bill_no>')
def download_bill(bill_no):
    filename = secure_filename(f"{bill_no}.txt")
    return send_from_directory('Bills', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)