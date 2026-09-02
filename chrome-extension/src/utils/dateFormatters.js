// Date formatting utility functions

export const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return "Not specified";

  try {
    const date = new Date(dateTimeString);
    return date.toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch (error) {
    return dateTimeString;
  }
};

export const toDateTimeLocal = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

export const formatDateTimeShort = (isoString) => {
  if (!isoString) return "";
  const date = new Date(isoString);
  const options = {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  };
  return date.toLocaleString("en-US", options);
};

export const formatTimeShort = (isoString) => {
  if (!isoString) return "";
  const date = new Date(isoString);
  const options = { hour: "numeric", minute: "2-digit" };
  return date.toLocaleString("en-US", options);
};

/** Format a date or ISO datetime without shifting date-only values across timezones. */
export const formatDateOnly = (value) => {
  if (!value) return "";
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const date = new Date(
      Number(match[1]),
      Number(match[2]) - 1,
      Number(match[3])
    );
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
  return formatDateTimeShort(value);
};

