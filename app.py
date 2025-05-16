from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import time
from questions import get_job_questions
from speaker import speak, USE_OPENAI_TTS, check_voice_services, set_voice
from transcriber import transcribe_audio
from recorder import record_audio_threaded, stop_current_recording
from evaluater import evaluate_response
import threading
import json

app = Flask(__name__)

interview_state = {
    "job": "",
    "current_question_index": -1,
    "questions": [],
    "answers": [],
    "feedbacks": [],
    "is_recording": False,
    "is_processing": False,
    "is_complete": False,
    "using_openai_tts": USE_OPENAI_TTS,
    "interviewer_name": "",
    "interviewer_voice": ""
}

@app.route('/')
def serve():
    return render_template('index.html')

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Check the status of voice services
@app.route('/api/voice_status', methods=['GET'])
def get_voice_status():
    voice_status = check_voice_services()
    
    return jsonify({
        "using_openai_tts": USE_OPENAI_TTS,
        "active_voice": voice_status["active"],
        "status": voice_status
    })

# Try to reconnect to voice services
@app.route('/api/check_voice', methods=['GET'])
def refresh_voice():
    voice_status = check_voice_services()
    
    return jsonify({
        "using_openai_tts": USE_OPENAI_TTS,
        "active_voice": voice_status["active"],
        "status": voice_status
    })

@app.route('/api/jobs', methods=['GET'])
def get_suggested_jobs():
    """Return a list of suggested job roles using GPT"""
    try:
        from openai import OpenAI
        from config import OPENAI_API_KEY
        
        # Initialize the client with minimal required parameters
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Generate a list of 10 diverse and popular job titles that people might want to practice interviewing for. Return only the job titles, one per line, without any numbering or extra text."}]
            )
            
            # Parse the response
            jobs_text = response.choices[0].message.content
            suggested_jobs = [job.strip() for job in jobs_text.split('\n') if job.strip()]
            
            # Ensure we have at least some job suggestions
            if not suggested_jobs:
                raise Exception("No job suggestions generated")
                
            return jsonify({"jobs": suggested_jobs})
        except Exception as e:
            print(f"Error generating job suggestions with API: {e}")
            raise e
    except Exception as e:
        print(f"Error generating job suggestions: {e}")
        # Fallback generic job roles
        fallback_jobs = [
            "Software Engineer", "Product Manager", "Data Scientist", 
            "Marketing Manager", "UX Designer", "Project Manager"
        ]
        return jsonify({"jobs": fallback_jobs})

