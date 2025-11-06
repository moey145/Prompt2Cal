# Test Prompts for Auto-Detection

## 🧪 Quick Test Suite - Recent Fixes

### Critical Tests to Verify

1. **"Meeting with CEO at 2pm with 30 minute buffer before and after"** → Should be SINGLE (not detect "and" as separator)
2. **"Every Monday for 6 months meeting at 2pm"** → Should be MULTIPLE (6 months of weekly events)
3. **"Create 5 meetings every day this week at 2pm"** → Should be 7 events (not 35)

---

## Single Event Prompts (Should detect as SINGLE)

### Basic Single Events

1. "Dentist appointment tomorrow at 2:30pm for 45 minutes"
2. "Meet John at Central Park this Saturday at 3pm"
3. "Team standup tomorrow morning at 9am"
4. "Flight to New York next Monday at 6:30am for 3 hours"
5. "Gym session tonight at 7pm for 1 hour"
6. "Lunch with Sarah on Nov 12 at 1:15pm for 45 minutes"
7. "Call John tomorrow at 9am for 30 minutes"
8. "Dentist appointment in 3 weeks at 2:30pm for 45 minutes"
9. "Project kickoff next week at 10am"
10. "Work session at 9:00am - 11:30am tomorrow"

### Analog Time Expressions

11. "Meeting at half past 2 tomorrow"
12. "Dentist at quarter past 10 on Monday"
13. "Call at quarter to 3 this afternoon"
14. "Gym at half past 7 tonight"
15. "Lunch at quarter past 12 tomorrow"
16. "Standup at 25 past 9 am"
17. "Review at 15 to 5 pm on Friday"
18. "Workshop at half past 10 in the morning"

### Natural Duration Expressions

19. "Quick call tomorrow at 2pm for half an hour"
20. "Meeting at 10am for a quarter of an hour"
21. "Gym session tonight at 7pm for an hour"
22. "Lunch at noon for half an hour"
23. "Call at 3pm for one hour"
24. "Workshop at 10am for two and a half hours"
25. "Seminar from 9am for one hour and a half"

### Weekday/Weekend Expressions

26. "Meeting every weekday at 9am"
27. "Weekend gym sessions on Saturday and Sunday at 8am"
28. "Standup every weekday at 10am for the next month"
29. "Weekend call on Saturday at 2pm"
30. "Weekday check-ins Monday through Friday at 3pm"

### Relative Time (Single Events)

31. "Meeting with Sarah in 2 hours"
32. "Doctor appointment in 3 days at 2pm"
33. "Phone call with client in 1 hour for 30 minutes"
34. "Pickup groceries in 45 minutes"
35. "Presentation in 4 hours for 2 hours"

### Specific Dates (Single Events)

36. "Annual review on December 15th at 2pm"
37. "Birthday party on November 10th at 6pm for 4 hours"
38. "Conference on January 5th at 9am for 2 days"
39. "Wedding on April 20th at 3pm for 6 hours"
40. "Vacation from December 20th to January 5th"
41. "Parent-teacher meeting next Thursday"

### Time Ranges (Single Events)

42. "Workshop at 1pm-5pm"
43. "All-day retreat from 8am -6pm tomorrow"

---

## Multiple Event Prompts (Should detect as MULTIPLE)

### Separator-Based Multiple Events

44. "Coffee at 10am and code review at 2pm"
45. "Lunch Friday at 12pm, doctor on Tuesday at 9am, gym tomorrow 7pm"
46. "Meeting at 8pm and lunch at 2pm"
47. "Meeting at 8pm then lunch at 2pm"
48. "Meeting at 8pm also lunch at 2pm"
49. "Meeting at 8pm plus lunch at 2pm"

### Numbered Bulk Events (Should ignore the number when "this week" is present)

50. "Create 5 meetings every day this week at 2pm"
51. "Create 3 appointments every day this week at 10am"
52. "Create 10 events every day this week at 2pm"
53. "2 calls tomorrow at 3pm and 5pm"

---

## Recurring Event Prompts (Should detect as MULTIPLE due to recurring patterns)

### Basic Recurring

53. "Every Monday team meeting at 10am for 1 hour"
54. "Every Tuesday morning yoga at 8am for 4 weeks"
55. "Every Friday happy hour at 5pm for 3 months"
56. "Every Wednesday afternoon coding session at 2pm for 6 weeks"
57. "Every Thursday book club at 7pm until December 15th"

### Time Range Recurring

58. "Every Monday lunch meeting at 12pm -1pm for 1 month"
59. "Every Friday team review at 3pm -5pm for 6 weeks"
60. "Every Tuesday tutorial session at 2pm -4pm for 2 months"
61. "Every Wednesday workshop at 10am -12pm until November 30th"
62. "Every Thursday strategy meeting at 9am -11am for 8 weeks"

### Short Duration Recurring

63. "Every Monday quick sync at 10am for 15 minutes for 3 months"
64. "Every Tuesday standup at 9am for 30 minutes for 6 weeks"
65. "Every Friday check-in at 4pm for 20 minutes until December"
66. "Every Wednesday update at 3pm for 45 minutes for 2 months"
67. "Every Thursday briefing at 11am for 10 minutes for 1 month"

### Long Duration Recurring

