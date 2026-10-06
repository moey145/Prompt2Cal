import { Link } from "react-router-dom";
import Icon from "../components/Icon";
import { GITHUB_ISSUES_URL, SUPPORT_EMAIL } from "../links";

// Each answer describes the extension as it is; keep them in step with it.
const TOPICS = [
  {
    id: "getting-started",
    icon: "play",
    title: "Getting started",
    questions: [
      {
        q: "How do I connect my calendar?",
        a: (
          <>
            Click the Prompt2Cal icon in Chrome's toolbar, then choose <strong>Sign in with Google</strong> or{" "}
            <strong>Sign in with Microsoft</strong> and approve access in the window that opens. You can connect both and
            switch between them, and pick which calendar events go to, from the <strong>Settings</strong> (gear) menu.
          </>
        ),
      },
      {
        q: "Which calendars does it work with?",
        a: "Google Calendar, and Outlook through a Microsoft account. Events go to the calendar you choose in Settings.",
      },
      {
        q: "How do I add an event from a web page or email?",
        a: (
          <>
            Select the text with the details, right-click it and choose{" "}
            <strong>Add to calendar with Prompt2Cal</strong>. The toolbar icon shows a grey dot while it reads the text,
            a green <strong>1</strong> when the event is ready and a red <strong>!</strong> if something went wrong.
            Click the icon to review it.
          </>
        ),
      },
      {
        q: "Can I add several events at once?",
        a: "Yes. Write them in one message, such as \"Coffee at 10am and dentist at 3pm\", and each one is listed separately so you can keep or remove it before creating.",
      },
    ],
  },
  {
    id: "using",
    icon: "sparkles",
    title: "Using Prompt2Cal",
    questions: [
      {
        q: "Why are some details highlighted?",
        a: "Highlighted details weren't in your text, so Prompt2Cal filled them in, such as a time when you only gave a day. An end time marked \"assumed\" is the default one-hour length. Check them, or click the pencil to change them, before you create the event.",
      },
      {
        q: "What does Find a free time do?",
        a: "Click the calendar icon beside the gear. Choose a length, how far ahead to look and which hours, and Prompt2Cal lists the open times in your calendar, keeping 15 minutes clear around existing events. Weekends are left out unless you tick Include weekends. Click a time to start an event there.",
      },
      {
        q: "Can I close the popup while it's working?",
        a: "Yes. Reading the event carries on in the background, and the preview is waiting when you open the popup again. A preview you haven't created or cancelled is also kept for 12 hours.",
      },
      {
        q: "Does it cost anything?",
        a: "No, Prompt2Cal is free.",
      },
    ],
  },
  {
    id: "troubleshooting",
    icon: "wrench",
    title: "Troubleshooting",
    questions: [
      {
        q: "It says \"Couldn't find an event in that text\".",
        a: "Prompt2Cal needs to know what the event is and roughly when. Add both, for example \"Lunch with Sam on Friday at 1pm\", and try again.",
      },
      {
        q: "It says \"The event reader isn't available right now\".",
        a: "The service that reads your text couldn't be reached. This is usually brief, so wait a minute and try again.",
      },
      {
        q: "The right-click option doesn't appear.",
        a: "Make sure you've selected some text first; the option only appears when you right-click a selection. Chrome doesn't allow extensions on its own pages (those starting with chrome://) or on the Chrome Web Store. If you've just installed or updated Prompt2Cal, restart Chrome.",
      },
      {
        q: "It asks me to connect my calendar again.",
        a: "For security, sign-ins last 14 days. Click Sign in with Google or Sign in with Microsoft again to reconnect.",
      },
      {
        q: "It says \"Too many requests\".",
        a: "There's a limit on how many events can be read per minute. Wait a moment and try again.",
      },
      {
        q: "The time or date looks wrong.",
        a: "Times are read in your computer's time zone, so check that it's set correctly. You can always fix a time with the pencil before creating the event.",
      },
    ],
  },
  {
    id: "privacy",
    icon: "shield",
    title: "Privacy and your data",
    questions: [
      {
        q: "What happens to the text I type?",
        a: (
          <>
            It's sent securely to the Prompt2Cal service, which uses Anthropic's Claude to read it, and the details come
            back to you for review. The text isn't written to our logs. The <Link to="/privacy-policy">privacy policy</Link>{" "}
            covers this in full.
          </>
        ),
      },
      {
        q: "How do I disconnect my calendar?",
        a: (
          <>
            Open Settings and choose <strong>Logout</strong>. You can also remove access from your{" "}
            <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer">
              Google account permissions
            </a>{" "}
            or your{" "}
            <a href="https://account.live.com/consent/Manage" target="_blank" rel="noopener noreferrer">
              Microsoft app permissions
            </a>
            , or remove the extension from Chrome.
          </>
        ),
      },
    ],
  },
];

function Support() {
  return (
    <>
      <section className="page-hero">
        <div className="section-inner">
          <span className="eyebrow">Support</span>
          <h1>How can we help?</h1>
          <p>Answers to the most common questions, and how to reach us if you're stuck.</p>
          <div className="topic-links">
            {TOPICS.map((topic) => (
              <a className="topic-link" href={`#${topic.id}`} key={topic.id}>
                <span className="card-icon">
                  <Icon name={topic.icon} size={20} />
                </span>
                {topic.title}
              </a>
            ))}
            <a className="topic-link" href="#contact">
              <span className="card-icon">
                <Icon name="mail" size={20} />
              </span>
              Contact us
            </a>
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="section-inner faq">
          {TOPICS.map((topic) => (
            <div className="faq-group" id={topic.id} key={topic.id}>
              <h2>{topic.title}</h2>
              {topic.questions.map(({ q, a }) => (
                <details className="faq-item" key={q}>
                  <summary>
                    {q}
                    <Icon name="chevronDown" size={18} className="faq-chevron" />
                  </summary>
                  <div className="faq-answer">{a}</div>
                </details>
              ))}
            </div>
          ))}

          <div className="contact-card" id="contact">
            <span className="card-icon card-icon-large">
              <Icon name="lifeBuoy" size={26} />
            </span>
            <div>
              <h2>Still stuck?</h2>
              <p>
                Tell us what you typed and the message you saw, and we'll help. Please leave out anything private, such as
                full email threads.
              </p>
              <div className="contact-actions">
                <a className="button button-primary" href={`mailto:${SUPPORT_EMAIL}?subject=Prompt2Cal%20support`}>
                  <Icon name="mail" size={18} /> Email support
                </a>
                <a className="button button-secondary" href={GITHUB_ISSUES_URL} target="_blank" rel="noopener noreferrer">
                  <Icon name="github" size={18} /> Report an issue on GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default Support;
