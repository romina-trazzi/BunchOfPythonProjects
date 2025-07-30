import os
from flask import Flask, render_template
from api.api_routes import api_blueprint
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.register_blueprint(api_blueprint)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    os.makedirs("output/charts", exist_ok=True)
    app.run(debug=True)
