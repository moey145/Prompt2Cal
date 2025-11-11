// Voice recognition hook
import { useState, useRef } from "react";

export const useVoiceRecognition = () => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const originalTextRef = useRef("");
  const silenceTimeoutRef = useRef(null);
  const setEventInputRef = useRef(null);

  const startVoiceRecognition = (currentInput) => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      originalTextRef.current = currentInput || "";
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        const newText =
          originalTextRef.current +
          (originalTextRef.current ? " " : "") +
          finalTranscript.trim();
        if (setEventInputRef.current) {
          setEventInputRef.current(newText);
        }
        originalTextRef.current = newText;

        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = setTimeout(() => {
          stopVoiceRecognition();
        }, 2000);
      } else if (interimTranscript) {
        const newText =
          originalTextRef.current +
          (originalTextRef.current ? " " : "") +
          interimTranscript.trim();
        if (setEventInputRef.current) {
          setEventInputRef.current(newText);
        }

        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = setTimeout(() => {
          stopVoiceRecognition();
        }, 2000);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }

      let errorMessage = "Voice recognition error";
      switch (event.error) {
        case "no-speech":
          errorMessage = "No speech detected. Please try again.";
          break;
        case "audio-capture":
          errorMessage = "No microphone found. Please check your microphone.";
          break;
        case "not-allowed":
          errorMessage =
            "Microphone permission denied. Please allow microphone access.";
          break;
        case "network":
          errorMessage = "Network error. Please check your connection.";
          break;
        case "aborted":
          return;
        default:
          errorMessage = `Voice recognition error: ${event.error}`;
      }

      throw new Error(errorMessage);
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const stopVoiceRecognition = () => {
    if (recognitionRef.current) {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Recognition might already be stopped
      }
      setIsListening(false);
    }
  };

  const toggleVoiceRecognition = async (currentInput, setEventInput) => {
    if (
      !("webkitSpeechRecognition" in window || "SpeechRecognition" in window)
    ) {
      throw new Error("Voice recognition not supported");
    }

    if (isListening) {
      stopVoiceRecognition();
    } else {
      setEventInputRef.current = setEventInput;
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        stream.getTracks().forEach((track) => track.stop());
        startVoiceRecognition(currentInput);
      } catch (error) {
        throw new Error(
          "Microphone permission denied. Please allow microphone access in your browser settings."
        );
      }
    }
  };

  return {
    isListening,
    toggleVoiceRecognition,
    stopVoiceRecognition,
  };
};

