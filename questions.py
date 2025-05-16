import os

# Try to import OpenAI API for dynamic question generation
USE_OPENAI_FOR_QUESTIONS = True
try:
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    # Initialize the client with minimal required parameters to avoid compatibility issues
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_job_questions(job_title, num_questions=3, interviewer_name="Kashmala"):
        """Generate interview questions for any job role using GPT."""
        print(f"Generating questions for {job_title} role...")
        
        # First, generate a personalized welcome message
        try:
            welcome_prompt = f"""Create a warm, professional welcome message for a mock interview for a {job_title} role. 
            The message should:
            - Greet the candidate
            - Introduce yourself as {interviewer_name}, an AI Interview Coach
            - Mention you'll be asking them questions about the {job_title} role
            - Offer a brief encouragement
            - Keep it under 3 sentences
            
            Return just the welcome message with no additional text or explanation.
            """
            
            welcome_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": welcome_prompt}]
            )
            
            welcome_message = welcome_response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating welcome message: {e}")
            welcome_message = f"Welcome to your {job_title} interview! I'm {interviewer_name}, your AI Interview Coach, and I'll be asking you some questions about your experience and skills. Take your time to think before answering."
        
        # Define generic questions outside of the try block so they're available in the except block
        generic_questions = [
            f"Why are you interested in the {job_title} role?",
            f"What relevant experience do you have for this {job_title} position?",
            f"How do you stay updated with trends in the {job_title} field?",
            f"Tell me about your experience as a {job_title}.",
            f"What skills do you think are most important for a {job_title}?",
            f"Describe a challenging situation you faced in your role as a {job_title}."
        ]
        
        prompt = f"""Generate {num_questions} professional interview questions for a {job_title} role.
        
        The questions should:
        - Be challenging but fair
        - Cover different aspects of the role
        - Be open-ended (not yes/no questions)
        - Focus on experience, skills, and scenarios relevant to the position
        
        Format each question on a new line without numbering.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and clean questions from the response
            questions_text = response.choices[0].message.content
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            # Filter out any non-questions (GPT might add explanations)
            questions = [q for q in questions if q.endswith('?')]
            
            # If we got fewer than requested, add generic questions
            while len(questions) < num_questions and generic_questions:
                questions.append(generic_questions.pop(0))
            
            # Prepend the welcome message as the first "question"
            all_questions = [welcome_message] + questions[:num_questions]
                
            return all_questions  # Return welcome message + the requested number of questions
            
        except Exception as e:
            print(f"Error with OpenAI API call: {e}")
            # If the API call fails, return welcome message + generic questions
            return [welcome_message] + generic_questions[:num_questions]
        
except (ImportError, OSError) as e:
    USE_OPENAI_FOR_QUESTIONS = False
    print(f"Error loading OpenAI for questions: {e}")
    print("Using generic questions. Install OpenAI properly for dynamic question generation.")

def get_job_questions(job_title, num_questions=3, interviewer_name="Kashmala"):
    """Get interview questions for a job role."""
    # Clean and normalize job title
    job_title = job_title.lower().strip()
    
    # Try to generate questions with OpenAI
    if USE_OPENAI_FOR_QUESTIONS:
        try:
            return generate_job_questions(job_title, num_questions, interviewer_name)
        except Exception as e:
            print(f"Failed to generate questions: {e}")
            # Fall through to generic questions if generation fails
    
    # If we can't use OpenAI or it failed, create generic questions
    print(f"Using generic questions for {job_title}")
    welcome_message = f"Welcome to your {job_title} interview! I'm {interviewer_name}, your AI Interview Coach, and I'll be asking you some questions about your experience and skills. Take your time to think before answering."
    
    return [
        welcome_message,
        f"Tell me about your experience as a {job_title}.",
        f"What skills do you think are most important for a {job_title}?",
        f"Describe a challenging situation you faced in your role as a {job_title}."
    ]