68. "Every Monday workshop at 9am for 3 hours for 4 weeks"
69. "Every Tuesday training session at 1pm for 4 hours for 2 months"
70. "Every Friday offsite meeting at 10am for 5 hours for 1 month"
71. "Every Wednesday all-day retreat from 8am -6pm for 6 weeks"
72. "Every Thursday conference at 9am for 8 hours until December"

### Complex Recurring Patterns

73. "Every other Tuesday mentoring session at 5pm for 2 months"
74. "First Monday of each month board meeting at 9am"
75. "Last Friday of each quarter review at 3pm"
76. "Every Monday for 6 months meeting at 2pm"
77. "Every Tuesday for 1 year training at 10am"
78. "Team sync every Tuesday at 4pm for 6 weeks"
79. "Standup every weekday at 9am until Dec 20"
80. "Focus block every day this week at 2pm"
81. "Mentoring every other Tuesday at 5pm for 2 months"
82. "First Monday of each month board meeting at 9am"
83. "Last Friday of each month town hall at 3pm"
84. "Every Wednesday this November yoga at 6:30pm"
85. "Every Tuesday team sync at 10am except holidays"
86. "Weekly 1:1 every Wednesday at 3pm for the next 4 weeks"

---

## Buffer Time Prompts (Should detect as SINGLE)

87. "Meeting with CEO at 2pm with 30 minute buffer before and after"
88. "Team sync at 10am with 15 minute buffer before"
89. "Client call at 3pm with 20 minute buffer after"
90. "Interview at 11am with 15 minute buffer both sides"
91. "Presentation at 4pm with 45 minute buffer before"
92. "Meeting with CEO at 2pm with 30 minutes buffer before and after"
93. "Review meeting at 3pm with buffer before and after"
94. "Standup at 9am with 15 minute buffer before and after"
95. "Conference call at 11am with 20 minute buffer before"
96. "Workshop at 2pm with 45 minute buffer after"

---

## Edge Cases & Special Patterns

### Timezone Mentions

97. "Call with Tokyo team at 2pm Tokyo time"

### Typos/Normalization

98. "Tommorow at 8 am quick standup" (tests typo handling)
99. "Tommorow at 8 am quick standup" (missing punctuation)

### No Time Given (Defaults)

100. "Parent-teacher meeting next Thursday"

### Duration with "and" (Should NOT be multiple)

101. "Meeting at 2pm for 2 hours and 30 minutes"
102. "Call at 10am for an hour and a half"
103. "Appointment at 3pm for 2 and a half hours"

### Time Range (Should NOT be multiple)

104. "Meeting from 9am to 11am tomorrow"
105. "Workshop at 1pm-5pm next Monday"

### Combined Analog Time & Duration

106. "Call at quarter past 2 for half an hour"
107. "Meeting at half past 10 for one hour"
108. "Review at 15 to 5 for a quarter of an hour"

### Date Range Events

#### Trips/Vacations (Should be SINGLE event)

109. "Holiday trip from 22nd November - 28th December"
110. "Vacation Nov 20 - Dec 5"
111. "Conference from January 10 - January 15"
112. "Ski trip Dec 20 to Jan 5"

#### Recurring Date Ranges (Should be MULTIPLE events)

113. "Daily meetings from Monday - Friday"
114. "Standup every weekday Nov 1 - Nov 30"

---

## Testing Checklist

### ✅ Single Event Detection

- [ ] Basic single events parse correctly
- [ ] Analog time expressions ("half past", "quarter to") work
- [ ] Natural duration expressions ("half an hour", "an hour") work
- [ ] Weekday/weekend expressions parse correctly
- [ ] Relative time ("in X hours") works
- [ ] Specific dates parse correctly
- [ ] Time ranges ("9am-11am") are treated as single
- [ ] Duration "and" ("2 hours and 30 minutes") doesn't trigger multiple

### ✅ Multiple Event Detection

- [ ] Separators ("and", "then", "also", "plus") detected
- [ ] Numbered events ("5 meetings") detected
- [ ] Multiple times with different activities detected
- [ ] Mixed events ("lunch at 12pm, doctor at 3pm") detected

### ✅ Recurring Event Detection

- [ ] "Every [day]" patterns detected as multiple
- [ ] "Every other" patterns detected
- [ ] "First/Last [day]" patterns detected
- [ ] Recurring with end conditions (count/until date) work
- [ ] Trip/vacation date ranges create single spanning event
- [ ] Recurring date ranges create multiple daily events

### ✅ Edge Cases

- [ ] Buffer time prompts parse correctly
- [ ] Typos handled gracefully
- [ ] Missing time defaults appropriately
- [ ] Complex nested patterns work

---

## Expected Results Summary

- **Single Events**: ~54 prompts
- **Multiple Events**: ~45 prompts (including recurring)
- **Total Test Cases**: ~114 prompts

**Note**: Recurring events are detected as "multiple" because they expand into multiple occurrences, even though they start as a single recurring pattern.

## New Features Tested

### Analog Time Expressions

- "half past", "quarter past", "quarter to"
- Specific minutes past/to ("25 past", "15 to")
- Combined with natural language durations

### Natural Duration Expressions

- "half an hour", "a quarter of an hour"
- "an hour", "one hour"
- "two and a half hours", "one hour and a half"

### Weekday/Weekend Patterns

- "every weekday" / "every weekdays"
- "weekend" / "weekends"
- "Monday through Friday" patterns
