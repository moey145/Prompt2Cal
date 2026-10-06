// Chrome Web Store screenshots, built from the extension's real components
// with sample data. Each screen is chosen by the URL hash (#1 to #5); see
// capture.py, which photographs them at 1280x800.
import React from "react";
import ReactDOM from "react-dom/client";
import {
  CalendarSearch,
  Check,
  Copy,
  Globe,
  MousePointerClick,
  Settings,
  Sun,
} from "lucide-react";
import "../src/index.css";
import "./screens.css";
import logoUrl from "../icons/Logo.svg";
import { EventInputSection } from "../src/components/EventInputSection";
import { SingleEventCard } from "../src/components/SingleEventCard";
import { FindSlotPanel } from "../src/components/FindSlotPanel";

// The components read a few chrome.* APIs; these stand-ins return the saved
// slot-finder choices the screenshots show.
window.chrome = {
  storage: {
    local: {
      get: async () => ({
        prompt2cal_slot_hours: [9, 17],
        prompt2cal_slot_prefs: { durationMinutes: 60, days: 3, includeWeekends: false },
      }),
      set: async () => {},
    },
  },
  runtime: { getURL: (path) => path },
};

const noop = () => {};

/** A local date `dayOffset` days from today at the given time, as ISO. */
const at = (dayOffset, hour, minute = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + dayOffset);
  date.setHours(hour, minute, 0, 0);
  return date.toISOString();
};

/** Days until the next given weekday (0 = Sunday), at least 2 days out. */
const daysUntil = (weekday) => {
  const today = new Date().getDay();
  let days = (weekday - today + 7) % 7;
  if (days < 2) days += 7;
  return days;
};

const PopupHeader = ({ slotFinderActive = false }) => (
  <div className="header">
    <div className="header-left">
      <div className="settings-container">
        <button className="settings-button" type="button">
          <Settings size={18} />
        </button>
      </div>
      <button type="button" className={`settings-button ${slotFinderActive ? "active" : ""}`}>
        <CalendarSearch size={18} />
      </button>
    </div>
    <button className="theme-toggle" type="button">
      <Sun size={20} />
    </button>
    <div className="hero">
      <div className="hero-icon">
        <img src={logoUrl} alt="" className="logo-image" />
      </div>
      <h1 className="logo">
        <span className="logo-black">Prompt2</span>
        <span className="logo-red">Cal</span>
      </h1>
      <div className="tagline">Turn natural language into calendar events instantly</div>
    </div>
  </div>
);

const Popup = ({ children, slotFinderActive }) => (
  <div className="shot-popup">
    <div className="container">
      <PopupHeader slotFinderActive={slotFinderActive} />
      <div className="main-section">{children}</div>
    </div>
  </div>
);

const Input = ({ text }) => (
  <EventInputSection
    eventInput={text}
    setEventInput={noop}
    onParse={noop}
    isListening={false}
    onToggleVoice={noop}
    loadingSingle={false}
    showSelectedText={false}
  />
);

const Card = (props) => (
  <SingleEventCard onEdit={noop} onCreate={noop} onCancel={noop} calendarProvider="google" {...props} />
);

const ShotCopy = ({ eyebrow, title, body, points }) => (
  <div className="shot-copy">
    <div className="shot-eyebrow">{eyebrow}</div>
    <h1 className="shot-title">{title}</h1>
    <p className="shot-body">{body}</p>
    <ul className="shot-points">
      {points.map((point) => (
        <li key={point}>
          <span className="shot-check">
            <Check size={14} strokeWidth={3} />
          </span>
          {point}
        </li>
      ))}
    </ul>
  </div>
);

const Shot = ({ copy, children }) => (
  <div className="shot">
    <ShotCopy {...copy} />
    <div className="shot-visual">{children}</div>
  </div>
);

const thursday = daysUntil(4);
const friday = daysUntil(5);
const wednesday = daysUntil(3);

