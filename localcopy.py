from cgitb import html
from itertools import product
from unicodedata import decimal
from unittest import result
import MySQLdb
from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, session, flash, logging
from flask_mysqldb import MySQL
from datetime import datetime
import hashlib
from validate_email import validate_email
import barcode
from barcode.writer import ImageWriter
import string    
import random
import os 
import cv2 
from pyzbar.pyzbar import decode
import time

 
# datetime object containing current date and time (used for entering the date of entered products etc.)
now = datetime.now()
# dd/mm/YY H:M:S
#variable that will be called later
datetime = now.strftime("%d/%m/%Y")


app = Flask(__name__)

mysql = MySQL(app)

app.secret_key = 'thisisthesecretkey'

#database setup

app.config['MYSQL_HOST'] = 'inventorydatabase.cshck0entwnq.us-west-2.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'inventory001'
app.config['MYSQL_DB'] = 'inventorydatabase'

#barcodees
def generate_barcode_string():
    #generate a random 13 digit string for barcode
    barcode_string = ''.join(random.choice(string.digits) for i in range(13))
    EAN = barcode.get_barcode_class('ean13')
    barcode_barcode = str(EAN(barcode_string))
    print(barcode_barcode)
    return barcode_barcode
    
def generate_barcode(product_barcode, generate_barcode_name):
    path = os.path.dirname(os.path.realpath(__file__)) + "\\static\\barcodes\\" + generate_barcode_name
    EAN = barcode.get_barcode_class('ean13')
    render_barcode = EAN(product_barcode, writer=ImageWriter())
    render_barcode.save(path)

def generate_barcode_name(product_barcode, product_name):
    product_barcode_name = product_name + "_" + product_barcode
    return product_barcode_name

#check if the user is logged in (checks if loggedin is in session which is a dictionary created when the user logs in)
def is_loggin_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "loggedin" in session:
            return f(*args, **kwargs)
        else:
            return redirect("/login")
    return wrap

#default route
@app.route("/")
@is_loggin_in
def default():
    return redirect("/dashboard")

    
# login page    
@app.route("/login", methods=["POST","GET"])
def login():
    msg = ""
    if request.method == "POST":
        user_details = request.form
        username = user_details['usernameInput']
        password = user_details['passwordInput']

        #turn string password into a hashed password to compare with database
        hash_obj = hashlib.md5(password.encode())
        hashed_password = hash_obj.hexdigest()

        #open database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM usertable WHERE username = %s AND password = %s', (username, hashed_password,))
        account = cur.fetchone()

         # If account exists in accounts table in database
        if account:
             # Create session data, we can access this data in other routes
            session['loggedin'] = True  
            session['id'] = account['userID']
            session['username'] = account['username']
            # Redirect to home page
            return redirect("/dashboard")
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('Login-Page.html', msg=msg)



#signup page
@app.route("/signup", methods=["POST","GET"])
def signup():
    #using this to display error message to user later
    error_message = ""
    msg = ""
    if request.method == "POST":

        #signup details
        signup_info = request.form
        username = signup_info["signupUsername"]
        userpassword = signup_info["signupPassword"]
        userconfirmpassword = signup_info["signupConfirmPassword"]
        useremailaddress = signup_info["signupEmailAddress"]
       
        #check user emailaddress
        if validate_email(useremailaddress) == False:
            error_message = "that email address is invalid!"
            return render_template("sign-up.html", error_message = error_message)

        #check if username exists in database currently
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usertable WHERE username = %s", [username])
        check_user = cur.fetchall()
        if check_user:
            error_message = "that username exists already!"
            return render_template("sign-up.html", error_message = error_message)

        #check if email exists in database currently
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM usertable WHERE emailaddress = %s", [useremailaddress])
        check_email = cur2.fetchall()
        if check_email:
            error_message = "that email exists already!"
            return render_template("sign-up.html", error_message = error_message)

        #check if user password match
        if userpassword == userconfirmpassword:
            #hash password
            hash_obj = hashlib.md5(userpassword.encode())
            hashed_password = hash_obj.hexdigest()

            #insert hashed password into database
            cur3 = mysql.connection.cursor()
            cur3.execute("INSERT into usertable (username, password, emailaddress) VALUES(%s, %s, %s) ", (username, hashed_password, useremailaddress))
            mysql.connection.commit()
            msg = "Sucsessfully Created Login!"
            return render_template('Login-Page.html', msg=msg)
        else: 
            error_message = "passwords do not match!"
            return render_template("sign-up.html", error_message = error_message)
    else:
        return render_template("sign-up.html")


