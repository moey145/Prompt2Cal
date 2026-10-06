import { useState } from "react";
import { Link } from "react-router-dom";
import Icon from "../components/Icon";
import { AddToChrome } from "../components/SiteLayout";

// The popup images are made by chrome-extension/store-screenshots/capture.py
// from the extension's real components, so they match what users see.
const SHOWCASE = [
  {
    icon: "eye",
    title: "Review before it's added",
    body: "Every event is shown to you first. Anything that wasn't in your text, like a guessed time, is highlighted.",
    image: "/images/review.webp",
    alt: "The confirm card, with a guessed time highlighted and the end time marked as assumed",
  },
  {
    icon: "warning",
    title: "Catch clashes",
    body: "Prompt2Cal checks your calendar as you go and offers the nearest free times, so moving an event is one click.",
    image: "/images/clash.webp",
    alt: "A clash warning listing the overlapping event and two nearby free times",
  },
  {
    icon: "calendarSearch",
    title: "Find a free time",
    body: "Pick a length, how far ahead and which hours, and see the open slots in your calendar.",
    image: "/images/slots.webp",
    alt: "The free-time finder with length, range and hours, and open times grouped by day",
  },
  {
    icon: "mousePointer",
    title: "Right-click any page",
    body: "Select the details in an email or website and add them from the right-click menu, even with the popup closed.",
    image: "/images/rightclick.webp",
    alt: "Text selected in an email, with Add to calendar with Prompt2Cal in the right-click menu",
  },
];

const EXTRAS = [
  { icon: "mic", title: "Voice input", body: "Say your event instead of typing it." },
  { icon: "layers", title: "Several at once", body: "\"Coffee at 10am and dentist at 3pm\" becomes two events." },
  { icon: "repeat", title: "Recurring events", body: "\"Every Monday at 9am for 6 weeks\" becomes one series." },
  { icon: "pencil", title: "Edit anything first", body: "Guests, a Meet or Teams link, colours and reminders." },
  { icon: "zap", title: "Works in the background", body: "Close the popup; the badge says when it's ready." },
  { icon: "moon", title: "Light and dark", body: "Switch themes to match your browser." },
];

function Showcase() {
  const [active, setActive] = useState(0);

  return (
    <div className="showcase">
      <div className="showcase-tabs" role="tablist" aria-label="Features">
        {SHOWCASE.map((item, index) => (
          <button
            key={item.title}
            type="button"
            role="tab"
            id={`showcase-tab-${index}`}
            aria-selected={active === index}
            aria-controls="showcase-panel"
            className={`showcase-tab ${active === index ? "is-active" : ""}`}
            onClick={() => setActive(index)}
          >
            <span className="card-icon">
              <Icon name={item.icon} size={20} />
            </span>
            <span>
              <span className="showcase-tab-title">{item.title}</span>
              <span className="showcase-tab-body">{item.body}</span>
            </span>
          </button>
        ))}
      </div>
      <div className="showcase-stage" id="showcase-panel" role="tabpanel" aria-labelledby={`showcase-tab-${active}`}>
        {/* All four stay loaded so switching tabs never waits for an image. */}
        {SHOWCASE.map((item, index) => (
          <img
            key={item.image}
            src={item.image}
            alt={active === index ? item.alt : ""}
            aria-hidden={active !== index}
            className={active === index ? "is-active" : ""}
          />
        ))}
      </div>
    </div>
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
              Plans in plain English. <span className="accent">Events in your calendar.</span>
            </h1>
            <p className="hero-lead">
              Type, speak or right-click something like "dinner with Sarah next Thursday at 7pm". Prompt2Cal fills in the
              details, you check them, and it's added in one click.
            </p>
            <div className="hero-actions">
              <AddToChrome>
                Add to Chrome <span className="button-note">it's free</span>
              </AddToChrome>
              <Link className="button button-secondary" to="/#features">
                See what it does
              </Link>
            </div>
            <ul className="hero-facts">
              <li>
                <Icon name="check" size={16} strokeWidth={3} /> Google Calendar &amp; Outlook
              </li>
              <li>
                <Icon name="check" size={16} strokeWidth={3} /> Nothing added without your OK
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
          </div>
          <Showcase />
        </div>
      </section>

      <section className="section section-tint">
        <div className="section-inner">
          <div className="extras">
            {EXTRAS.map((extra) => (
              <div className="extra" key={extra.title}>
                <span className="card-icon">
                  <Icon name={extra.icon} size={20} />
                </span>
                <div>
                  <h3>{extra.title}</h3>
                  <p>{extra.body}</p>
                </div>
              </div>
            ))}
          </div>
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
