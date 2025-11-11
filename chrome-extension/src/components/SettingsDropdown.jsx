// Settings dropdown component
import React from "react";
import { Settings, LogOut } from "lucide-react";

export const SettingsDropdown = ({
  showSettings,
  setShowSettings,
  calendars,
  selectedCalendarId,
  loadingCalendars,
  onCalendarChange,
  onLogout,
}) => {
  if (!showSettings) return null;

  return (
    <div className="settings-dropdown">
      <div className="settings-section">
        <label className="settings-label">Calendar:</label>
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
      <div className="settings-divider"></div>
      <button
        className="settings-logout-button"
        onClick={() => {
          setShowSettings(false);
          onLogout();
        }}
      >
        <LogOut size={16} />
        Logout
      </button>
    </div>
  );
};

