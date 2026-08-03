# Appendix A: Benchmark dataset (100 inputs)

Stratified benchmark of 100 natural-language inputs (20 per category) with ground-truth event labels. Times are relative to the Australia/Sydney timezone.

| ID | Category | Input text | Ground-truth events |
| --- | --- | --- | --- |
| clean_01 | Clean | Team meeting next Tuesday at 3pm | team meeting @ next tuesday at 3pm |
| clean_02 | Clean | Coffee at 10am and code review at 2pm | coffee @ 10am; code review @ 2pm |
| clean_03 | Clean | Yoga class Saturday 8am at Bondi Gym | yoga class @ saturday at 8am (loc: bondi gym) |
| clean_04 | Clean | Dentist appointment tomorrow at 2:30pm | dentist appointment @ tomorrow at 2:30pm |
| clean_05 | Clean | Meet John at Central Park this Saturday at 3pm | meet john @ this saturday at 3pm (loc: central park) |
| clean_06 | Clean | Team standup tomorrow morning at 9am | team standup @ tomorrow morning at 9am |
| clean_07 | Clean | Lunch with Sarah on Nov 12 at 1:15pm | lunch with sarah @ nov 12 at 1:15pm |
| clean_08 | Clean | Project kickoff next week at 10am | project kickoff @ next week at 10am |
| clean_09 | Clean | Work session at 9:00am - 11:30am tomorrow | work session @ tomorrow at 9:00am (end: tomorrow at 11:30am) |
| clean_10 | Clean | Annual review on December 15th at 2pm | annual review @ december 15th at 2pm |
| clean_11 | Clean | Every Monday team meeting at 10am for 1 hour | team meeting @ every monday at 10am (recur: weekly) |
| clean_12 | Clean | First Monday of each month board meeting at 9am | board meeting @ first monday of each month at 9am (recur: monthly) |
| clean_13 | Clean | Parent-teacher meeting next Thursday | parent-teacher meeting @ next thursday |
| clean_14 | Clean | Flight to New York next Monday at 6:30am | flight to new york @ next monday at 6:30am |
| clean_15 | Clean | Birthday party on November 10th at 6pm | birthday party @ november 10th at 6pm |
| clean_16 | Clean | Coffee at 10am and lunch at 12pm and gym at 6pm | coffee @ 10am; lunch @ 12pm; gym @ 6pm |
| clean_17 | Clean | Weekly 1:1 every Wednesday at 3pm for the next 4 weeks | weekly 1:1 @ every wednesday at 3pm (recur: weekly) |
| clean_18 | Clean | Workshop at 1pm-5pm Friday | workshop @ friday at 1pm (end: friday at 5pm) |
| clean_19 | Clean | Meeting every weekday at 9am | meeting @ every weekday at 9am (recur: weekly) |
| clean_20 | Clean | Vacation from December 20th to January 5th | vacation @ december 20th (end: january 5th) |
| typos_01 | Typos | Lunch meeting Wednesdya at 1pm | lunch meeting @ wednesday at 1pm |
| typos_02 | Typos | Lnuch Friday at 12pm and dctor Tuesday at 9am | lunch @ friday at 12pm; doctor @ tuesday at 9am |
| typos_03 | Typos | Teem standup tomorow at 9am | team standup @ tomorrow at 9am |
| typos_04 | Typos | Dentst apointment tomorow at 2:30pm | dentist appointment @ tomorrow at 2:30pm |
| typos_05 | Typos | Meting with Sarah next Tuesady at 1pm | meeting with sarah @ next tuesday at 1pm |
| typos_06 | Typos | Coffe at 10am and code reveiw at 2pm | coffee @ 10am; code review @ 2pm |
| typos_07 | Typos | Gm session tonigt at 7pm | gym session @ tonight at 7pm |
| typos_08 | Typos | Confrence on Januery 5th at 9am | conference @ january 5th at 9am |
| typos_09 | Typos | Lunch with Jhon on Frday at 12pm | lunch with john @ friday at 12pm |
| typos_10 | Typos | Wrokshop at 1pm-5pm Frdiay | workshop @ friday at 1pm (end: friday at 5pm) |
| typos_11 | Typos | Evry Monday team meting at 10am | team meeting @ every monday at 10am (recur: weekly) |
| typos_12 | Typos | Birthady party on Novembr 10th at 6pm | birthday party @ november 10th at 6pm |
| typos_13 | Typos | Phne call with client next Wed at 3pm | phone call with client @ next wednesday at 3pm |
| typos_14 | Typos | Parent-techer meeting next Thrusday | parent-teacher meeting @ next thursday |
| typos_15 | Typos | Gym at half past 7 tonigt | gym @ tonight at 7:30pm |
| typos_16 | Typos | Anual review on Decembr 15th at 2pm | annual review @ december 15th at 2pm |
| typos_17 | Typos | Cofee at 10am and luch at 2pm | coffee @ 10am; lunch @ 2pm |
| typos_18 | Typos | Doktor appointment next Moday at 9am | doctor appointment @ next monday at 9am |
| typos_19 | Typos | Yogo class Satuday 8am at Bondi Gym | yoga class @ saturday at 8am (loc: bondi gym) |
| typos_20 | Typos | Projet kickoff nex week at 10am | project kickoff @ next week at 10am |
| voice_01 | Voice-to-text | meeting four next Tuesday at to PM | meeting @ next tuesday at 2pm |
| voice_02 | Voice-to-text | call mom Sunday eight thirty aye em | call mom @ sunday at 8:30am |
| voice_03 | Voice-to-text | lunch with sarah next too sday at won pm | lunch with sarah @ next tuesday at 1pm |
| voice_04 | Voice-to-text | gym session tonight at seven pee em | gym session @ tonight at 7pm |
| voice_05 | Voice-to-text | dentist appointment tomorrow at two thirty pee em | dentist appointment @ tomorrow at 2:30pm |
| voice_06 | Voice-to-text | team stand up tomorrow morning at nine ay em | team standup @ tomorrow morning at 9am |
| voice_07 | Voice-to-text | coffee at ten am and code review at two pee em | coffee @ 10am; code review @ 2pm |
| voice_08 | Voice-to-text | board meeting first monday of each month at nine ay em | board meeting @ first monday of each month at 9am (recur: monthly) |
| voice_09 | Voice-to-text | yoga class saturday at ate ay em at bondi gym | yoga class @ saturday at 8am (loc: bondi gym) |
| voice_10 | Voice-to-text | flight to new york next monday at six thirty ay em | flight to new york @ next monday at 6:30am |
| voice_11 | Voice-to-text | birthday party november tenth at six pee em | birthday party @ november 10th at 6pm |
| voice_12 | Voice-to-text | workshop at one pee em to five pee em friday | workshop @ friday at 1pm (end: friday at 5pm) |
| voice_13 | Voice-to-text | weekly one on one every wednesday at three pee em | weekly 1:1 @ every wednesday at 3pm (recur: weekly) |
| voice_14 | Voice-to-text | vacation from december twentieth two january fifth | vacation @ december 20th (end: january 5th) |
| voice_15 | Voice-to-text | lunch friday at twelve pee em doctor tuesday at nine ay em | lunch @ friday at 12pm; doctor @ tuesday at 9am |
| voice_16 | Voice-to-text | mentoring every other tuesday at five pee em | mentoring @ every other tuesday at 5pm (recur: weekly) |
| voice_17 | Voice-to-text | town hall last friday of each month at three pee em | town hall @ last friday of each month at 3pm (recur: monthly) |
| voice_18 | Voice-to-text | focus block every day this week at two pee em | focus block @ every day this week at 2pm (recur: daily) |
| voice_19 | Voice-to-text | call with client in won hour | call with client @ in 1 hour |
| voice_20 | Voice-to-text | parent teacher meeting next thursday at ate pee em | parent-teacher meeting @ next thursday at 8pm |
| ambiguous_01 | Ambiguous | Dinner with Sarah next Thursday around 7ish | dinner with sarah @ null |
| ambiguous_02 | Ambiguous | Catch up with the boys sometime this weekend | catch up with the boys @ null |
| ambiguous_03 | Ambiguous | Lunch with Alex sometime next week | lunch with alex @ null |
| ambiguous_04 | Ambiguous | Meeting with the team later today | meeting with the team @ null |
| ambiguous_05 | Ambiguous | Coffee soon with Jamie | coffee with jamie @ null |
| ambiguous_06 | Ambiguous | Dinner around eight tonight | dinner @ null |
| ambiguous_07 | Ambiguous | Catch up with Sam when we can | catch up with sam @ null |
| ambiguous_08 | Ambiguous | Party this weekend sometime | party @ null |
| ambiguous_09 | Ambiguous | Workout early morning tomorrow | workout @ null |
| ambiguous_10 | Ambiguous | Call mom in the evening Sunday | call mom @ null |
| ambiguous_11 | Ambiguous | Study session this week sometime | study session @ null |
| ambiguous_12 | Ambiguous | Brunch with friends mid-morning Saturday | brunch with friends @ null |
| ambiguous_13 | Ambiguous | Team sync when everyone's free next week | team sync @ null |
| ambiguous_14 | Ambiguous | Dinner with parents around dinnertime Friday | dinner with parents @ null |
| ambiguous_15 | Ambiguous | Meeting after lunch next Tuesday | meeting @ null |
| ambiguous_16 | Ambiguous | Gym session later this week | gym session @ null |
| ambiguous_17 | Ambiguous | Coffee with mentor sometime Thursday | coffee with mentor @ null |
| ambiguous_18 | Ambiguous | Presentation afternoon next Wednesday | presentation @ null |
| ambiguous_19 | Ambiguous | Happy hour end of day Friday | happy hour @ null |
| ambiguous_20 | Ambiguous | Lunch downtown around noonish | lunch @ null |
| missing_01 | Missing fields | Meeting with John next Tuesday (no time) | meeting with john @ next tuesday |
| missing_02 | Missing fields | Lunch on Friday (no time, no location) | lunch @ friday |
| missing_03 | Missing fields | Dinner with Sarah (no date or time) | dinner with sarah @ null |
| missing_04 | Missing fields | Gym session (no time) | gym session @ null |
| missing_05 | Missing fields | Call mom (no time) | call mom @ null |
| missing_06 | Missing fields | Team meeting next week (no time) | team meeting @ null |
| missing_07 | Missing fields | Doctor appointment (no date or time) | doctor appointment @ null |
| missing_08 | Missing fields | Coffee with Alex tomorrow (no time) | coffee with alex @ tomorrow |
| missing_09 | Missing fields | Workshop at the office (no time) | workshop @ null (loc: the office) |
| missing_10 | Missing fields | Birthday party (no date or time or location) | birthday party @ null |
| missing_11 | Missing fields | Conference call (no time) | conference call @ null |
| missing_12 | Missing fields | Lunch with Sarah (no time, no date) | lunch with sarah @ null |
| missing_13 | Missing fields | Dentist (no details) | dentist @ null |
| missing_14 | Missing fields | Meeting with John and Sarah next Tuesday (no time) | meeting with john and sarah @ next tuesday |
| missing_15 | Missing fields | Yoga at Bondi Gym (no time) | yoga @ null (loc: bondi gym) |
| missing_16 | Missing fields | Flight to Melbourne (no date or time) | flight to melbourne @ null |
| missing_17 | Missing fields | Code review (no time) | code review @ null |
| missing_18 | Missing fields | Standup every Monday (no time) | standup @ null (recur: weekly) |
| missing_19 | Missing fields | Interview next Thursday (no time) | interview @ next thursday |
| missing_20 | Missing fields | Pick up kids from school Friday (no time) | pick up kids from school @ friday |
