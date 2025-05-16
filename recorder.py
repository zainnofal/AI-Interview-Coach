import os
import time
import threading

# Try to import sound recording libraries, but provide a fallback if they fail
USE_SOUNDDEVICE = True
try:
    import sounddevice as sd
    from scipy.io.wavfile import write
    import numpy as np
    import queue
    
    def record_audio_with_device(filename="user_input.wav", duration=15, fs=44100, callback=None):
        """Record audio for a fixed duration."""
        print("🎤 Recording...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        write(filename, fs, audio)
        print("✅ Recorded")
        if callback:
            callback()
    
    def record_audio_voice_activated(filename="user_input.wav", fs=44100, silence_threshold=0.02, silence_duration=2.0, callback=None):
        """
        Record audio until silence is detected for a certain duration.
        
        Parameters:
            filename: Output WAV file
            fs: Sample rate
            silence_threshold: Amplitude threshold to consider as silence
            silence_duration: How long silence should persist before stopping (seconds)
            callback: Function to call after recording completes
        """
        print("🎤 Recording... (Stop automatically when you pause speaking)")
        print(f"Listening for voice activity... (silence_threshold={silence_threshold}, silence_duration={silence_duration}s)")
        
        # Create a queue to communicate between the audio callback and the main thread
        q = queue.Queue()
        
        # Initialize variables for silence detection
        last_audio_time = time.time()
        is_silent = True
        has_spoken = False
        start_time = time.time()
        
        # Create arrays to store debug data
        volumes = []
        silent_states = []
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal last_audio_time, is_silent, has_spoken
            
            # Calculate volume (RMS amplitude)
            volume_norm = np.linalg.norm(indata) / np.sqrt(frames)
            volumes.append(volume_norm)  # Store for debugging
            
            # Check if the current frame is silent
            current_is_silent = volume_norm < silence_threshold
            silent_states.append(current_is_silent)  # Store for debugging
            
            # Debug output
            if len(volumes) % 10 == 0:  # Print every 10th value to reduce output
                print(f"Current volume: {volume_norm:.6f} {'(SILENT)' if current_is_silent else '(SPEAKING)'}")
            
            # Only update the last_audio_time if we've detected speech followed by silence
            if not current_is_silent:
                has_spoken = True
                is_silent = False
                last_audio_time = time.time()
            elif has_spoken and not is_silent and current_is_silent:
                # Transition from speech to silence
                is_silent = True
                print(f"Silence detected at {time.time() - start_time:.2f}s - will stop in {silence_duration}s if silence continues")
            
            # Add the current audio frame to the queue
            q.put(indata.copy())
        
        # Start recording with callback
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=fs)
        with stream:
            print("👂 Speak now - recording will stop after you pause...")
            
            # Keep recording until silence is detected for the specified duration
            chunks = []
            recording_started = False
            
            while True:
                # Check for long silence after speech to end recording
                if has_spoken and is_silent:
                    silence_time = time.time() - last_audio_time
                    if silence_time > silence_duration:
                        print(f"Silence of {silence_time:.2f}s detected, stopping recording.")
                        break
                    elif silence_time > 0.5 and silence_time % 0.5 < 0.1:  # Print roughly every 0.5 seconds
                        print(f"Silent for {silence_time:.1f}s (waiting for {silence_duration}s to stop)")
                
                # Get audio data from the queue (non-blocking)
                try:
                    data = q.get_nowait()
                    chunks.append(data)
                    if not recording_started and has_spoken:
                        recording_started = True
                        print("Recording started!")
                except queue.Empty:
                    # No audio data available, continue checking
                    time.sleep(0.1)
        
        # Print debug summary
        if volumes:
            avg_volume = sum(volumes) / len(volumes)
            max_volume = max(volumes)
            print(f"\nRecording stats:")
            print(f"Duration: {time.time() - start_time:.2f}s")
            print(f"Average volume: {avg_volume:.6f}")
            print(f"Max volume: {max_volume:.6f}")
            print(f"Threshold: {silence_threshold}")
            print(f"Suggested threshold: {max(avg_volume * 0.2, 0.01):.6f} (if sensitivity issues persist)")
        
        # Concatenate all chunks and save as WAV file
        if chunks:
            audio_data = np.concatenate(chunks, axis=0)
            write(filename, fs, audio_data)
            print("✅ Recording saved to", filename)
        else:
            print("⚠️ No audio recorded")
            # Create an empty file
            with open(filename, 'wb') as f:
                f.write(b'')
        
        if callback:
            callback()
    
    def record_audio_manual(filename="user_input.wav", fs=44100, callback=None):
        """
        Record audio until explicitly stopped via the stop_recording flag.
        This requires the main application to update the stop_recording flag.
        
        Parameters:
            filename: Output WAV file
            fs: Sample rate
            callback: Function to call after recording completes
        """
        print(f"\n=== MANUAL RECORDING STARTED for {filename} ===")
        print("🎤 Recording... (Press Stop when finished)")
        
        # Create a queue to communicate between the audio callback and the main thread
        q = queue.Queue()
        
        # Flag that will be set to True when recording should stop
        # This flag is meant to be modified from the outside
        global stop_recording
        stop_recording = False
        print(f"Initial stop_recording flag: {stop_recording}")
        
        def audio_callback(indata, frames, time_info, status):
            # Add the current audio frame to the queue
            q.put(indata.copy())
        
        # Start recording with callback
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=fs)
        with stream:
            print("👂 Speak now - recording until you press Stop...")
            
            # Keep recording until explicitly told to stop
            chunks = []
            
            # Add a timeout safety mechanism
            start_time = time.time()
            max_duration = 120  # Maximum 2 minutes to prevent unending recordings
            
            while not stop_recording:
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    print(f"⚠️ Recording timed out after {max_duration} seconds")
                    break
                
                # Every 5 seconds, print a status update
                if int(elapsed) % 5 == 0 and int(elapsed) > 0 and int(elapsed - 0.1) % 5 != 0:
                    print(f"Still recording... {int(elapsed)}s elapsed. stop_recording={stop_recording}")
                
                # Get audio data from the queue (non-blocking)
                try:
                    data = q.get_nowait()
                    chunks.append(data)
                except queue.Empty:
                    # No audio data available, continue checking
                    time.sleep(0.1)
        
        print(f"Recording loop exited. stop_recording={stop_recording}, chunks={len(chunks)}")
        
        # Concatenate all chunks and save as WAV file
        if chunks:
            audio_data = np.concatenate(chunks, axis=0)
            write(filename, fs, audio_data)
            print(f"✅ Recording saved to {filename}, duration: {len(audio_data)/fs:.2f}s")
        else:
            print("⚠️ No audio recorded")
            # Create an empty file
            with open(filename, 'wb') as f:
                f.write(b'')
        
        print(f"Preparing to call callback, stop_recording={stop_recording}")
        
        # Explicitly set global flag back to False, to ensure it's reset for next recording
        global recording_active
        recording_active = False
        
        if callback:
            print("Calling recording callback function")
            callback()
        print("Record function completed")
        print(f"=== MANUAL RECORDING COMPLETED for {filename} ===\n")
    
    # Set the default recording function
    record_audio = record_audio_manual
    
