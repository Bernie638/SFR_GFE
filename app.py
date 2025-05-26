```python
from flask import Flask, jsonify, request, render_template
import json
import random
from collections import defaultdict

app = Flask(__name__)

# Load questions from JSON file
with open('questions.json') as f:
    questions_data = json.load(f)
    all_questions = questions_data['questions']

# Track user sessions and scores
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/topics', methods=['GET']) 
def get_topics():
    topics = list(set([q['topic'] for q in all_questions]))
    return jsonify(topics)

@app.route('/api/questions', methods=['POST'])
def get_questions():
    data = request.get_json()
    selected_topics = data.get('topics', [])
    mode = data.get('mode', 'practice')
    
    filtered_questions = [q for q in all_questions if q['topic'] in selected_topics]
    random.shuffle(filtered_questions)
    
    session_id = random.randint(1000,9999)
    sessions[session_id] = {
        'questions': filtered_questions,
        'current_index': 0,
        'score': 0,
        'mode': mode,
        'answers': [],
        'topic_scores': defaultdict(lambda: {'correct': 0, 'total': 0})
    }
    
    return jsonify({'session_id': session_id})

@app.route('/api/question/<int:session_id>', methods=['GET'])
def get_question(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 404
        
    session = sessions[session_id]
    if session['current_index'] >= len(session['questions']):
        return jsonify({'complete': True})
        
    question = session['questions'][session['current_index']]
    if session['mode'] == 'quiz':
        del question['correct_answer']
        
    return jsonify(question)

@app.route('/api/answer/<int:session_id>', methods=['POST'])
def submit_answer(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 404
        
    session = sessions[session_id]
    current_q = session['questions'][session['current_index']]
    
    data = request.get_json()
    user_answer = data['answer']
    correct = user_answer == current_q['correct_answer']
    
    session['answers'].append({
        'question_index': session['current_index'],
        'correct': correct,
        'user_answer': user_answer
    })
    
    if correct:
        session['score'] += 1
    
    session['topic_scores'][current_q['topic']]['total'] += 1
    if correct:
        session['topic_scores'][current_q['topic']]['correct'] += 1
    
    session['current_index'] += 1
    
    if session['mode'] == 'practice':
        return jsonify({
            'correct': correct,
            'correct_answer': current_q['correct_answer'],
            'explanation': current_q.get('explanation', '')
        })
    else:
        return jsonify({'received': True})

@app.route('/api/results/<int:session_id>', methods=['GET'])
def get_results(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 404
        
    session = sessions[session_id]
    total_questions = len(session['questions'])
    
    results = {
        'score': session['score'],
        'total': total_questions,
        'percentage': round((session['score'] / total_questions) * 100, 1),
        'topic_breakdown': {},
        'answers': session['answers']
    }
    
    for topic, scores in session['topic_scores'].items():
        results['topic_breakdown'][topic] = {
            'correct': scores['correct'],
            'total': scores['total'],
            'percentage': round((scores['correct'] / scores['total']) * 100, 1)
        }
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
```