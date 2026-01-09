from app import __init__

app = _init_.create_app()

if __name__ == "__main__":
    app.run(debug=True)