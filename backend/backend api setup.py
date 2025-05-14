cd ../backend

# Install required packages
pip install flask flask-cors

# Create .env file for configuration
echo "DB_PATH=../pdf-extraction/extracted_data/nuclear_quiz.db" > .env
echo "IMAGES_DIR=../pdf-extraction/extracted_data/images" >> .env
echo "PORT=5000" >> .env

# Run the API server
python quiz-app-backend.py