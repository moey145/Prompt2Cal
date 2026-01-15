import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home">
      <div className="container">
        <header className="header">
          <div className="brand">
            <img className="brand-logo" src="/logo.svg" alt="Prompt2Cal logo" />
            <div className="brand-text">
              <h1>Prompt2Cal</h1>
              <p className="tagline">
                Turn natural language into calendar events instantly
              </p>
            </div>
          </div>
        </header>

        <main className="content">
          <section className="section">
            <h2>About Prompt2Cal</h2>
            <p>
              Prompt2Cal is a Chrome extension that converts natural language
              into Google Calendar events. Simply type or speak your event in
              plain English, and AI handles the rest. No more clicking through
              multiple form fields, just describe your event and it's added to
              your calendar.
            </p>
          </section>

          <section className="section">
            <h2>Key Features</h2>
            <div className="features">
              <div className="feature">
                <h3>Voice Input</h3>
                <p>Speak your events naturally using voice recognition</p>
              </div>
              <div className="feature">
                <h3>AI-Powered Parsing</h3>
                <p>Advanced AI understands complex natural language</p>
              </div>
              <div className="feature">
                <h3>Conflict Detection</h3>
                <p>Automatically checks for scheduling conflicts</p>
              </div>
              <div className="feature">
                <h3>Bulk Events</h3>
                <p>Parse and create multiple events at once</p>
              </div>
            </div>
          </section>

          <section className="section">
            <h2>How It Works</h2>
            <ul className="how-it-works">
              <li>Type or speak your event in plain English</li>
              <li>AI parses your text into structured event details</li>
              <li>Review and edit the parsed event (if needed)</li>
              <li>Confirm and it's added to your Google Calendar instantly</li>
            </ul>
          </section>

          <div className="cta">
            <a
               href="https://chromewebstore.google.com/detail/prompt2cal-natural-langua/appgechmmibkflmhhblcnfonecomfikm"
              className="cta-button"
              target="_blank"
              rel="noopener noreferrer"
            >
              Install from Chrome Web Store
            </a>
          </div>
        </main>

        <footer className="footer">
          <p>&copy; 2025 Prompt2Cal. All rights reserved.</p>
          <div className="footer-links">
            <Link to="/privacy-policy">Privacy Policy</Link>
            <a
              href="https://github.com/moey145/Prompt2Cal"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default Home;