@app.route('/api/start', methods=['POST'])
def start_interview():
    global interview_state
    
    # Reset interview state
    interview_state = {
        "job": "",
        "current_question_index": -1,
        "questions": [],
        "answers": [],
        "feedbacks": [],
        "is_recording": False,
        "is_processing": False,
        "is_complete": False,
        "using_openai_tts": USE_OPENAI_TTS,
        "interviewer_name": "",
        "interviewer_voice": ""
    }
    
    # Get job role from request
    data = request.json
    job = data.get('job', '').strip()
    
    if not job:
        return jsonify({"status": "error", "message": "Job role is required"})
    
    # Get number of questions from request or use default
    num_questions = data.get('num_questions', 3)
    
    # Get interviewer settings
    interviewer_name = data.get('interviewer_name', 'Kashmala')
    interviewer_voice = data.get('interviewer_voice', 'shimmer')
    
    # Generate questions for this job role
    try:
        questions = get_job_questions(job, num_questions=num_questions, interviewer_name=interviewer_name)
        if not questions:
            return jsonify({"status": "error", "message": "Failed to generate questions"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error generating questions: {str(e)}"})
    
    interview_state["job"] = job
    interview_state["questions"] = questions
    interview_state["interviewer_name"] = interviewer_name
    interview_state["interviewer_voice"] = interviewer_voice
    
    # Set the voice to use
    set_voice(interviewer_voice)
    
    # Start interview with welcome message
    def speak_welcome():
        # Speak the welcome message (first item in questions array)
        welcome_message = interview_state["questions"][0]
        speak(welcome_message)
        time.sleep(1)
        
        # Move to the first actual question (index 1 in the array)
        interview_state["current_question_index"] = 1
        speak(interview_state["questions"][1])
    
    threading.Thread(target=speak_welcome).start()
    
    return jsonify({
        "status": "success", 
        "message": "Interview started",
        "job": job,
        "questions": questions,
        "using_openai_tts": USE_OPENAI_TTS
    })

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(interview_state)

@app.route('/api/record', methods=['POST'])
def record_answer():
    if interview_state["current_question_index"] < 0:
        return jsonify({"status": "error", "message": "Interview not started"})
    
    if interview_state["is_recording"] or interview_state["is_processing"]:
        return jsonify({"status": "error", "message": "Already recording or processing"})
    
    interview_state["is_recording"] = True
    
    def recording_finished():
        process_recording_result()
    
    # Record the answer
    index = interview_state["current_question_index"]
    filename = f"answer_{index}.wav"
    
    # Start recording in a thread - using manual recording mode
    record_audio_threaded(
        filename,
        callback=recording_finished,
        manual_mode=True  # Use manual mode (requires explicit stop)
    )
    
    return jsonify({"status": "success", "message": "Recording started - press stop when finished"})

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording():
    """Stop the current recording session"""
    print("\n=== STOP RECORDING API CALLED ===")
    print(f"Current interview state: {json.dumps(interview_state, indent=2)}")
    
    if not interview_state["is_recording"]:
        print("ERROR: Attempted to stop recording but not currently recording")
        print(f"Current question index: {interview_state['current_question_index']}")
        print(f"Is processing: {interview_state['is_processing']}")
        return jsonify({"status": "error", "message": "Not currently recording"})
    
    # Call the stop function
    print("Stopping recording via API request")
    success = stop_current_recording()
    
    # Add a safety measure to ensure the recording state is properly reset
    if success:
        # Don't actually set is_recording to False here, let the callback handle it
        print("Successfully requested recording to stop")
    else:
        print("WARNING: Failed to stop recording, forcing state reset")
        interview_state["is_recording"] = False
    
    print("=== END STOP RECORDING API ===\n")
    return jsonify({"status": "success", "message": "Recording stop requested"})

@app.route('/api/reset_recording', methods=['POST'])
def reset_recording_state():
    """Emergency endpoint to reset the recording state if it gets stuck"""
    global interview_state
    
    print("\n=== EMERGENCY RECORDING STATE RESET ===")
    print(f"Previous state: {json.dumps(interview_state, indent=2)}")
    
    # Reset all relevant flags
    interview_state["is_recording"] = False
    interview_state["is_processing"] = False
    
    # Also reset the recorder module's state
    from recorder import recording_active, stop_recording
    if recording_active:
        print("Resetting recorder module's recording_active flag")
        import recorder
        recorder.recording_active = False
        recorder.stop_recording = True
    
    print(f"New state: {json.dumps(interview_state, indent=2)}")
    print("=== EMERGENCY RESET COMPLETE ===\n")
    
    return jsonify({
        "status": "success", 
        "message": "Recording state has been reset"
    })

def process_recording_result():
    # This function is called after recording finishes
    print(f"Processing recording result. Current state: recording={interview_state['is_recording']}, processing={interview_state['is_processing']}")
    interview_state["is_recording"] = False
    interview_state["is_processing"] = True
    print("Set is_recording=False, is_processing=True")
    
    # Get the current index
    index = interview_state["current_question_index"]
    filename = f"answer_{index}.wav"
    
    # Transcribe the answer
    try:
        print(f"Transcribing answer from {filename}")
        answer = transcribe_audio(filename)
        interview_state["answers"].append(answer)
        print(f"Transcription result: {answer[:50]}...")
        
        # Evaluate the response
        question = interview_state["questions"][index]
        print(f"Evaluating response to: {question}")
        feedback = evaluate_response(question, answer)
        interview_state["feedbacks"].append(feedback)
        print(f"Feedback: {feedback[:50]}...")
        
        # Speak the feedback
        speak(feedback)
        time.sleep(1)
        
        # Move to next question or complete interview
        print(f"Moving to next question. Current index: {interview_state['current_question_index']}")
        interview_state["current_question_index"] += 1
        print(f"New index: {interview_state['current_question_index']}, Total questions: {len(interview_state['questions'])}")
        
        # Note: index 0 was the welcome message, so we include it in the length check
        if interview_state["current_question_index"] < len(interview_state["questions"]):
            # Speak the next question
            next_question = interview_state["questions"][interview_state["current_question_index"]]
            print(f"Next question: {next_question}")
            speak(next_question)
        else:
            interview_state["is_complete"] = True
            interviewer_name = interview_state["interviewer_name"]
            print("Interview complete")
            speak(f"That completes our interview session. Thank you for practicing with me today! This is {interviewer_name}, wishing you the best of luck with your job search.")
    except Exception as e:
        print(f"Error processing recording: {e}")
    finally:
        # Make sure to reset processing state when done
        interview_state["is_processing"] = False
        print("Set is_processing=False")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🤖 AI INTERVIEW COACH 🤖")
    print("=" * 60)
    print("Open your browser at http://localhost:8080 to start")
    print("Using OpenAI TTS: " + ("YES" if USE_OPENAI_TTS else "NO - using system voice"))
    print("=" * 60 + "\n")
    app.run(debug=True, port=8080) 