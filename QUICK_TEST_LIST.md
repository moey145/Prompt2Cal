# Quick Test List - Recent Fixes

## 🎯 Priority Tests (Must Work)

### 1. Multiple Distinct Events Detection

✅ These should detect **3 separate events** (not expand into recurrence):

- "Parent-teacher meeting next Thursday and Wedding on April 20th at 3pm for 6 hours and Conference on January 5th at 9am for 2 days"
- "Lunch with Sarah on Nov 12 at 1:15pm for 45 minutes and Work session at 9:00am - 11:30am tomorrow and Project kickoff next week at 10am"

### 2. Buffer Time "And" Detection

✅ These should be **SINGLE** events (no false "and" separator detection):

- "Meeting with CEO at 2pm with 30 minute buffer before and after"
- "Team sync at 10am with 15 minute buffer before and after"
- "Review meeting at 3pm with buffer before and after"
- "Conference call at 11am with 20 minute buffer before"

### 3. Date Range Events

✅ Trips/Vacations should be **SINGLE** long events:

- "Holiday trip from 22nd November - 28th December" → Single event spanning the dates
- "Vacation Nov 20 - Dec 5" → Single event spanning the dates
- "Ski trip Dec 20 to Jan 5" → Single event spanning the dates

✅ Recurring date ranges should be **MULTIPLE** events:

- "Daily meetings from Monday - Friday" → 5 daily events

### 4. Recurring Events Auto-Detection

✅ These should be **MULTIPLE** events (auto-detect and expand):

- "Every Monday for 6 months meeting at 2pm" → Should expand to ~24 weekly events
- "Every Monday team meeting at 10am for 1 hour" → Should expand to ~4 events (default)
- "Every Friday happy hour at 5pm for 3 months" → Should expand to ~12 weekly events

### 5. "This Week" Numbered Events

✅ These should create **7 events** (full week), ignoring the number:

- "Create 5 meetings every day this week at 2pm" → 7 events (not 35!)
- "Create 3 appointments every day this week at 10am" → 7 events (not 21!)
- "Create 10 events every day this week at 2pm" → 7 events (not 70!)

---

## 🧪 Additional Buffer Time Tests

- "Standup at 9am with 15 minute buffer before and after"
- "Workshop at 2pm with 45 minute buffer after"
- "Meeting with CEO at 2pm with 30 minutes buffer before and after"

---

## 🧪 Additional Recurring Tests

- "Every Tuesday morning yoga at 8am for 4 weeks"
- "Every Wednesday afternoon coding session at 2pm for 6 weeks"
- "Every Thursday book club at 7pm until December 15th"
- "Team sync every Tuesday at 4pm for 6 weeks"
- "Weekly 1:1 every Wednesday at 3pm for the next 4 weeks"

---

## Quick Verification

### ✅ Single Event (should NOT expand):

- "Dentist appointment tomorrow at 2:30pm for 45 minutes"
- "Gym session tonight at 7pm for 1 hour"
- "Meeting with CEO at 2pm with 30 minute buffer before and after"

### ✅ Multiple Events (should expand):

- "Every Monday for 6 months meeting at 2pm" → ~24 events
- "Create 5 meetings every day this week at 2pm" → 7 events
- "Every Monday team meeting at 10am for 1 hour" → ~4 events

---

## What to Check

1. **Detection**: Does auto-detection correctly identify single vs multiple?
2. **Expansion**: Do recurring events expand to the right count?
3. **Buffer Time**: Does "before and after" NOT trigger multiple detection?
4. **This Week**: Does "this week" create exactly 7 events regardless of the number?
5. **UI**: Does the UI show the correct event count in the preview?
