from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
import random
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DB_PATH = os.environ.get('DB_PATH', '../pdf-extraction/extracted_data/nuclear_quiz.db')
IMAGES_DIR = os.environ.get('IMAGES_DIR', '../pdf-extraction/extracted_data/images')

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "API is running"})

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Get all available topics from the database"""
    try:
        conn = get_db_connection()
        topics = conn.execute('SELECT id, name FROM topics ORDER BY name').fetchall()
        conn.close()
        
        return jsonify({
            "success": True,
            "topics": [dict(topic) for topic in topics]
        })
    except Exception as e:
        logging.error(f"Error retrieving topics: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve topics"
        }), 500

@app.route('/api/questions/count', methods=['GET'])
def get_question_count():
    """Get count of questions, optionally filtered by topic"""
    topic_id = request.args.get('topic_id')
    
    try:
        conn = get_db_connection()
        
        if topic_id and topic_id != 'all':
            count = conn.execute(
                'SELECT COUNT(*) FROM questions WHERE topic_id = ?', 
                (topic_id,)
            ).fetchone()[0]
        else:
            count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "count": count
        })
    except Exception as e:
        logging.error(f"Error getting question count: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get question count"
        }), 500

@app.route('/api/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get a specific question by ID with its options and images"""
    try:
        conn = get_db_connection()
        
        # Get question
        question = conn.execute(
            '''
            SELECT q.id, q.question_html, q.answer, t.name as topic, t.id as topic_id, q.page_number
            FROM questions q
            JOIN topics t ON q.topic_id = t.id
            WHERE q.id = ?
            ''',
            (question_id,)
        ).fetchone()
        
        if not question:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Question not found"
            }), 404
        
        # Get options
        options = conn.execute(
            '''
            SELECT option_letter, option_html
            FROM options
            WHERE question_id = ?
            ORDER BY option_letter
            ''',
            (question_id,)
        ).fetchall()
        
        # Get images
        images = conn.execute(
            '''
            SELECT image_path
            FROM images
            WHERE question_id = ?
            ''',
            (question_id,)
        ).fetchall()
        
        conn.close()
        
        # Convert to dictionary
        question_dict = dict(question)
        question_dict["options"] = [dict(opt) for opt in options]
        question_dict["images"] = [img["image_path"] for img in images]
        
        return jsonify({
            "success": True,
            "question": question_dict
        })
    except Exception as e:
        logging.error(f"Error retrieving question {question_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve question"
        }), 500

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    """Generate a quiz based on selected topics and length"""
    data = request.json
    topics = data.get('topics', ['all'])
    quiz_length = min(int(data.get('length', 10)), 100)  # Limit to 100 questions max
    include_answers = data.get('include_answers', False)
    
    try:
        conn = get_db_connection()
        
        # Get questions based on topics
        if 'all' in topics:
            query = '''
                SELECT q.id
                FROM questions q
                JOIN topics t ON q.topic_id = t.id
            '''
            questions = conn.execute(query).fetchall()
        else:
            placeholders = ','.join('?' for _ in topics)
            query = f'''
                SELECT q.id
                FROM questions q
                JOIN topics t ON q.topic_id = t.id
                WHERE t.id IN ({placeholders})
            '''
            questions = conn.execute(query, topics).fetchall()
        
        # Convert to list of IDs
        question_ids = [q['id'] for q in questions]
        
        if not question_ids:
            conn.close()
            return jsonify({
                "success": False,
                "error": "No questions found for the selected topics"
            }), 404
        
        # Select random questions
        selected_ids = []
        if len(question_ids) <= quiz_length:
            selected_ids = question_ids
        else:
            selected_ids = random.sample(question_ids, quiz_length)
        
        # Get full question data for selected IDs
        quiz_questions = []
        for qid in selected_ids:
            # Get question
            question = conn.execute(
                '''
                SELECT q.id, q.question_html, q.answer, t.name as topic
                FROM questions q
                JOIN topics t ON q.topic_id = t.id
                WHERE q.id = ?
                ''',
                (qid,)
            ).fetchone()
            
            # Get options
            options = conn.execute(
                '''
                SELECT option_letter, option_html
                FROM options
                WHERE question_id = ?
                ORDER BY option_letter
                ''',
                (qid,)
            ).fetchall()
            
            # Get images
            images = conn.execute(
                '''
                SELECT image_path
                FROM images
                WHERE question_id = ?
                ''',
                (qid,)
            ).fetchall()
            
            # Convert to dictionary
            q_dict = dict(question)
            q_dict["options"] = [dict(opt) for opt in options]
            q_dict["images"] = [img["image_path"] for img in images]
            
            # Remove answer if not requested
            if not include_answers:
                q_dict["answer"] = None
                
            quiz_questions.append(q_dict)
        
        conn.close()
        
        # Generate a unique quiz ID
        quiz_id = f"quiz_{random.randint(10000, 99999)}"
        
        return jsonify({
            "success": True,
            "quiz": {
                "id": quiz_id,
                "title": f"Nuclear Engineering Quiz - {len(quiz_questions)} Questions",
                "questions": quiz_questions,
                "total_questions": len(quiz_questions)
            }
        })
    except Exception as e:
        logging.error(f"Error generating quiz: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate quiz"
        }), 500

@app.route('/api/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """Serve images from the images directory"""
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """Submit an answer for a question and get feedback"""
    data = request.json
    question_id = data.get('question_id')
    selected_option = data.get('selected_option')
    
    if not question_id or not selected_option:
        return jsonify({
            "success": False,
            "error": "Missing question ID or selected option"
        }), 400
    
    try:
        conn = get_db_connection()
        
        # Get correct answer
        question = conn.execute(
            'SELECT answer FROM questions WHERE id = ?',
            (question_id,)
        ).fetchone()
        
        if not question:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Question not found"
            }), 404
        
        correct_answer = question['answer']
        is_correct = selected_option == correct_answer
        
        conn.close()
        
        return jsonify({
            "success": True,
            "result": {
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "selected_option": selected_option
            }
        })
    except Exception as e:
        logging.error(f"Error submitting answer: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to submit answer"
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the question database"""
    try:
        conn = get_db_connection()
        
        # Get total questions
        total_questions = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        
        # Get questions per topic
        topic_stats = conn.execute('''
            SELECT t.name, COUNT(q.id) as question_count
            FROM topics t
            LEFT JOIN questions q ON t.id = q.topic_id
            GROUP BY t.id
            ORDER BY question_count DESC
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_questions": total_questions,
                "topics": [dict(stat) for stat in topic_stats]
            }
        })
    except Exception as e:
        logging.error(f"Error retrieving stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve stats"
        }), 500

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Please run the PDF extraction script first to create the database.")
        exit(1)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
