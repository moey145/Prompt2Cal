// Group free slots by day for the find-a-slot panel.

const sameDay = (a, b) =>
  a.getFullYear() === b.getFullYear() &&
  a.getMonth() === b.getMonth() &&
  a.getDate() === b.getDate();

export const dayLabel = (date, now = new Date()) => {
  const tomorrow = new Date(now);
  tomorrow.setDate(now.getDate() + 1);
  if (sameDay(date, now)) return "Today";
  if (sameDay(date, tomorrow)) return "Tomorrow";
  return date.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
};

export const timeLabel = (date) =>
  date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });

// [{ label, slots: [{ ...slot, time }] }] in the order the slots arrive.
export const groupSlotsByDay = (slots, now = new Date()) => {
  const groups = [];
  for (const slot of slots) {
    const start = new Date(slot.start);
    const label = dayLabel(start, now);
    let group = groups[groups.length - 1];
    if (!group || group.label !== label) {
      group = { label, slots: [] };
      groups.push(group);
    }
    group.slots.push({ ...slot, time: timeLabel(start) });
  }
  return groups;
};
