import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/Home';
import TopicSelector from './components/TopicSelector';
import QuizPlayer from './components/QuizPlayer';
import Results from './components/Results';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import api from './services/api';
import './styles/App.css';

function App() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [quizResults, setQuizResults] = useState(null);
  
  useEffect(() => {
    // Load topics when the app initializes
    fetchTopics();
  }, []);
  
  const fetchTopics = async () => {
    setLoading(true);
    try {
      const response = await api.getTopics();
      if (response.data.success) {
        setTopics(response.data.topics);
      } else {
        setError("Failed to load topics: " + response.data.error);
      }
    } catch (err) {
      setError("Error connecting to the server. Please make sure the backend is running.");
      console.error("API error:", err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleGenerateQuiz = async (selectedTopics, quizLength) => {
    setLoading(true);
    try {
      const response = await api.generateQuiz(selectedTopics, quizLength);
      if (response.data.success) {
        setCurrentQuiz(response.data.quiz);
        setQuizResults(null); // Clear any previous results
        return true;
      } else {
        setError("Failed to generate quiz: " + response.data.error);
        return false;
      }
    } catch (err) {
      setError("Error generating quiz. Please try again.");
      console.error("API error:", err);
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const handleQuizComplete = (results) => {
    setQuizResults(results);
  };
  
  if (loading && topics.length === 0) {
    return <LoadingSpinner message="Loading application..." />;
  }
  
  if (error && topics.length === 0) {
    return <ErrorMessage message={error} onRetry={fetchTopics} />;
  }

  return (
    <Router>
      <div className="app-container">
        <Navbar />
        
        {loading && <LoadingSpinner />}
        
        {error && (
          <div className="error-toast">
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}
        
        <Routes>
          <Route 
            path="/" 
            element={<Home topics={topics} onGenerateQuiz={handleGenerateQuiz} />} 
          />
          
          <Route 
            path="/topics" 
            element={
              <TopicSelector 
                topics={topics} 
                onGenerateQuiz={handleGenerateQuiz} 
              />
            } 
          />
          
          <Route 
            path="/quiz" 
            element={
              currentQuiz ? (
                <QuizPlayer 
                  quiz={currentQuiz} 
                  onComplete={handleQuizComplete} 
                />
              ) : (
                <Navigate to="/topics" replace />
              )
            } 
          />
          
          <Route 
            path="/results" 
            element={
              quizResults ? (
                <Results 
                  results={quizResults} 
                  quiz={currentQuiz}
                  onNewQuiz={() => {
                    setCurrentQuiz(null);
                    setQuizResults(null);
                  }} 
                />
              ) : (
                <Navigate to="/topics" replace />
              )
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;