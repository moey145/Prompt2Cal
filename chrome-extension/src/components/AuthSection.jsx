// Authentication section component
import React from "react";
import { Calendar } from "lucide-react";

export const AuthSection = ({
  onGoogleAuth,
  onMicrosoftAuth,
  loadingAuth,
  loadingMicrosoftAuth,
}) => {
  return (
    <div className="auth-section" id="authSection">
      <button
        id="authButton"
        className="auth-button"
        onClick={onGoogleAuth}
        disabled={loadingAuth || loadingMicrosoftAuth}
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
      <button
        id="microsoftAuthButton"
        className="auth-button auth-button-microsoft"
        onClick={onMicrosoftAuth}
        disabled={loadingAuth || loadingMicrosoftAuth}
      >
        {loadingMicrosoftAuth ? (
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
            <Calendar size={18} /> Connect Microsoft Calendar
          </>
        )}
      </button>
    </div>
  );
};
