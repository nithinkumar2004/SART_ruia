from app import create_app

app = create_app()

if __name__ == "__main__":
    # Running customer application locally on port 5001 (Nexus runs on 5000)
    app.run(debug=True, port=5001)
