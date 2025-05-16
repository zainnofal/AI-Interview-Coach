# Try to import OpenAI, but provide a fallback if it fails
USE_OPENAI = True
from config import DEBUG

try:
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    if DEBUG:
        print(f"OpenAI API Key in evaluater.py: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
    
    try:
        # Initialize client with minimal required parameters
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        if DEBUG:
            print("OpenAI client initialized successfully")
        
        # Test connection with a simple request
        if DEBUG:
            try:
                print("Testing OpenAI connection...")
                response = client.models.list()
                print(f"OpenAI connection successful - available models: {len(response.data)}")
            except Exception as e:
                print(f"OpenAI connection test failed: {e}")
        
        def evaluate_response_with_openai(question, answer):
            prompt = f"""You are a mock interview coach.

            Interviewer Question: "{question}"
            User's Answer: "{answer}"

            Give a 2-3 sentence evaluation of the answer. Focus on the quality, content, and professionalism of the response.
            
            DO NOT include a follow-up question in your response.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Error in response evaluation: {e}")
                return evaluate_response_fallback(question, answer)
        
        evaluate_response = evaluate_response_with_openai
        
    except Exception as e:
        USE_OPENAI = False
        print(f"OpenAI client initialization error: {e}")
        print("Using fallback evaluator.")
    
except (ImportError, OSError) as e:
    USE_OPENAI = False
    print(f"Error loading OpenAI API: {e}")
    print("Using canned responses for evaluation. Install OpenAI properly for real functionality.")
    
# Fallback response generator
def evaluate_response_fallback(question, answer):
    print(f"Would evaluate response to: {question}")
    
    # Canned responses without follow-up questions
    responses = [
        "Your answer shows good technical knowledge and provides clear examples. To improve, you could quantify the impact of your work more specifically. Consider adding measurable outcomes to strengthen future responses.",
        
        "Good response with concrete practices mentioned. You might consider explaining how these practices improved outcomes in previous roles. Adding specific metrics would make this answer even stronger.",
        
        "Your approach seems methodical and thorough. You could strengthen this answer by mentioning how you collaborate with team members during difficult debugging sessions. Communication is key in technical roles.",
        
        "That's a solid answer showcasing your expertise. To make it stronger, provide more specific metrics or results from your experience. Quantifiable achievements help interviewers understand your impact."
    ]
    
    # Return a response based on the question (using a simple hash)
    hash_value = sum(ord(c) for c in question) % len(responses)
    return responses[hash_value]

# If OpenAI client initialization failed, use the fallback
if not USE_OPENAI:
    evaluate_response = evaluate_response_fallback