except (ImportError, OSError) as e:
    USE_SOUNDDEVICE = False
    print(f"Error loading audio recording libraries: {e}")
    print("Using a simulation for audio recording. Install sounddevice and scipy properly for real functionality.")
    
    # Create an empty audio file to maintain the workflow
    def create_empty_wav(filename):
        # Create an empty wav file so that the workflow doesn't break
        with open(filename, 'w') as f:
            f.write('')
    
    # Fixed duration recording simulation
    def record_audio_fallback(filename="user_input.wav", duration=15, fs=44100, callback=None):
        """Simulate fixed duration recording."""
        print(f"🎤 Recording for {duration} seconds (simulated)...")
        
        # Create a progress display
        total_dots = 20
        for i in range(total_dots):
            print(".", end="", flush=True)
            time.sleep(duration / total_dots)
        print(" Done!")
        
        # Create an empty file
        create_empty_wav(filename)
        print("✅ Simulated recording complete")
        
        if callback:
            callback()
    
    # Simulate voice-activated recording for fallback mode
    def record_audio_voice_activated_fallback(filename="user_input.wav", fs=44100, 
                                             silence_threshold=0.02, silence_duration=2.0, callback=None):
        """Simulate voice-activated recording."""
        print(f"🎤 Recording until silence detected (simulated)...")
        print("Speak as long as you want. Recording will stop after you pause.")
        
        # Simulate waiting for user input
        input("Press Enter when you've finished speaking (simulating voice detection)...")
        
        # Create an empty file
        create_empty_wav(filename)
        print("✅ Simulated recording complete")
        
        if callback:
            callback()
    
    # Simulate manual recording for fallback mode
    def record_audio_manual_fallback(filename="user_input.wav", fs=44100, callback=None):
        """Simulate manual recording."""
        print(f"🎤 Recording until stopped (simulated)...")
        print("Speak as long as you want. Press the Stop button when finished.")
        
        # Simulate waiting for stop signal
        global stop_recording
        stop_recording = False
        
        while not stop_recording:
            time.sleep(0.5)  # Check every half second if we should stop
        
        # Create an empty file
        create_empty_wav(filename)
        print("✅ Simulated recording complete")
        
        if callback:
            callback()
    
    # Use manual recording as the default
    record_audio = record_audio_manual_fallback

