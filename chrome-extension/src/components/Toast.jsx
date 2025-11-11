// Toast notification component
import React, { useEffect, useRef, useState } from "react";
import { CheckCircle, XCircle, Info, X } from "lucide-react";

export const Toast = ({ message, type, onClose, id, link }) => {
  const DURATION_MS = 5000;
  const [paused, setPaused] = useState(false);
  const startTimeRef = useRef(Date.now());
  const remainingRef = useRef(DURATION_MS);
  const timeoutRef = useRef(null);

  const clearTimer = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const startTimer = (ms) => {
    clearTimer();
    startTimeRef.current = Date.now();
    timeoutRef.current = setTimeout(() => onClose(id), ms);
  };

  useEffect(() => {
    // Start initial timer
    startTimer(remainingRef.current);
    return () => clearTimer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, onClose]);

  const handleMouseEnter = () => {
    // Pause timer and progress
    const elapsed = Date.now() - startTimeRef.current;
    remainingRef.current = Math.max(0, remainingRef.current - elapsed);
    clearTimer();
    setPaused(true);
  };

  const handleMouseLeave = () => {
    // Resume timer with remaining time
    setPaused(false);
    startTimer(remainingRef.current);
  };

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle size={18} />;
      case "error":
        return <XCircle size={18} />;
      default:
        return <Info size={18} />;
    }
  };

  // Parse message to extract link if it contains "View: [url]"
  const renderMessage = () => {
    if (link) {
      return (
        <>
          {message.replace(/View:.*$/, "").trim()}
          {" "}
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="toast-link"
            onClick={(e) => e.stopPropagation()}
          >
            View Event
          </a>
        </>
      );
    }
    return message;
  };

  return (
    <div
      className={`toast toast-${type} ${paused ? "paused" : ""}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="toast-content">
        <div className="toast-icon">{getIcon()}</div>
        <div className="toast-message">{renderMessage()}</div>
        <button className="toast-close" onClick={() => onClose(id)}>
          <X size={16} />
        </button>
      </div>
      <div className="toast-progress-bar">
        <div className="toast-progress-fill"></div>
      </div>
    </div>
  );
};

export const ToastContainer = ({ toasts, onClose }) => {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          id={toast.id}
          message={toast.message}
          type={toast.type}
          link={toast.link}
          onClose={onClose}
        />
      ))}
    </div>
  );
};

