
function PrivacyPolicy() {
  return (
    <>
      <section className="page-hero page-hero-compact">
        <div className="section-inner">
          <span className="eyebrow">Legal</span>
          <h1>Privacy policy</h1>
          <p>Last updated: October 6, 2026</p>
        </div>
      </section>
      <section className="section section-tight">
      <article className="section-inner prose">

        <p>
          <strong>Prompt2Cal</strong> ("we", "our", "us", or "the application") is a Google Chrome extension 
          developed and operated by the Prompt2Cal development team. This application helps you turn natural 
          language text into calendar events by integrating with Google Calendar and Microsoft Outlook. This privacy policy applies 
          specifically to the Prompt2Cal Chrome extension and associated services.
        </p>

        <p>
          Prompt2Cal respects your privacy and is committed to protecting the personal information
          you share with us. This privacy policy explains what data we collect,
          how we use it, and the choices you have regarding your information.
        </p>

        <h2>Information We Collect</h2>
        <p>Prompt2Cal handles the following categories of information:</p>
        <ul>
          <li>
            <strong>User-provided event text.</strong> The text you type or paste
            into the extension popup, capture via voice recognition, or select on
            a web page and send with the "Add to calendar with Prompt2Cal"
            right-click menu, so that we can parse it into event details. The
            right-click menu only reads the text you have selected, and only
            when you choose it.
          </li>
          <li>
            <strong>Calendar metadata.</strong> Names and identifiers of calendars
            you select when creating events, obtained through the Google Calendar
            API or the Microsoft Graph API (for Outlook) with your permission.
          </li>
          <li>
            <strong>Event details.</strong> Titles, times, recurrence rules,
            notes, attendees, meeting links, and other fields required to create
            calendar events.
          </li>
          <li>
            <strong>Authentication tokens.</strong> OAuth tokens provided by
            Google or Microsoft when you sign in, stored securely on your device (and on your
            account's backend workspace if you deploy and authenticate with the
            optional cloud service).
          </li>
          <li>
            <strong>Usage diagnostics (anonymous).</strong> Non-identifiable logs
            on the backend services (for example, error traces and performance
            timings). These never include the actual text of your events.
          </li>
        </ul>

        <h2>How We Use Your Information</h2>
        <p>
          We use the collected information solely to deliver the functionality of
          the extension:
        </p>
        <ul>
          <li>
            Parse your input text with our event parsing service (which calls
            Anthropic's Claude API) and return structured event details.
          </li>
          <li>
            Check for scheduling conflicts and suggest alternatives when you
            request it.
          </li>
          <li>
            Create, update, or delete events on your selected Google or Outlook
            calendar as instructed.
          </li>
          <li>
            Generate notifications (toasts) within the extension UI about success
            or errors.
          </li>
          <li>
            Improve reliability, troubleshoot issues, and secure the service.
          </li>
        </ul>

        <h2>Data Storage and Retention</h2>
        <p>
          Prompt2Cal stores most data locally in the extension context. When you
          deploy and connect to the optional Prompt2Cal backend service:
        </p>
        <ul>
          <li>
            OAuth tokens are encrypted and stored in the backend's secure
            storage so that the service can act on your behalf.
          </li>
          <li>
            Event parsing requests sent to Anthropic are transient and not
            retained beyond the session needed to fulfill the request, according
            to the Anthropic API policies.
          </li>
          <li>
            Logs record the size and outcome of a request, not the text of your
            events, and are retained temporarily for diagnostics before
            automatic deletion.
          </li>
        </ul>

        <h2>Sharing and Disclosure</h2>
        <p>
          We do not sell or rent your personal information. Data is shared only
          with:
        </p>
        <ul>
          <li>
            <strong>Google Calendar API.</strong> Required to create and manage
            events on your calendars.
          </li>
          <li>
            <strong>Microsoft Graph API.</strong> Required to create and manage
            events on your Outlook calendars when you sign in with Microsoft.
          </li>
          <li>
            <strong>Anthropic (Claude) API.</strong> When parsing event text
            (your input text is transmitted to Anthropic for processing).
          </li>
          <li>
            <strong>Service providers.</strong> If you deploy the backend on
            Google Cloud, information is processed according to Google Cloud's
            security and privacy standards.
          </li>
          <li>
            <strong>Legal requirements.</strong> We may disclose information if
            required by law or in response to valid requests by public
            authorities.
          </li>
        </ul>

        <h2>Your Choices and Controls</h2>
        <ul>
          <li>
            You can disconnect the extension from your Google or Microsoft
            account at any time from the settings menu, via Google's{' '}
            <a
              href="https://myaccount.google.com/permissions"
              rel="noreferrer noopener"
              target="_blank"
            >
              Account Permissions
            </a>{' '}
            page, or via Microsoft's{' '}
            <a
              href="https://account.live.com/consent/Manage"
              rel="noreferrer noopener"
              target="_blank"
            >
              app permissions
            </a>{' '}
            page.
          </li>
          <li>
            You can delete the OAuth tokens the backend holds for you at any
            time by choosing Disconnect in the extension. They are also deleted
            automatically 14 days after you connect, at which point you sign in
            again.
          </li>
          <li>
            You may remove the extension from Chrome to stop all data collection
            and interaction.
          </li>
        </ul>

        <h2>Security</h2>
        <p>
          We use industry-standard security practices to protect your information,
          including HTTPS for all communication and encrypted storage for OAuth
          tokens. Nevertheless, no online service is entirely risk-free. Please
          use strong, unique passwords and keep your devices secure.
        </p>

        <h2>Children's Privacy</h2>
        <p>
          Prompt2Cal is not intended for use by children under the age of 13. We
          do not knowingly collect personal information from children. If you are
          a parent or guardian and believe your child has provided personal
          information, please contact us so that we can delete it.
        </p>

        <h2>International Users</h2>
        <p>
          If you use Prompt2Cal from outside Australia, be aware that data may be
          processed in the country where you deploy the backend (for example, the
          United States if you deploy on Google Cloud Run in the us-central1
          region) and in regions where our service providers operate.
        </p>

        <h2>Changes to This Policy</h2>
        <p>
          We may update this privacy policy from time to time. Any changes will be
          posted on this page with an updated "Last updated" date. Your continued
          use of Prompt2Cal after changes constitutes acceptance of the revised
          policy.
        </p>

        <h2>Contact Us</h2>
        <p>
          If you have questions or concerns about this privacy policy, please
          email <a href="mailto:mohamad.eldhaibi@gmail.com">mohamad.eldhaibi@gmail.com</a>{' '}
          or open an issue on the project GitHub repository:{' '}
          <a
            href="https://github.com/moey145/Prompt2Cal"
            rel="noreferrer noopener"
            target="_blank"
          >
            github.com/moey145/Prompt2Cal
          </a>.
        </p>
      </article>
      </section>
    </>
  )
}

export default PrivacyPolicy
