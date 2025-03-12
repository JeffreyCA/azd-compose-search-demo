from flask import Flask, render_template
from api.pages import bp as api_bp

app = Flask(__name__, template_folder='templates')
app.register_blueprint(api_bp, url_prefix="/api")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
