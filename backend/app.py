from flask import Flask, request
app = Flask(__name__)
@app.route("/")
def home():
    return "ScanWise Flask backend is running!"
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    print(data)
    return "Analyze endpoint is working!"
if __name__ == "__main__":
    app.run(debug=True)