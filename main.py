from questions import get_job_questions
from speaker import speak, USE_ELEVENLABS, check_elevenlabs
from transcriber import transcribe_audio
from recorder import record_audio
from evaluater import evaluate_response
import time
import os

# Show voice status
print("\n" + "=" * 60)
print("🤖 AI INTERVIEW COACH - COMMAND LINE MODE 🤖")
print("=" * 60)
voice_status = check_elevenlabs()
print(f"Voice System: {voice_status}")
print("=" * 60 + "\n")

# Ask for the job role
speak("What job are you preparing for?")
record_audio("job_role.wav", duration=5)
job = transcribe_audio("job_role.wav").lower().strip()

print(f"Job role detected: {job}")

# Get dynamic questions for this job role
questions = get_job_questions(job, num_questions=4)
print(f"Generated {len(questions)} questions for {job} role.")

# Main interview loop
speak(f"Great! Let's begin your {job} interview. I'll ask you {len(questions)} questions, and give you feedback after each one.")
time.sleep(1)

for i, question in enumerate(questions):
    print("\n" + "-" * 40)
    print(f"Question {i+1}/{len(questions)}")
    print("-" * 40)
    
    # Ask the question
    print(f"Interviewer: {question}")
    speak(question)
    
    # Record the answer
    print("\nRecording your answer...")
    record_audio(f"answer_{i}.wav", duration=15)
    
    # Transcribe the answer
    print("\nTranscribing your answer...")
    answer = transcribe_audio(f"answer_{i}.wav")
    print(f"Your answer: {answer}")
    
    # Evaluate the response
    print("\nEvaluating your response...")
    feedback = evaluate_response(question, answer)
    print(f"Feedback: {feedback}")
    
    # Speak the feedback
    speak(feedback)
    time.sleep(1)
    
    if i < len(questions) - 1:
        print("\nPreparing next question...")
        time.sleep(1)

print("\n" + "=" * 40)
print("Interview complete!")
print("=" * 40)
speak("That completes our interview session. Thank you for practicing with me today!")
