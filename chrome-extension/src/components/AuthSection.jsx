// Authentication section component
import React from "react";
import { Calendar } from "lucide-react";

export const AuthSection = ({ onAuth, loadingAuth }) => {
  return (
    <div className="auth-section" id="authSection">
      <button
        id="authButton"
        className="auth-button"
        onClick={onAuth}
        disabled={loadingAuth}
      >
        {loadingAuth ? (
          <>
            <div className="dots-spinner">
              <div></div>
              <div></div>
              <div></div>
              <div></div>
            </div>{" "}
            Connecting...
          </>
        ) : (
          <>
            <Calendar size={18} /> Connect Google Calendar
          </>
        )}
      </button>
    </div>
  );
};

