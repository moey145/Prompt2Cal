import { Link } from "react-router-dom";
import Icon from "../components/Icon";
import { AddToChrome } from "../components/SiteLayout";

// The popup images are made by chrome-extension/store-screenshots/capture.py
// from the extension's real components, so they match what users see.
const FEATURES = [
  {
    image: "/images/review.webp",
    alt: "The confirm card, with a guessed time highlighted and the end time marked as assumed",
    eyebrow: "Always in your control",
    title: "Nothing is added until you say so.",
    body: "Every event is shown for review first. Anything that wasn't in your text is highlighted, so a guessed time never slips in unnoticed.",
    points: [
      "Guessed details are highlighted",
      "Default end times are labelled as assumed",
      "Edit any field before creating",
    ],
  },
  {
    image: "/images/clash.webp",
    alt: "A clash warning listing the overlapping event and two nearby free times",
    eyebrow: "Clash check",
    title: "Catch clashes before they happen.",
    body: "Prompt2Cal checks your calendar as you go and offers the nearest free times, so moving an event takes one click.",
    points: [
      "Checks your Google or Outlook calendar",
      "Suggests free times either side",
      "Handles recurring events too",
    ],
  },
  {
    image: "/images/slots.webp",
    alt: "The free-time finder with length, range and hours, and open times grouped by day",
    eyebrow: "Find a free time",
    title: "Not sure when? Let it find a gap.",
    body: "Choose a length, how far ahead and which hours, and see the open times in your calendar. Pick one to start an event.",
    points: [
      "Any length, from 5 minutes to 12 hours",
      "Your own hours, with or without weekends",
      "Remembers your choices",
    ],
  },
  {
    image: "/images/rightclick.webp",
    alt: "Text selected in an email, with Add to calendar with Prompt2Cal in the right-click menu",
    eyebrow: "Right-click to add",
    title: "Add events from any page.",
    body: "Select the details in an email or website, right-click, and Prompt2Cal turns them into an event. It keeps working even if you close the popup.",
    points: [
      "Works on emails, chats and web pages",
      "Keeps parsing with the popup closed",
      "The toolbar badge shows when it's ready",
    ],
  },
];

const EXTRAS = [
  { icon: "mic", title: "Voice input", body: "Say your event instead of typing it." },
  {
    icon: "layers",
    title: "Several at once",
    body: "\"Coffee at 10am and dentist at 3pm\" becomes two events you can accept one by one.",
  },
  {
    icon: "repeat",
    title: "Recurring events",
    body: "\"Team meeting every Monday at 9am for 6 weeks\" becomes a single series.",
  },
  {
    icon: "pencil",
    title: "Edit anything first",
    body: "Add guests, a Google Meet or Teams link, a colour or category, and a reminder.",
  },
  {
    icon: "zap",
    title: "Keeps working when closed",
    body: "Close the popup mid-parse; the badge tells you when the event is ready.",
  },
  { icon: "moon", title: "Light and dark", body: "Switch themes from the popup to match your browser." },
];

const STEPS = [
  { icon: "sparkles", title: "Describe it", body: "Type, speak or right-click text on a page." },
  { icon: "eye", title: "Review it", body: "Check the details. Anything guessed is highlighted." },
  { icon: "pencil", title: "Adjust it", body: "Change a time, add guests or set a reminder." },
  { icon: "calendarCheck", title: "Add it", body: "Click Create Event and it's in your calendar." },
];

function CheckList({ points }) {
  return (
    <ul className="checklist">
      {points.map((point) => (
        <li key={point}>
          <span className="checklist-mark">
            <Icon name="check" size={14} strokeWidth={3} />
          </span>
          {point}
        </li>
      ))}
    </ul>
  );
}

function Home() {
  return (
    <>
      <section className="hero">
        <div className="section-inner hero-inner">
          <div className="hero-copy">
            <span className="eyebrow">Chrome extension for Google Calendar &amp; Outlook</span>
            <h1 className="hero-title">
              Type it the way you'd say it. <span className="accent">It's in your calendar.</span>
            </h1>
            <p className="hero-lead">
              Prompt2Cal turns plain-English plans into calendar events. Type, speak or right-click text on any page,
              check the details, and add it in one click.
            </p>
            <div className="hero-actions">
              <AddToChrome>
                Add to Chrome <span className="button-note">it's free</span>
              </AddToChrome>
              <Link className="button button-secondary" to="/#how-it-works">
                See how it works
              </Link>
            </div>
            <ul className="hero-facts">
              <li>
                <Icon name="check" size={16} strokeWidth={3} /> Google Calendar &amp; Outlook
              </li>
              <li>
                <Icon name="check" size={16} strokeWidth={3} /> Nothing added without your OK
              </li>
              <li>
                <Icon name="check" size={16} strokeWidth={3} /> Free
              </li>
            </ul>
          </div>
          <div className="hero-visual">
            <img
              src="/images/input.webp"
              alt="The Prompt2Cal popup turning that sentence into an event for Thursday at 7pm at Nando's"
              width="552"
              height="838"
            />
          </div>
        </div>
      </section>

      <section className="section" id="features">
        <div className="section-inner">
          <div className="section-head">
            <span className="eyebrow">Features</span>
            <h2>Everything between a message and your calendar.</h2>
            <p>From a quick note to a week of plans, Prompt2Cal reads it, checks it against your calendar and lets you decide.</p>
          </div>

          {FEATURES.map((feature, index) => (
            <div className={`feature-row ${index % 2 ? "is-flipped" : ""}`} key={feature.title}>
              <div className="feature-copy">
                <span className="eyebrow">{feature.eyebrow}</span>
                <h3>{feature.title}</h3>
                <p>{feature.body}</p>
                <CheckList points={feature.points} />
              </div>
              <div className="feature-visual">
                <img src={feature.image} alt={feature.alt} loading="lazy" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section section-tint">
        <div className="section-inner">
          <div className="section-head">
            <span className="eyebrow">And the little things</span>
            <h2>Made for how people actually write plans.</h2>
          </div>
          <div className="card-grid">
            {EXTRAS.map((extra) => (
              <div className="card" key={extra.title}>
                <span className="card-icon">
                  <Icon name={extra.icon} size={22} />
                </span>
                <h3>{extra.title}</h3>
                <p>{extra.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="how-it-works">
        <div className="section-inner">
          <div className="section-head">
            <span className="eyebrow">How it works</span>
            <h2>From a sentence to an event, in four steps.</h2>
          </div>
          <ol className="steps">
            {STEPS.map((step, index) => (
              <li className="step" key={step.title}>
                <span className="step-icon">
                  <Icon name={step.icon} size={22} />
                  <span className="step-number">{index + 1}</span>
                </span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="section-inner">
          <div className="cta-band">
            <div>
              <h2>Stop clicking through calendar forms.</h2>
              <p>Add Prompt2Cal to Chrome and type your next plan the way you'd say it.</p>
            </div>
            <div className="cta-band-actions">
              <AddToChrome />
              <Link className="button button-ghost" to="/support">
                Get help
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default Home;
