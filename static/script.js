```javascript
let questions = [];
let currentQuestionIndex = 0;
let timer = null;
let timeLeft = 0;
let quizMode = 'practice';
let score = 0;

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
});

function initializeEventListeners() {
    document.getElementById('selectAll').addEventListener('click', selectAllTopics);
    document.getElementById('deselectAll').addEventListener('click', deselectAllTopics);
    document.getElementById('startQuiz').addEventListener('click', startQuiz);
    document.getElementById('nextQuestion').addEventListener('click', nextQuestion);
    document.getElementById('prevQuestion').addEventListener('click', prevQuestion);
    document.getElementById('submitQuiz').addEventListener('click', submitQuiz);
}

function selectAllTopics() {
    document.querySelectorAll('input[name="topics"]').forEach(checkbox => checkbox.checked = true);
}

function deselectAllTopics() {
    document.querySelectorAll('input[name="topics"]').forEach(checkbox => checkbox.checked = false);
}

async function startQuiz() {
    const selectedTopics = Array.from(document.querySelectorAll('input[name="topics"]:checked'))
        .map(checkbox => checkbox.value);
    
    if(selectedTopics.length === 0) {
        alert('Please select at least one topic');
        return;
    }

    quizMode = document.querySelector('input[name="mode"]:checked').value;
    
    try {
        const response = await fetch('/get_questions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topics: selectedTopics})
        });
        questions = await response.json();
        
        currentQuestionIndex = 0;
        score = 0;
        
        document.getElementById('topicSelection').style.display = 'none';
        document.getElementById('quizSection').style.display = 'block';
        
        if(quizMode === 'quiz') {
            startTimer(questions.length * 60);
        }
        
        displayQuestion();
    } catch(error) {
        console.error('Error fetching questions:', error);
    }
}

function displayQuestion() {
    const question = questions[currentQuestionIndex];
    document.getElementById('questionText').textContent = question.question;
    
    const optionsContainer = document.getElementById('options');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((option, index) => {
        const button = document.createElement('button');
        button.textContent = option;
        button.classList.add('option-btn');
        button.addEventListener('click', () => checkAnswer(index));
        optionsContainer.appendChild(button);
    });
    
    updateNavigationButtons();
}

function checkAnswer(selectedIndex) {
    const question = questions[currentQuestionIndex];
    const buttons = document.querySelectorAll('.option-btn');
    
    if(quizMode === 'practice') {
        buttons.forEach(button => button.disabled = true);
        buttons[selectedIndex].classList.add(
            selectedIndex === question.correct_answer ? 'correct' : 'incorrect'
        );
        buttons[question.correct_answer].classList.add('correct');
    } else {
        questions[currentQuestionIndex].userAnswer = selectedIndex;
        buttons[selectedIndex].classList.add('selected');
    }
}

function nextQuestion() {
    if(currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        displayQuestion();
    }
}

function prevQuestion() {
    if(currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion();
    }
}

function updateNavigationButtons() {
    document.getElementById('prevQuestion').disabled = currentQuestionIndex === 0;
    document.getElementById('nextQuestion').disabled = currentQuestionIndex === questions.length - 1;
}

function startTimer(seconds) {
    timeLeft = seconds;
    updateTimerDisplay();
    
    timer = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        
        if(timeLeft <= 0) {
            clearInterval(timer);
            submitQuiz();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    document.getElementById('timer').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function submitQuiz() {
    clearInterval(timer);
    
    score = questions.reduce((total, question, index) => {
        return total + (question.userAnswer === question.correct_answer ? 1 : 0);
    }, 0);
    
    displayResults();
}

function displayResults() {
    document.getElementById('quizSection').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    
    const percentage = (score / questions.length) * 100;
    document.getElementById('score').textContent = 
        `Score: ${score}/${questions.length} (${percentage.toFixed(1)}%)`;
    
    const reviewContainer = document.getElementById('questionReview');
    reviewContainer.innerHTML = '';
    
    questions.forEach((question, index) => {
        const div = document.createElement('div');
        div.classList.add('review-question');
        div.innerHTML = `
            <p><strong>Question ${index + 1}:</strong> ${question.question}</p>
            <p>Your answer: ${question.options[question.userAnswer]}</p>
            <p>Correct answer: ${question.options[question.correct_answer]}</p>
        `;
        div.classList.add(question.userAnswer === question.correct_answer ? 'correct' : 'incorrect');
        reviewContainer.appendChild(div);
    });
}
```