from flask import Flask, render_template, request

app = Flask(__name__)

def authentic(username, password):
    #TODO - authenticate against the fop db
    return username == 'ferguman' and password == 'wood$lye9sheep'

@app.route("/")
def home():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route("/login", methods=['POST'])
def process_login():

    if authentic(request.form['username'], request.form['password']):
        session['logged_in_user'] = request.form['username']
        return render_template('home.html')
    else:
        return render_template('login.html')

# TODO - write a logout function
       

@app.route("/login", methods=['GET'])
def get_login_form():
     # show the login form 
     return render_template('login.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