#dashboard
@app.route("/dashboard")
@is_loggin_in
def dashboard():
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute("SELECT saleName, salePrice, saleQuantity, datetime, productID FROM sales WHERE username = %s", [username])
    salesrows = cur.fetchall()

    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT name, price, quantity, description, productID FROM products WHERE username = %s", [username])
    productrows = cur2.fetchall()
    

    cur3 = mysql.connection.cursor()
    totalsales = cur3.execute("SELECT * FROM sales WHERE username = %s", [username])

    cur4 = mysql.connection.cursor()
    cur4.execute("SELECT SUM(linetotal) FROM sales WHERE username = %s", [username])
    totalsalesprice = cur4.fetchone()[0]
    totalsalesprice = str(totalsalesprice)
    if totalsalesprice == "None":
        totalsalesprice = 0

    cur5 = mysql.connection.cursor()
    cur5.execute("SELECT * FROM products WHERE username = %s", [username])
    productrows2 = cur5.fetchall()


    

    return render_template("main-menu.html", salesrows=salesrows, productrows=productrows, totalsales=totalsales, totalsalesprice=totalsalesprice, productrows2=productrows2)


#product page
@app.route("/products", methods=["POST","GET"])
@is_loggin_in
def products():
        username = session["username"]
        #Grab Product list and send  to the product table in the html
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, price, quantity, description, productID FROM products WHERE username = %s", [username])
        productrows = cur.fetchall()
        return render_template("products.html", productrows=productrows)

@app.route("/addproducts", methods=["POST","GET"])
@is_loggin_in
def add_products():
    #if user posts the add product form add products to database
    if request.method =="POST":
        product_details = request.form
        pname = product_details["product-name"]
        pprice = product_details["product-price"]
        pquantity = product_details["product-quanitity"]
        pdescription = product_details["product-description"]
        user = session["username"]

        #create a random 13 digit barcode
        barcode = generate_barcode_string()
        print(barcode)
        barcode_name = generate_barcode_name(barcode, pname)
        print(barcode_name)
        generate_barcode(barcode, barcode_name)
        barcodeURL =  "\\static\\barcodes\\" + "{}".format(barcode_name) + ".png"
        barcodeURLFIXED = barcodeURL.replace("\\", "/")
        print(barcodeURLFIXED)
        cur = mysql.connection.cursor()
        cur.execute("INSERT into products(name, price, quantity, description, username, datetime, updatetime, barcode, barcode_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", [pname, pprice, pquantity, pdescription, user, datetime, datetime, barcode, barcodeURLFIXED])
        mysql.connection.commit()
      
        #prevent modal form resubmission of data
        return redirect("/products")

#add products ajax
@app.route("/ajaxaddproducts", methods=["POST", "GET"])
@is_loggin_in
def ajaxaddproducts():
    return render_template("product-add.html", locations = locations)

#view products ajax (shows detals of produt and allows users to edit them thorugh bootstrap model)
@app.route("/ajaxViewProduct",methods=["POST","GET"])
@is_loggin_in
def ajaxViewproduct():
    if request.method == 'POST':
        #grab product details
        productid = request.form['productid']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products WHERE productID = %s", [productid])
        viewProductList = cur.fetchall() 

        #grab barcode url to display image
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM products WHERE productID = %s", [productid])
        barcodefetch = cur2.fetchall() 
        for row in barcodefetch:
            barcodeURL = row[9]
    return jsonify({'htmlresponse': render_template('product-view.html',viewProductList=viewProductList, barcodeURL=barcodeURL)})