# Global variable to control recording state
stop_recording = False
recording_active = False  # Track if a recording session is currently active

# Function to stop recording
def stop_current_recording():
    """Stop the current recording session"""
    global stop_recording, recording_active
    print(f"\n=== STOP CURRENT RECORDING FUNCTION ===")
    print(f"Current stop_recording flag: {stop_recording}")
    print(f"Current recording_active status: {recording_active}")
    
    if not recording_active:
        print("WARNING: No active recording session to stop!")
        print("This could happen if:")
        print("- The recording thread hasn't started yet")
        print("- A previous stop request is still being processed")
        print("- The recording thread has already completed")
        print("=== END STOP FUNCTION (NO ACTIVE RECORDING) ===\n")
        return False
    
    stop_recording = True
    print(f"Set stop_recording = {stop_recording}")
    print("=== END STOP FUNCTION ===\n")
    return True

# Function to record in a thread so it doesn't block the UI
def record_audio_threaded(filename="user_input.wav", duration=None, fs=44100, callback=None, 
                         silence_threshold=0.02, silence_duration=2.0, manual_mode=True):
    """
    Record audio in a separate thread so it doesn't block
    """
    global stop_recording, recording_active
    stop_recording = False  # Reset stop flag before starting
    recording_active = True  # Set recording as active
    
    print(f"\n=== STARTING NEW RECORDING THREAD ===")
    print(f"Filename: {filename}")
    print(f"Manual mode: {manual_mode}")
    print(f"Reset stop_recording to {stop_recording}")
    print(f"Set recording_active to {recording_active}")
    
    def record_thread():
        global recording_active
        try:
            print(f"Recording thread started for {filename}")
            if manual_mode:
                # Use manual recording (start/stop button)
                if "manual" in record_audio.__name__:
                    record_audio(filename, fs=fs, callback=callback)
                else:
                    print("Using fixed duration recording (15 seconds) as fallback")
                    record_audio(filename, 15, fs, callback)
            elif duration is not None:
                # Use fixed duration recording if duration is specified
                if "voice_activated" not in record_audio.__name__:
                    record_audio(filename, duration, fs, callback)
                else:
                    print("Using voice-activated recording (ignoring duration parameter)")
                    record_audio(filename, fs=fs, silence_threshold=silence_threshold, 
                                silence_duration=silence_duration, callback=callback)
            else:
                # Use voice-activated recording
                if "voice_activated" in record_audio.__name__:
                    record_audio(filename, fs=fs, silence_threshold=silence_threshold, 
                                silence_duration=silence_duration, callback=callback)
                else:
                    print("Using fixed duration recording (15 seconds) as fallback")
                    record_audio(filename, 15, fs, callback)
        except Exception as e:
            print(f"ERROR in recording thread: {e}")
        finally:
            # Always ensure recording is marked as not active
            recording_active = False
            print(f"Recording thread for {filename} completed, set recording_active to {recording_active}")
    
    thread = threading.Thread(target=record_thread)
    thread.daemon = True  # This ensures the thread will exit when the main program exits
    thread.start()
    print(f"Recording thread started, returning from record_audio_threaded")
    print("=== END STARTING RECORDING THREAD ===\n")
    return thread
