// Email utility functions

export const isValidEmail = (email = "") =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

export const ensureUniqueEmails = (emails = []) => {
  const unique = [];
  const seen = new Set();
  emails.forEach((raw) => {
    if (!raw) return;
    const trimmed = raw.trim();
    if (!trimmed) return;
    if (!isValidEmail(trimmed)) return;
    const lower = trimmed.toLowerCase();
    if (!seen.has(lower)) {
      seen.add(lower);
      unique.push(trimmed);
    }
  });
  return unique;
};

export const parseAttendeeInput = (value = "") => {
  if (Array.isArray(value)) {
    return ensureUniqueEmails(value);
  }
  if (typeof value !== "string") {
    return [];
  }
  const parts = value
    .split(/[\s,;]+/)
    .map((email) => email.trim())
    .filter((email) => email.length > 0);
  return ensureUniqueEmails(parts);
};