#Edit or remove items into the database from the modal form
@app.route('/ajaxUpdateProduct', methods=['POST','GET'])
def update_view_item():
    if request.method == 'POST':
        #open database
        cur = mysql.connection.cursor()
        #if the delete button is pressed delete the data entry
        if request.form.get("deleteButton"):
            productid = request.form['productId']
            cur.execute ("DELETE from products WHERE productID = %s", [productid])
            mysql.connection.commit()
            cur.close()
            return redirect("/products")
       

        #elif
        elif request.form.get("view_barcode"):
            productid = request.form['productId']
            cur.execute("SELECT * from products WHERE productID = %s", [productid])
            barcodefetch = cur.fetchall()
            for row in barcodefetch:
                barcodeURL = row[9]
            return render_template("view-barcode.html", barcodeURL=barcodeURL)
 #else update the data with the user's new data
        else:
              #fetch form data
            product_details = request.form
            productid =  product_details['productId']
            name = product_details['product-name']
            description = product_details['product-description']
            quantity = product_details['product-quantity']
            price = product_details["product-price"]
            barcode = product_details["product-barcode"]
            new_barcode_name = generate_barcode_name(name, barcode)
            generate_barcode(barcode, new_barcode_name)
            barcodeURL =  "\\static\\barcodes\\" + "{}".format(new_barcode_name) + ".png"
            barcodeURLFIXED = barcodeURL.replace("\\", "/")
            cur = mysql.connection.cursor()
            cur.execute("UPDATE products SET name=%s, price=%s, quantity=%s, description=%s, updatetime =%s, barcode=%s, barcode_url=%s WHERE productID=%s",[name, price, quantity, description, datetime, barcode, barcodeURLFIXED, productid])
            mysql.connection.commit()
            cur.close()
            return redirect("/products")

#Sales
@app.route("/sales", methods=["POST","GET"])
@is_loggin_in
def sales():
    username = session["username"]
    #Grab sales list and send  to the product table in the html
    cur = mysql.connection.cursor()
    cur.execute("SELECT saleName, salePrice, saleQuantity, saleDescription, saleID FROM sales WHERE username = %s", [username])
    salesrows = cur.fetchall()
    return render_template("sales-page.html", salesrows=salesrows)

@app.route("/addsales", methods=["POST","GET"])
@is_loggin_in
def addsales():
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE username = %s", [username])
    productrows = cur.fetchall()
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT * from locations WHERE username = %s", [username])
    locations = cur.fetchall()
    return render_template("sales-add.html", productrows=productrows, locations=locations)

@app.route("/addsalesmodal", methods=["POST","GET"])
@is_loggin_in
def addsalemodalrender():
    return render_template("sales-add.html")

#view products ajax (shows detals of produt and allows users to edit them thorugh bootstrap model)
@app.route("/ajaxViewAddSale",methods=["POST","GET"])
@is_loggin_in
def ajaxViewAddSale():
    username = session["username"]
    if request.method == 'POST':
        productid = request.form['productid']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products WHERE productID = %s", [productid])
        viewProductList = cur.fetchall() 
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * from locations WHERE username = %s", [username])
        locations = cur2.fetchall()
        return jsonify({'htmlresponse': render_template("sale-add-view.html", viewProductList=viewProductList, locations=locations)})
        
@app.route("/ajaxViewSale",methods=["POST","GET"])
@is_loggin_in
def ajaxViewSale():
    username = session["username"]
    if request.method == 'POST':
        saleID = request.form['saleID']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM sales WHERE saleID = %s", [saleID])
        viewSale = cur.fetchall() 
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * from locations WHERE username = %s", [username])
        locations = cur2.fetchall()
        return jsonify({'htmlresponse': render_template("sale-view.html", viewSale=viewSale, locations=locations)})



