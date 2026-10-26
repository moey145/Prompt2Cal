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
import { EditEventModal } from "../src/components/EditEventModal";
import { Toast } from "../src/components/Toast";

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
// The first three weekdays from today, as day offsets: the free-time sample
// leaves weekends out, as the slot finder does by default.
const WEEKDAYS = [];
for (let offset = 0; WEEKDAYS.length < 3; offset += 1) {
  const day = new Date();
  day.setDate(day.getDate() + offset);
  if (day.getDay() !== 0 && day.getDay() !== 6) WEEKDAYS.push(offset);
}

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

// What each screen shows; the site reuses these on their own (site-* below).
const VISUALS = {
  input: () => (
    <Popup>
      <Input text="Dinner with Sarah next Thursday at 7pm to 8pm at Nando's" />
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
  ),

  review: () => (
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
  ),

  clash: () => (
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
  ),

  slots: () => (
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
            start: at(WEEKDAYS[day], hour, minute),
            end: at(WEEKDAYS[day], hour + 1, minute),
            formatted_start: "",
          })),
        ]}
      />
    </Popup>
  ),

  rightclick: () => (
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
  ),
};

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
      {VISUALS.input()}
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
      {VISUALS.review()}
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
      {VISUALS.clash()}
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
      {VISUALS.slots()}
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
      {VISUALS.rightclick()}
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

// Capstone report: Figure 7 (core scenarios) and Figure 8 (extended
// scenarios), each a grid of panels on white, cropped by capture.py. Each
// panel is one user scenario: a title, then what the user does and gets, with
// the user stories from Table 13 it satisfies.
const Panel = ({ label, detail, wide = false, hero = false, children }) => (
  <div className={`report-panel ${wide ? "report-wide" : ""} ${hero ? "" : "no-hero"}`}>
    <div className="report-label">
      {label}
      {detail && <span className="report-detail">{detail}</span>}
    </div>
    {children}
  </div>
);

const ReportFigure = ({ children }) => {
  document.documentElement.classList.add("report-image");
  return <div className="report-figure">{children}</div>;
};

// Real screenshots of the created events, for Figure 9: saved beside this file
// as calendar-event-google.png and calendar-event-outlook.png. A missing one
// leaves its panel out.
const CALENDAR_SHOTS = import.meta.glob("./calendar-event-*.png", {
  eager: true,
  query: "?url",
  import: "default",
});
const calendarShot = (provider) => CALENDAR_SHOTS[`./calendar-event-${provider}.png`];

const NO_EVENT_MESSAGE =
  "Couldn't find an event in that text. Try saying what it is and when, like \"Lunch with Sam on Friday at 1pm\".";

SCREENS["report-fig7"] = () => (
  <ReportFigure>
    <Panel
      label="(a) Scenario 1, a clear request"
      detail="“Dinner with Sarah next Thursday at 7pm to 8pm at Nando's” gives a preview ready to create (US-01, US-02)"
    >
      {VISUALS.input()}
    </Panel>
    <Panel
      label="(b) Scenario 2, missing details"
      detail="“Coffee with Alex on Friday” gives a guessed time highlighted and the end time assumed (US-03, US-04)"
    >
      {VISUALS.review()}
    </Panel>
    <Panel
      label="(c) Scenario 3, correcting before creating"
      detail="The user fixes the details in the edit dialog (US-05)"
    >
      <EditEventModal
        event={{
          title: "Coffee with Alex",
          start_time: at(friday, 10),
          end_time: at(friday, 11),
          location: "Cafe on George St",
          recurrence_type: "none",
        }}
        attendees={["alex@example.com"]}
        attendeeInput=""
        setAttendeeInput={noop}
        onAddAttendee={noop}
        onRemoveAttendee={noop}
        selectedColor="#039be5"
        setSelectedColor={noop}
        selectedReminder="15"
        setSelectedReminder={noop}
        onFieldChange={noop}
        onSave={noop}
        onCancel={noop}
        loading={false}
        calendarProvider="google"
        categories={[]}
      />
    </Panel>
    <Panel
      label="(d) Scenario 4, no event in the text"
      detail="“hmm, not sure yet” gives a message, and nothing is added (US-11)"
    >
      <Popup>
        <Input text="hmm, not sure yet" />
        <div className="report-toast">
          <Toast id={1} type="error" message={NO_EVENT_MESSAGE} onClose={noop} />
        </div>
      </Popup>
    </Panel>
  </ReportFigure>
);

SCREENS["report-fig8"] = () => (
  <ReportFigure>
    <Panel
      label="(a) Scenario 5, adding from an email"
      detail="Select the text, right-click, and the badge shows when it is ready (US-10)"
      wide
    >
      {VISUALS.rightclick()}
    </Panel>
    <Panel
      label="(b) Scenario 6, a clash with an existing event"
      detail="The warning offers the nearest free times (US-12)"
    >
      {VISUALS.clash()}
    </Panel>
    <Panel
      label="(c) Scenario 7, finding a time first"
      detail="Pick an open slot, and the editor opens with that time filled in (US-13)"
    >
      {VISUALS.slots()}
    </Panel>
  </ReportFigure>
);

// For prompt2cal.com: each visual alone on a transparent page, cropped by
// capture.py.
Object.keys(VISUALS).forEach((key) => {
  SCREENS[`site-${key}`] = () => {
    document.documentElement.classList.add("site-image");
    return <div className="site-visual">{VISUALS[key]()}</div>;
  };
});

// Figure 9: the end of the flow: the extension's confirmation, then the created
// events in each calendar.
SCREENS["report-fig9"] = () => {
  const shots = [
    ["google", "Google Calendar", "Scenario 1's dinner"],
    ["outlook", "Outlook", "Scenario 5's lunch"],
  ].filter(([provider]) => calendarShot(provider));
  return (
    <ReportFigure>
      <Panel
        label="(a) Confirming the event"
        detail="Create Event adds it to the user's calendar, and View Event opens it there (US-02)"
      >
        <Popup>
          <Input text="" />
          <div className="report-toast">
            <Toast id={2} type="success" message="Event created!" link="#" onClose={noop} />
          </div>
        </Popup>
      </Panel>
      {shots.map(([provider, name, scenario], index) => (
        <Panel
          key={provider}
          label={`(${"bc"[index]}) The event in ${name}`}
          detail={`${scenario}, as created (R7)`}
        >
          <img className="report-shot" src={calendarShot(provider)} alt="" />
        </Panel>
      ))}
    </ReportFigure>
  );
};

const screen = SCREENS[window.location.hash.slice(1)] || SCREENS[1];
ReactDOM.createRoot(document.getElementById("root")).render(screen());
