from app import app

# when a web browser requests either of these two URLs, Flask is going to invoke this function and pass its return value 
# back to the browser as a response
@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"