// Recurrence description utility

export const getRecurrenceDescription = (event) => {
  if (!event || !event.recurrence_type || event.recurrence_type === "none") {
    return null;
  }

  const recurrenceType = event.recurrence_type.toLowerCase();
  const interval = event.recurrence_interval || 1;
  const startTime = event.start_time;

  if (!startTime) {
    return recurrenceType.charAt(0).toUpperCase() + recurrenceType.slice(1);
  }

  try {
    const date = new Date(startTime);
    const dayOfWeek = date.getDay();
    const dayOfMonth = date.getDate();
    const month = date.getMonth();

    const days = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];

    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];

    const dayName = days[dayOfWeek];
    const monthName = months[month];

    const textSources = [event.title, event.notes, event.original_text]
      .filter(Boolean)
      .map((text) => text.toLowerCase());

    const hasWeekendKeyword = textSources.some((text) =>
      text.includes("weekend")
    );
    const hasWeekdayKeyword = textSources.some(
      (text) =>
        text.includes("weekday") ||
        text.includes("weekdays") ||
        text.includes("business day") ||
        text.includes("business days") ||
        text.includes("workday") ||
        text.includes("workdays") ||
        text.includes("work day") ||
        text.includes("work days")
    );
    const startsOnWeekend = dayOfWeek === 6 || dayOfWeek === 0;

    const getWeekdayOccurrence = (date) => {
      const dayOfMonth = date.getDate();
      const dayOfWeek = date.getDay();
      const year = date.getFullYear();
      const month = date.getMonth();
      const lastDayOfMonth = new Date(year, month + 1, 0).getDate();

      const occurrences = [];
      for (let d = 1; d <= lastDayOfMonth; d++) {
        const testDate = new Date(year, month, d);
        if (testDate.getDay() === dayOfWeek) {
          occurrences.push(d);
        }
      }

      const occurrenceIndex = occurrences.indexOf(dayOfMonth);
      if (occurrenceIndex === -1) return null;

      const occurrenceNumber = occurrenceIndex + 1;
      const totalOccurrences = occurrences.length;

      if (occurrenceNumber === 1) return "first";
      if (occurrenceNumber === 2) return "second";
      if (occurrenceNumber === 3) return "third";
      if (occurrenceNumber === 4) return "fourth";
      if (occurrenceNumber === totalOccurrences && totalOccurrences > 1)
        return "last";

      return null;
    };

    let description = "";

    if (recurrenceType === "daily") {
      if (interval === 1) {
        if (hasWeekendKeyword) {
          description = "Weekends";
        } else if (hasWeekdayKeyword) {
          description = "Weekdays";
        } else {
          description = "Daily";
        }
      } else {
        description = `Every ${interval === 2 ? "other" : interval} day`;
      }
    } else if (recurrenceType === "weekly") {
      const isWeekendEvent =
        hasWeekendKeyword && startsOnWeekend && interval === 1;
      const isWeekdayEvent = hasWeekdayKeyword && interval === 1;

      if (isWeekendEvent) {
        description = "Weekends";
      } else if (isWeekdayEvent) {
        description = "Weekdays";
      } else if (interval === 1) {
        description = `Weekly on ${dayName}`;
      } else if (interval === 2) {
        description = `Every other ${dayName}`;
      } else {
        description = `Every ${interval} weeks on ${dayName}`;
      }
    } else if (recurrenceType === "monthly") {
      if (interval === 1) {
        const occurrence = getWeekdayOccurrence(date);
        if (occurrence) {
          description = `Monthly on the ${occurrence} ${dayName}`;
        } else {
          description = `Monthly on day ${dayOfMonth}`;
        }
      } else {
        const occurrence = getWeekdayOccurrence(date);
        if (occurrence) {
          description = `Every ${interval} months on the ${occurrence} ${dayName}`;
        } else {
          description = `Every ${interval} months on day ${dayOfMonth}`;
        }
      }
    } else if (recurrenceType === "yearly") {
      if (interval === 1) {
        description = `Annually on ${monthName} ${dayOfMonth}`;
      } else {
        description = `Every ${interval} years on ${monthName} ${dayOfMonth}`;
      }
    } else {
      description =
        recurrenceType.charAt(0).toUpperCase() + recurrenceType.slice(1);
    }

    return description;
  } catch (e) {
    return recurrenceType.charAt(0).toUpperCase() + recurrenceType.slice(1);
  }
};

