cd backend

# Install required packages
pip install flask flask-cors python-dotenv

# Create .env file for configuration
cat <<EOF > .env
DB_PATH=../pdf-extraction/extracted_data/nuclear_quiz.db
IMAGES_DIR=../pdf-extraction/extracted_data/images
PORT=5000
EOF

# Run the API server
python quiz-app-backend.py
