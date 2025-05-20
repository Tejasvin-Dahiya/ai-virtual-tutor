import os
from typing import List, Dict, Any, Optional
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class AITutorService:
    def __init__(self):
        # Initialize with your OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Configuration for different AI behaviors
        self.tutor_personas = {
            "default": "You are a knowledgeable and patient tutor who explains concepts clearly.",
            "strict": "You are a strict tutor who expects precision and gives direct feedback.",
            "friendly": "You are a friendly tutor who encourages learning through positive reinforcement."
        }
        
        
        self.use_fallback = not self.api_key
        if self.use_fallback:
            print("WARNING: No OpenAI API key found. Using fallback responses.")
    
    def generate_learning_path(self, subject_name: str, level: str) -> Dict[str, Any]:
        """Generate a customized learning path based on subject and proficiency level"""
        if self.use_fallback:
            return self._create_fallback_learning_path(subject_name, level)
            
        prompt = f"""
        Create a detailed, structured learning path for {subject_name} at {level} level.
        
        Requirements:
        1. Include 5-8 modules in a logical progression
        2. For each module provide:
           - Title (specific to the subject and level)
           - Detailed description of what will be learned
           - Clear learning objectives (3-5 bullet points)
           - Estimated time to complete (e.g., "2-3 hours")
           - 3-5 high-quality learning resources (as text suggestions with types)
           - Prerequisites (if any)
        
        Example module structure:
        {{
            "id": 1,
            "title": "Introduction to Calculus",
            "description": "Learn the fundamental concepts of limits and derivatives",
            "objectives": [
                "Understand the concept of a limit",
                "Calculate simple derivatives",
                "Apply derivatives to solve basic problems"
            ],
            "estimatedTime": "3-4 hours",
            "resources": [
                "Khan Academy: Introduction to Limits (video)",
                "Calculus Made Easy by Silvanus Thompson (book)",
                "Derivative Practice Problems (interactive exercises)"
            ],
            "prerequisites": ["Basic algebra"]
        }}
        
        Return the complete learning path as a JSON object with this exact structure:
        {{
            "subject": "{subject_name}",
            "level": "{level}",
            "totalEstimatedTime": "X hours",
            "modules": [MODULE_OBJECTS]
        }}
        """
        
        response = self._call_ai_api(prompt, max_tokens=1500)
        print("response: ", response)
        try:
            learning_path = json.loads(response)
            print("learning_path: ", learning_path)
            # Validate the structure
            if not all(key in learning_path for key in ["subject", "level", "modules"]):
                raise ValueError("Invalid structure in AI response")
            return learning_path
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing AI response: {str(e)}")
            return self._create_fallback_learning_path(subject_name, level)
    
    def get_chat_response(
        self,
        subject_name: str,
        user_message: str,
        chat_history: List[Dict] = None,
        tutor_style: str = "default",
        user_level: str = "beginner"
    ) -> str:
        """Get a contextual response from the AI tutor"""
        if self.use_fallback:
            return self._create_fallback_chat_response(subject_name, user_message)
            
        # Prepare context from chat history
        context_messages = []
        
        # System message defining the tutor's role
        system_message = {
            "role": "system",
            "content": f"{self.tutor_personas.get(tutor_style, self.tutor_personas['default'])} "
                      f"You specialize in teaching {subject_name} to {user_level} level students. "
                      "Adapt your explanations to the student's level. Ask clarifying questions "
                      "when needed, and provide examples to illustrate concepts."
        }
        context_messages.append(system_message)
        
        # Add chat history if available
        if chat_history:
            for msg in chat_history[-6:]:  # Keep last 6 messages for context
                role = "assistant" if msg["sender"] == "tutor" else "user"
                context_messages.append({"role": role, "content": msg["content"]})
        
        # Add current user message
        context_messages.append({"role": "user", "content": user_message})
        
        # Additional instructions for the AI
        context_messages.append({
            "role": "system",
            "content": "Remember to: "
                       "1. Break down complex concepts "
                       "2. Provide real-world examples "
                       "3. Check for understanding "
                       "4. Suggest relevant resources when helpful"
        })
        
        response = self._call_ai_api(
            messages=context_messages,
            temperature=0.7 if tutor_style == "friendly" else 0.5,
            max_tokens=500
        )
        
        return response
    
    def generate_practice_questions(
        self,
        subject_name: str,
        topic: str,
        level: str,
        question_type: str = "multiple_choice",
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate practice questions on a specific topic"""
        if self.use_fallback:
            return self._create_fallback_questions(subject_name, topic, count)
            
        prompt = f"""
        Generate {count} {question_type} practice questions about {topic} in {subject_name} 
        for {level} level students. For each question include:
        - The question text
        - Correct answer
        - 3-4 distractors (for multiple choice)
        - Brief explanation of the correct answer
        - Difficulty level (easy, medium, hard)
        
        Return the questions as a JSON array with this structure:
        [
            {{
                "question": "Question text",
                "type": "{question_type}",
                "options": ["Option1", "Option2", "Option3", "Option4"],
                "correct_answer": "Option1",
                "explanation": "Detailed explanation...",
                "difficulty": "easy"
            }}
        ]
        """
        
        response = self._call_ai_api(prompt, max_tokens=1200)
        
        try:
            questions = json.loads(response)
            if not isinstance(questions, list):
                raise ValueError("Expected array of questions")
            return questions
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing questions: {str(e)}")
            return self._create_fallback_questions(subject_name, topic, count)
    
    def _call_ai_api(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> str:
        """Make a call to the OpenAI API with either prompt or messages"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            return f"I'm having trouble accessing my knowledge base. Please try again later."
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return "An unexpected error occurred. Please try your request again."
    
    def _create_fallback_learning_path(self, subject_name: str, level: str) -> Dict[str, Any]:
        """Create a structured fallback learning path"""
        modules = []
        base_topics = {
            "beginner": ["Introduction", "Fundamentals", "Basic Applications"],
            "intermediate": ["Core Concepts", "Problem Solving", "Practical Applications"],
            "advanced": ["Advanced Theory", "Complex Problems", "Research Applications"]
        }
        
        for i, topic in enumerate(base_topics.get(level, base_topics["beginner"]), 1):
            modules.append({
                "id": i,
                "title": f"{topic} of {subject_name}",
                "description": f"Learn {topic.lower()} in {subject_name}",
                "objectives": [
                    f"Understand basic {topic.lower()} concepts",
                    f"Apply {topic.lower()} to simple problems",
                    f"Recognize {topic.lower()} in practical scenarios"
                ],
                "estimatedTime": f"{i+1} hours",
                "resources": [
                    f"Introduction to {subject_name} (Textbook)",
                    f"{topic} Tutorial (Video)",
                    f"Practice Exercises (Online)"
                ],
                "prerequisites": []
            })
        
        return {
            "subject": subject_name,
            "level": level,
            "totalEstimatedTime": f"{len(modules)*2} hours",
            "modules": modules
        }
    
    def _create_fallback_chat_response(self, subject_name: str, user_message: str) -> str:
        """Create a fallback response when API fails"""
        responses = [
            f"I specialize in {subject_name}. Could you clarify your question about '{user_message}'?",
            f"That's an interesting question about {subject_name}. I'd need more context to give a precise answer.",
            f"For questions about {user_message} in {subject_name}, I typically recommend starting with the basics.",
            f"Regarding {user_message}, this is an important concept in {subject_name}. What specific aspect are you interested in?"
        ]
        return responses[len(user_message) % len(responses)]
    
    def _create_fallback_questions(self, subject_name: str, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate fallback practice questions"""
        questions = []
        for i in range(1, count+1):
            questions.append({
                "question": f"Sample question {i} about {topic} in {subject_name}?",
                "type": "multiple_choice",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": f"Option {['A','B','C','D'][i%4]}",
                "explanation": f"This is a sample explanation for question {i}.",
                "difficulty": ["easy", "medium", "hard"][i%3]
            })
        return questions