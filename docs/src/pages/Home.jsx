import { useEffect } from "react";
import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  useEffect(() => {
    const elements = document.querySelectorAll(".reveal-on-scroll");
    if (!elements.length) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.2,
        rootMargin: "0px 0px -10% 0px",
      }
    );

    elements.forEach((element) => observer.observe(element));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-glow hero-glow-1"></div>
          <div className="hero-glow hero-glow-2"></div>
          <div className="hero-grid"></div>
        </div>
        
        <nav className="hero-nav">
          <div className="nav-brand">
            <img src="/logo.svg" alt="Prompt2Cal" className="nav-logo" />
            <span className="nav-name">Prompt2Cal</span>
          </div>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="https://github.com/moey145/Prompt2Cal" target="_blank" rel="noopener noreferrer">GitHub</a>
          </div>
        </nav>

        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">✨</span>
            <span>AI-Powered Chrome Extension</span>
          </div>
          
          <h1 className="hero-title">
            Turn <span className="highlight">Natural Language</span> into Calendar Events
          </h1>
          
          <p className="hero-description">
            Stop clicking through forms. Just type or speak your event in plain English, 
            and let AI create your Google Calendar events instantly.
          </p>

          <div className="hero-demo">
            <div className="demo-input">
              <span className="demo-icon">🎤</span>
              <span className="demo-text">"Meeting with Sarah tomorrow at 3pm for coffee"</span>
              <span className="demo-cursor"></span>
            </div>
            <div className="demo-arrow">↓</div>
            <div className="demo-output">
              <div className="demo-event">
                <span className="event-color"></span>
                <div className="event-details">
                  <span className="event-title">Meeting with Sarah</span>
                  <span className="event-time">Tomorrow, 3:00 PM • Coffee</span>
                </div>
                <span className="event-check">✓</span>
              </div>
            </div>
          </div>

          <div className="hero-cta">
            <a
              href="https://chromewebstore.google.com/detail/prompt2cal-natural-langua/appgechmmibkflmhhblcnfonecomfikm"
              className="cta-primary"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg className="chrome-icon" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
                <circle cx="12" cy="12" r="4" fill="currentColor"/>
              </svg>
              Install Free from Chrome Store
            </a>
            <a href="#features" className="cta-secondary">
              Learn More
              <span className="arrow">→</span>
            </a>
          </div>

          <div className="hero-stats">
            <div className="stat">
              <span className="stat-value">4.9★</span>
              <span className="stat-label">User Rating</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat">
              <span className="stat-value">1000+</span>
              <span className="stat-label">Active Users</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat">
              <span className="stat-value">Free</span>
              <span className="stat-label">Forever</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="container">
        <main className="content">
          <section className="section reveal-on-scroll" id="features">
            <h2 className="features-title reveal-on-scroll" style={{ transitionDelay: "0ms" }}>Powerful Features</h2>
            <p className="features-subtitle reveal-on-scroll" style={{ transitionDelay: "100ms" }}>Everything you need to manage your calendar effortlessly with the power of AI</p>
            <div className="features">
              <div className="feature reveal-on-scroll" style={{ transitionDelay: "0ms" }}>
                <div className="feature-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                  </svg>
                </div>
                <div className="feature-content">
                  <h3>Voice Input</h3>
                  <p>Speak your events naturally using voice recognition. Just talk, and we'll capture every detail.</p>
                </div>
              </div>
              <div className="feature reveal-on-scroll" style={{ transitionDelay: "120ms" }}>
                <div className="feature-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.4V11h3a3 3 0 0 1 3 3v1a2 2 0 0 1-2 2h-1v3a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-3H6a2 2 0 0 1-2-2v-1a3 3 0 0 1 3-3h3V9.4A4 4 0 0 1 12 2z"/>
                    <circle cx="12" cy="6" r="1"/>
                  </svg>
                </div>
                <div className="feature-content">
                  <h3>AI-Powered Parsing</h3>
                  <p>Advanced AI understands complex natural language. Dates, times, locations—it gets it all.</p>
                </div>
              </div>
              <div className="feature reveal-on-scroll" style={{ transitionDelay: "240ms" }}>
                <div className="feature-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                </div>
                <div className="feature-content">
                  <h3>Conflict Detection</h3>
                  <p>Automatically checks for scheduling conflicts before creating events. Never double-book again.</p>
                </div>
              </div>
              <div className="feature reveal-on-scroll" style={{ transitionDelay: "360ms" }}>
                <div className="feature-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                    <line x1="12" y1="14" x2="12" y2="18"/>
                    <line x1="10" y1="16" x2="14" y2="16"/>
                  </svg>
                </div>
                <div className="feature-content">
                  <h3>Bulk Events</h3>
                  <p>Parse and create multiple events at once. Perfect for planning your entire week in seconds.</p>
                </div>
              </div>
            </div>
          </section>

          <section className="section reveal-on-scroll" id="how-it-works">
            <h2 className="how-it-works-title reveal-on-scroll" style={{ transitionDelay: "0ms" }}>How It Works</h2>
            <div className="steps-container">
              <div className="step reveal-on-scroll" style={{ transitionDelay: "80ms" }}>
                <div className="step-icon-wrapper">
                  <div className="step-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  </div>
                  <span className="step-number">1</span>
                </div>
                <h3 className="step-title">Type or Speak</h3>
                <p className="step-desc">Type or speak your event in plain English</p>
              </div>

              <div className="step-divider"></div>

              <div className="step reveal-on-scroll" style={{ transitionDelay: "180ms" }}>
                <div className="step-icon-wrapper">
                  <div className="step-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                  </div>
                  <span className="step-number">2</span>
                </div>
                <h3 className="step-title">AI Parses</h3>
                <p className="step-desc">AI parses your text into structured event details</p>
              </div>

              <div className="step-divider"></div>

              <div className="step reveal-on-scroll" style={{ transitionDelay: "280ms" }}>
                <div className="step-icon-wrapper">
                  <div className="step-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </div>
                  <span className="step-number">3</span>
                </div>
                <h3 className="step-title">Review & Edit</h3>
                <p className="step-desc">Review and edit the parsed event (if needed)</p>
              </div>

              <div className="step-divider"></div>

              <div className="step reveal-on-scroll" style={{ transitionDelay: "380ms" }}>
                <div className="step-icon-wrapper">
                  <div className="step-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                      <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                  </div>
                  <span className="step-number">4</span>
                </div>
                <h3 className="step-title">Confirm</h3>
                <p className="step-desc">Confirm and it's added to your Google Calendar instantly</p>
              </div>
            </div>
          </section>

          <div className="cta reveal-on-scroll" style={{ transitionDelay: "120ms" }}>
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
      </div>

      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-left">
            <p>&copy; 2025 Prompt2Cal. All rights reserved.</p>
            <p className="footer-subtle">Built for fast, reliable calendar event creation.</p>
          </div>
          <div className="footer-links">
            <Link to="/privacy-policy">Privacy Policy</Link>
            <a
              href="https://github.com/moey145/Prompt2Cal"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub repo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
