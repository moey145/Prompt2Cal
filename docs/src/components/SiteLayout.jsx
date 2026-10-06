import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import Icon from "./Icon";
import { CHROME_STORE_URL, GITHUB_URL } from "../links";

export function Wordmark() {
  return (
    <span className="wordmark">
      <img src="/logo.svg" alt="" className="wordmark-logo" />
      <span className="wordmark-name">
        Prompt2<span className="wordmark-red">Cal</span>
      </span>
    </span>
  );
}

export function AddToChrome({ className = "", children = "Add to Chrome" }) {
  return (
    <a className={`button button-primary ${className}`} href={CHROME_STORE_URL} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

function SiteNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // Close the phone menu after following a link.
  useEffect(() => setOpen(false), [location.pathname, location.hash]);

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-brand" aria-label="Prompt2Cal home">
          <Wordmark />
        </Link>
        <nav className={`nav-links ${open ? "is-open" : ""}`} aria-label="Main">
          <Link to="/#features">Features</Link>
          <Link to="/#how-it-works">How it works</Link>
          <NavLink to="/support">Support</NavLink>
          <AddToChrome className="nav-cta" />
        </nav>
        <button
          type="button"
          className="nav-toggle"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          <Icon name={open ? "x" : "menu"} size={22} />
        </button>
      </div>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Wordmark />
          <p>Plain English in, calendar events out. For Google Calendar and Outlook.</p>
        </div>
        <div className="footer-columns">
          <div>
            <h3>Product</h3>
            <Link to="/#features">Features</Link>
            <Link to="/#how-it-works">How it works</Link>
            <a href={CHROME_STORE_URL} target="_blank" rel="noopener noreferrer">
              Chrome Web Store
            </a>
          </div>
          <div>
            <h3>Help</h3>
            <Link to="/support">Support</Link>
            <Link to="/privacy-policy">Privacy policy</Link>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </div>
        </div>
      </div>
      <div className="footer-base">© 2026 Prompt2Cal</div>
    </footer>
  );
}

// Every page: the bar along the top, the page, and the footer. Following a
// link to /#features scrolls to that section; other page changes start at the
// top.
function SiteLayout({ children }) {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const target = document.getElementById(hash.slice(1));
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);

  return (
    <div className="site">
      <SiteNav />
      <main>{children}</main>
      <SiteFooter />
    </div>
  );
}

export default SiteLayout;
