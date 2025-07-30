from flask import Flask
from dotenv import load_dotenv
from api.routes import api_blueprint

load_dotenv()

app = Flask(__name__)
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    print("✅ App Flask avviata: http://localhost:5000")
    app.run(debug=True)