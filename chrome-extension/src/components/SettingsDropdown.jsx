// Settings dropdown component
import React from "react";
import { Settings, LogOut, Link2 } from "lucide-react";

export const SettingsDropdown = ({
  showSettings,
  setShowSettings,
  calendars,
  selectedCalendarId,
  loadingCalendars,
  onCalendarChange,
  onLogout,
  calendarProvider = "google",
  providers = {},
  onProviderChange,
  onConnectGoogle,
  onConnectMicrosoft,
  loadingAuth,
  loadingMicrosoftAuth,
}) => {
  if (!showSettings) return null;

  const providerLabel =
    calendarProvider === "microsoft" ? "Microsoft" : "Google";

  return (
    <div className="settings-dropdown">
      {(providers.google || providers.microsoft) && (
        <>
          <div className="settings-section">
            <label className="settings-label">Calendar account:</label>
            <select
              className="settings-calendar-select"
              value={calendarProvider}
              onChange={(e) => onProviderChange?.(e.target.value)}
            >
              {providers.google && <option value="google">Google</option>}
              {providers.microsoft && (
                <option value="microsoft">Microsoft</option>
              )}
            </select>
          </div>
          <div className="settings-divider"></div>
        </>
      )}
      <div className="settings-section">
        <label className="settings-label">{providerLabel} calendar:</label>
        <select
          className="settings-calendar-select"
          value={selectedCalendarId || ""}
          onChange={onCalendarChange}
          disabled={loadingCalendars}
        >
          {calendars.map((cal) => (
            <option key={cal.id} value={cal.id}>
              {cal.summary} {cal.primary ? "(Primary)" : ""}
            </option>
          ))}
        </select>
      </div>
      {!providers.google && (
        <>
          <div className="settings-divider"></div>
          <button
            className="settings-logout-button"
            disabled={loadingAuth || loadingMicrosoftAuth}
            onClick={() => {
              setShowSettings(false);
              onConnectGoogle?.();
            }}
          >
            <Link2 size={16} />
            Connect Google
          </button>
        </>
      )}
      {!providers.microsoft && (
        <>
          <div className="settings-divider"></div>
          <button
            className="settings-logout-button"
            disabled={loadingAuth || loadingMicrosoftAuth}
            onClick={() => {
              setShowSettings(false);
              onConnectMicrosoft?.();
            }}
          >
            <Link2 size={16} />
            Connect Microsoft
          </button>
        </>
      )}
      <div className="settings-divider"></div>
      <button
        className="settings-logout-button"
        onClick={() => {
          setShowSettings(false);
          onLogout();
        }}
      >
        <LogOut size={16} />
        Logout {providerLabel}
      </button>
    </div>
  );
};