@app.route("/create_sale", methods=["POST","GET"])
@is_loggin_in
def create_sales():
    username = session["username"]
    if request.method == "POST":
        
        #details from sale form
        sale_details = request.form
        saleName = sale_details["product-name"]
        saleQuantity = int(sale_details["product-quantity"])
        saleLocation = sale_details["product-location"]
        productID = sale_details["productId"]
        salePrice = sale_details["product-price"]
        saleDesc = sale_details["sale-description"]
        fsaleprice = float(salePrice)
        linetotal = fsaleprice * saleQuantity
        print(linetotal)
        #insert into database and create a new sale
        cur = mysql.connection.cursor()
        cur.execute("INSERT into sales(saleName, salePrice, saleQuantity, saleDescription, username, datetime, updatetime, location, productID, linetotal) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (saleName, salePrice, saleQuantity, saleDesc, username, datetime, datetime, saleLocation, productID, linetotal))
        mysql.connection.commit()

        #subtract sale quantity from products
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * from products WHERE productID =%s", [productID])
        original_product = cur2.fetchall()
        
        for row in original_product:
            original_quantity = row[2]

        #make new quantity
        new_quantity = original_quantity - saleQuantity

        #replace existing quantity with new quantity
        cur3 = mysql .connection.cursor()
        cur3.execute("UPDATE products SET quantity=%s WHERE productID =%s",(new_quantity, productID))
        mysql.connection.commit()
        return redirect("/sales")

@app.route("/update_sale", methods=["POST","GET"])
@is_loggin_in
def update_sale():
    if request.method == "POST":
        if request.form.get("deleteButton"):
            sale_details = request.form
            pID = sale_details["productID"]
            #get current quantity of products
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT * from products WHERE productID =%s", [pID])
            product_details = cur2.fetchall()
            for row in product_details:
                product_quantity = row[2]
            sale_quantity = int(sale_details["sale-quantity"])
           

            #add the sale quantity back into the original quanttiy
            updated_product_quantity = product_quantity + sale_quantity
            cur3 = mysql .connection.cursor()
            cur3.execute("UPDATE products SET quantity=%s WHERE productID =%s",(updated_product_quantity, pID))
            mysql.connection.commit()

            #delete the sale
            saleID = sale_details["saleID"]
            #delete the sale
            cur = mysql.connection.cursor()
            cur.execute ("DELETE from sales WHERE saleID = %s", [saleID])
            mysql.connection.commit()
            cur.close()
            return redirect("/sales")
        else:
            sale_details = request.form
            saleid =  sale_details['saleID']
            salename = sale_details['sale-name']
            saledescription = sale_details['sale-description']
            salequantity = int(sale_details['sale-quantity'])
            saleprice = sale_details["sale-price"]
            saleLocation = sale_details["sale-location"]

            #get original product quantity
            pID = sale_details["productID"]
            #get current quantity of products
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT * from products WHERE productID =%s", [pID])
            product_details = cur2.fetchall()
            for row in product_details:
                product_quantity = row[2]
            
            sale_quantitycalc = int(sale_details["sale-quantity"])
            #get original sale quantity
            cur3 = mysql.connection.cursor()
            cur3.execute("SELECT * from sales WHERE saleID =%s", [saleid])
            sale_details = cur3.fetchall()
            for row in sale_details:
                original_sale_quantity = row[2]
            #calculate the amount of product that should be added back or removed
            add_edited_quanttiy = original_sale_quantity - sale_quantitycalc
            #calculate the new product quanttiy
            new_product_quanttiy = add_edited_quanttiy + product_quantity

            #update product quantity
            cur4 = mysql.connection.cursor()
            cur4.execute("UPDATE products SET quantity=%s WHERE productID=%s",[new_product_quanttiy, pID])
            mysql.connection.commit()
            cur4.close()

            #update the sale
            
            fsaleprice = float(saleprice)
            linetotal = salequantity * fsaleprice
            cur = mysql.connection.cursor()
            cur.execute("UPDATE sales SET saleName=%s, salePrice=%s, saleQuantity=%s, saleDescription=%s, updatetime =%s, location =%s, linetotal =%s WHERE saleID=%s",[salename, saleprice, salequantity, saledescription, datetime, saleLocation, linetotal, saleid])
            mysql.connection.commit()
            cur.close()
            return redirect("/sales")



#Location
@app.route("/locations", methods=["POST","GET"])
@is_loggin_in
def locations():
        username = session["username"]
        #Grab Product list and send  to the product table in the html
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM locations WHERE username = %s", [username])
        locationsrows = cur.fetchall()
        return render_template("location-page.html", locationrows=locationsrows)

@app.route("/ajaxViewLocations",methods=["POST","GET"])
def ajaxViewLocation():
  
    if request.method == 'POST':
        locationID = request.form['locationid']
        cur = mysql.connection.cursor()
        cur.execute("SELECT locationName, locationDesc FROM locations WHERE locationID = %s", [locationID])
        viewlocationList = cur.fetchall() 

        for row in viewlocationList:
            currentlocation = row[0]
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM sales WHERE location=%s",[currentlocation])
        saleList = cur2.fetchall()
        return jsonify({'htmlresponse': render_template('location-view-edit.html',viewlocationList=viewlocationList, saleList=saleList)})
       

#render add lcoations modal
@app.route("/ajaxaddlocation", methods=["POST", "GET"])
def ajaxaddLocation():
    return render_template("location-add.html")
#process from form to add lcoations
@app.route("/addlocation", methods=["POST","GET"])
def add_location():
    username = session["username"]
    if request.method =="POST":
        location_details = request.form
        location_name = location_details["location-name"]
        location_desc = location_details["location-description"]
        cur = mysql.connection.cursor()
        cur.execute("INSERT into locations(locationName, username, locationDesc) VALUES(%s, %s, %s)", (location_name, username, location_desc ))
        mysql.connection.commit()
        #prevent modal form resubmission of data
        return redirect("/locations")
        
#expenses
@app.route("/expenses", methods=["POST","GET"])
@is_loggin_in
def expenses():
        username = session["username"]
        #Grab Product list and send  to the product table in the html
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM expenses WHERE username = %s", [username])
        expensesrows = cur.fetchall()
        return render_template("expenses.html", expensesrows=expensesrows)    

#add pexpense ajax
@app.route("/ajaxaddexpenses", methods=["POST", "GET"])
@is_loggin_in
def ajaxaddexpenses():
    return render_template("expense-add.html", locations = locations)

@app.route("/addexpense", methods=["POST","GET"])
@is_loggin_in
def add_expense():
    #if user posts the add product form add products to database
    if request.method =="POST":
        expense_details = request.form
        ename = expense_details["expense-name"]
        eprice = expense_details["expense-price"]
        equantity = expense_details["expense-quanitity"]
        edescription = expense_details["expense-description"]
        user = session["username"]
        cur = mysql.connection.cursor()
        cur.execute("INSERT into expenses(name, price, quantity, description, username, datetime, updatetime) VALUES(%s, %s, %s, %s, %s, %s, %s)", ( ename, eprice, equantity, edescription, user, datetime, datetime))
        mysql.connection.commit()
        #prevent modal form resubmission of data
        return redirect("/expenses")

@app.route("/ajaxViewExpenses",methods=["POST","GET"])
def ajaxViewExpenses():
    if request.method == 'POST':
        expenseid = request.form['expenseid']
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, price, quantity, description, expenseID, datetime FROM expenses WHERE expenseid = %s", [expenseid])
        viewExpenseslist = cur.fetchall() 
        return jsonify({'htmlresponse': render_template('expense-view.html',viewExpenseslist=viewExpenseslist)})


#camera implementation

@app.route("/scanbarcode", methods=["POST","GET"])
def scanbarcode():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    camera = True           
    while camera == True:
        success, frame = cap.read()

        for code in decode(frame):
                if code:
                    barcode = code.data.decode("utf-8")
                    print(barcode)
                    time.sleep(5)
                    username = session["username"]
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT * FROM products WHERE barcode = %s", [barcode])
                    viewProductList = cur.fetchall()
                    if viewProductList:
                        cur2 = mysql.connection.cursor()
                        cur2.execute("SELECT * from locations WHERE username = %s", [username])
                        locations = cur2.fetchall()
                        return render_template("/quick-sale.html", viewProductList=viewProductList, locations=locations)
                    else: 
                        return redirect("/scanbarcode")
        cv2.imshow("Scan-Barcode-Please", frame)
        cv2.waitKey(1)

    return render_template("/scanbarcode.html")



  


#social media





#settings
@app.route("/settings",methods=["POST","GET"])
def settings():
   return render_template("settings.html")

#logout route
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect("/login")


#run app
if __name__== '__main__':
    app.run(debug=True)