const SCREENS = {
  1: () => (
    <Shot
      copy={{
        eyebrow: "Prompt2Cal",
        title: "Type it the way you'd say it.",
        body: "Describe any plan in plain English and it becomes a calendar event, ready to review.",
        points: [
          "Works with Google Calendar and Outlook",
          "Understands typos, voice and casual phrasing",
          "Several events from one message",
        ],
      }}
    >
      <Popup>
        <Input text="Dinner with Sarah next Thursday at 7pm at Nando's" />
        <Card
          parsedEvent={{
            title: "Dinner with Sarah",
            start_time: at(thursday, 19),
            end_time: at(thursday, 20),
            location: "Nando's",
            recurrence_type: "none",
          }}
        />
      </Popup>
    </Shot>
  ),

  2: () => (
    <Shot
      copy={{
        eyebrow: "Always in your control",
        title: "Nothing is added until you say so.",
        body: "Every event is shown for review first. Anything that wasn't in your text is highlighted, so a guessed time never slips in unnoticed.",
        points: [
          "Guessed details are highlighted",
          "Default end times are labelled as assumed",
          "Edit any field before creating",
        ],
      }}
    >
      <Popup>
        <Input text="Coffee with Alex on Friday" />
        <Card
          parsedEvent={{
            title: "Coffee with Alex",
            start_time: at(friday, 10),
            end_time: at(friday, 11),
            end_time_assumed: true,
            recurrence_type: "none",
            field_confidence: { title: "grounded", start_time: "ungrounded", end_time: "ungrounded" },
          }}
        />
      </Popup>
    </Shot>
  ),

  3: () => (
    <Shot
      copy={{
        eyebrow: "Clash check",
        title: "Catch clashes before they happen.",
        body: "Prompt2Cal checks your calendar as you go and offers the nearest free times, so moving an event takes one click.",
        points: [
          "Checks your Google or Outlook calendar",
          "Suggests free times either side",
          "Handles recurring events too",
        ],
      }}
    >
      <Popup>
        <Card
          parsedEvent={{
            title: "Team planning session",
            start_time: at(wednesday, 14),
            end_time: at(wednesday, 15),
            location: "Level 3 meeting room",
            recurrence_type: "none",
          }}
          conflicts={[
            {
              title: "Client call with Northwind",
              start: at(wednesday, 14, 30),
              end: at(wednesday, 15),
            },
          ]}
          alternatives={[
            { start: at(wednesday, 12, 45), formatted_time: "12:45 PM - 1:45 PM" },
            { start: at(wednesday, 15, 15), formatted_time: "3:15 PM - 4:15 PM" },
          ]}
        />
      </Popup>
    </Shot>
  ),

  4: () => (
    <Shot
      copy={{
        eyebrow: "Find a free time",
        title: "Not sure when? Let it find a gap.",
        body: "Choose a length, how far ahead and which hours, and see the open times in your calendar. Pick one to start an event.",
        points: [
          "Any length, from 5 minutes to 12 hours",
          "Your own hours, with or without weekends",
          "Remembers your choices",
        ],
      }}
    >
      <Popup slotFinderActive>
        <FindSlotPanel
          onClose={noop}
          onPickSlot={noop}
          onFindSlots={async () => [
            ...[
              [0, 13],
              [0, 15, 30],
              [1, 9],
              [1, 10, 30],
              [1, 13],
              [1, 14, 30],
              [1, 16],
              [2, 9, 30],
              [2, 11],
              [2, 15],
            ].map(([day, hour, minute = 0]) => ({
              start: at(day, hour, minute),
              end: at(day, hour + 1, minute),
              formatted_start: "",
            })),
          ]}
        />
      </Popup>
    </Shot>
  ),

  5: () => (
    <Shot
      copy={{
        eyebrow: "Right-click to add",
        title: "Add events from any page.",
        body: "Select the details in an email or website, right-click, and Prompt2Cal turns them into an event. It keeps working even if you close the popup.",
        points: [
          "Works on emails, chats and web pages",
          "Keeps parsing with the popup closed",
          "The toolbar badge shows when it's ready",
        ],
      }}
    >
      <div className="shot-browser">
        <div className="shot-browser-bar">
          <span className="shot-dot" />
          <span className="shot-dot" />
          <span className="shot-dot" />
          <div className="shot-address">mail.example.com/inbox</div>
          <div className="shot-toolbar-icon">
            <img src={logoUrl} alt="" />
            <span className="shot-badge">1</span>
          </div>
        </div>
        <div className="shot-email">
          <div className="shot-email-subject">Catch-up next week?</div>
          <div className="shot-email-from">
            <span className="shot-avatar">J</span>
            <div>
              <strong>Jess Taylor</strong>
              <span>to me</span>
            </div>
          </div>
          <p>Hey! It's been ages since we properly caught up.</p>
          <p>
            <span className="shot-selected">
              Lunch next Wednesday at 12:30 at The Grounds of Alexandria?
            </span>{" "}
            Let me know if that works for you.
          </p>
          <p>Jess</p>
          <div className="shot-menu">
            <div className="shot-menu-item">
              <Copy size={15} /> Copy
            </div>
            <div className="shot-menu-item">
              <Globe size={15} /> Search Google for "Lunch next Wed…"
            </div>
            <div className="shot-menu-divider" />
            <div className="shot-menu-item shot-menu-item-active">
              <img src={logoUrl} alt="" /> Add to calendar with Prompt2Cal
            </div>
            <div className="shot-menu-divider" />
            <div className="shot-menu-item">
              <MousePointerClick size={15} /> Inspect
            </div>
          </div>
        </div>
      </div>
    </Shot>
  ),
};

const Wordmark = () => (
  <div className="tile-wordmark">
    <img src={logoUrl} alt="" />
    <span className="logo">
      <span className="logo-black">Prompt2</span>
      <span className="logo-red">Cal</span>
    </span>
  </div>
);

// Promo tiles: the small one is shown when the store features or lists the
// extension, so it stays simple; the marquee is the wide banner.
SCREENS.small = () => (
  <div className="tile tile-small">
    <Wordmark />
    <div className="tile-small-line">Turn plain English into calendar events.</div>
    <div className="tile-chips">
      <span>Google Calendar</span>
      <span>Outlook</span>
    </div>
  </div>
);

SCREENS.marquee = () => (
  <div className="tile tile-marquee">
    <div className="tile-marquee-copy">
      <Wordmark />
      <h1 className="tile-marquee-title">Type it the way you'd say it. Review it. Done.</h1>
      <div className="tile-chips">
        <span>Google Calendar</span>
        <span>Outlook</span>
        <span>Right-click any page</span>
      </div>
    </div>
    <div className="tile-marquee-card">
      <Card
        parsedEvent={{
          title: "Dinner with Sarah",
          start_time: at(thursday, 19),
          end_time: at(thursday, 20),
          location: "Nando's",
          recurrence_type: "none",
        }}
      />
    </div>
  </div>
);

const screen = SCREENS[window.location.hash.slice(1)] || SCREENS[1];
ReactDOM.createRoot(document.getElementById("root")).render(screen());

