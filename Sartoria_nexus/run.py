from app import create_app

app = create_app()

if __name__ == "__main__":
    # Running locally in debug mode on port 5000
    app.run(debug=True, port=5000)
