"""Speech recognition client for MoveMend dashboard."""

import speech_recognition as sr
import threading
import queue
import time
from typing import Optional, Callable, Dict, List, Any, Tuple

class SpeechRecognitionClient:
    """Client for processing speech input from the microphone."""
    
    def __init__(self):
        """Initialize the speech recognition client."""
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.listen_thread = None
        self.process_thread = None
        
        # Adjust for ambient noise for better recognition
        self.energy_threshold = 300  # Default value
        self.dynamic_energy_threshold = True
        
        # Configure the recognizer
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
        self.recognizer.pause_threshold = 0.8  # Shorter pause for more responsive detection
        
    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Start listening for speech input.
        
        Args:
            callback: Optional callback function to call when speech is recognized.
                     The callback function should accept a string parameter.
        """
        if self.is_listening:
            return  # Already listening
            
        self.is_listening = True
        
        # Start the listening thread
        self.listen_thread = threading.Thread(
            target=self._listen_microphone,
            args=(callback,),
            daemon=True
        )
        self.listen_thread.start()
        
        # Start the processing thread
        self.process_thread = threading.Thread(
            target=self._process_audio,
            args=(callback,),
            daemon=True
        )
        self.process_thread.start()
        
    def stop_listening(self):
        """Stop listening for speech input."""
        self.is_listening = False
        
        # Wait for threads to terminate
        if self.listen_thread:
            self.listen_thread.join(timeout=1.0)
            self.listen_thread = None
            
        if self.process_thread:
            self.process_thread.join(timeout=1.0)
            self.process_thread = None
            
    def _listen_microphone(self, callback: Optional[Callable[[str], None]] = None):
        """Listen to the microphone and add audio data to the queue."""
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise once at the start
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"Energy threshold set to {self.recognizer.energy_threshold}")
                
                # Continue listening until told to stop
                while self.is_listening:
                    try:
                        print("Listening for speech...")
                        audio = self.recognizer.listen(source, timeout=10.0, phrase_time_limit=10.0)
                        self.audio_queue.put(audio)
                        print("Audio captured, added to queue for processing")
                    except sr.WaitTimeoutError:
                        print("No speech detected in timeout period, continuing to listen...")
                        continue
        except Exception as e:
            print(f"Error in microphone listening: {e}")
            if callback:
                callback(f"Error listening: {str(e)}")
            
    def _process_audio(self, callback: Optional[Callable[[str], None]] = None):
        """Process audio data from the queue and convert to text."""
        while self.is_listening:
            try:
                # Get audio from the queue (with timeout to check is_listening)
                try:
                    audio = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                print("Processing audio to text...")
                
                # Try to recognize the speech
                try:
                    # First try using Google (requires internet)
                    text = self.recognizer.recognize_google(audio)
                    print(f"Google recognized: {text}")
                except sr.RequestError:
                    # If Google fails, try Sphinx (offline, less accurate)
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                        print(f"Sphinx recognized: {text}")
                    except (sr.UnknownValueError, sr.RequestError) as e:
                        print(f"Sphinx recognition error: {e}")
                        text = ""
                except sr.UnknownValueError:
                    print("Could not understand audio")
                    text = ""
                
                # If we have text, add it to the queue and trigger callback
                if text:
                    self.text_queue.put(text)
                    if callback:
                        callback(text)
                        
            except Exception as e:
                print(f"Error processing audio: {e}")
                if callback:
                    callback(f"Error processing: {str(e)}")
                    
    def get_recognized_text(self) -> str:
        """Get the next recognized text from the queue if available.
        
        Returns:
            The recognized text, or an empty string if no text is available.
        """
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return ""

# Create a singleton instance
speech_recognition_client = SpeechRecognitionClient()
