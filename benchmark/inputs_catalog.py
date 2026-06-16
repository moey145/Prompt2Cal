"""Curated benchmark inputs for the 100-input stratified dataset.

Ground-truth labels are draft labels for Phase 5. Review and refine before
the full benchmark run; have a supervisor verify at least 10% of labels.
"""

from __future__ import annotations

from typing import Any, Dict, List

Event = Dict[str, Any]
InputRow = Dict[str, Any]


def _event(
    title: str,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    notes: str | None = None,
    recurrence_type: str = "none",
) -> Event:
    return {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "notes": notes,
        "recurrence_type": recurrence_type,
    }


def _row(input_id: str, category: str, text: str, ground_truth: List[Event]) -> InputRow:
    return {
        "id": input_id,
        "category": category,
        "text": text,
        "ground_truth": ground_truth,
    }


def clean_inputs() -> List[InputRow]:
    return [
        _row("clean_01", "clean", "Team meeting next Tuesday at 3pm", [_event("team meeting", start_time="next tuesday at 3pm")]),
        _row(
            "clean_02",
            "clean",
            "Coffee at 10am and code review at 2pm",
            [_event("coffee", start_time="10am"), _event("code review", start_time="2pm")],
        ),
        _row(
            "clean_03",
            "clean",
            "Yoga class Saturday 8am at Bondi Gym",
            [_event("yoga class", start_time="saturday at 8am", location="bondi gym")],
        ),
        _row("clean_04", "clean", "Dentist appointment tomorrow at 2:30pm", [_event("dentist appointment", start_time="tomorrow at 2:30pm")]),
        _row(
            "clean_05",
            "clean",
            "Meet John at Central Park this Saturday at 3pm",
            [_event("meet john", start_time="this saturday at 3pm", location="central park")],
        ),
        _row("clean_06", "clean", "Team standup tomorrow morning at 9am", [_event("team standup", start_time="tomorrow morning at 9am")]),
        _row(
            "clean_07",
            "clean",
            "Lunch with Sarah on Nov 12 at 1:15pm",
            [_event("lunch with sarah", start_time="nov 12 at 1:15pm")],
        ),
        _row("clean_08", "clean", "Project kickoff next week at 10am", [_event("project kickoff", start_time="next week at 10am")]),
        _row(
            "clean_09",
            "clean",
            "Work session at 9:00am - 11:30am tomorrow",
            [_event("work session", start_time="tomorrow at 9:00am", end_time="tomorrow at 11:30am")],
        ),
        _row(
            "clean_10",
            "clean",
            "Annual review on December 15th at 2pm",
            [_event("annual review", start_time="december 15th at 2pm")],
        ),
        _row(
            "clean_11",
            "clean",
            "Every Monday team meeting at 10am for 1 hour",
            [_event("team meeting", start_time="every monday at 10am", recurrence_type="weekly")],
        ),
        _row(
            "clean_12",
            "clean",
            "First Monday of each month board meeting at 9am",
            [_event("board meeting", start_time="first monday of each month at 9am", recurrence_type="monthly")],
        ),
        _row("clean_13", "clean", "Parent-teacher meeting next Thursday", [_event("parent-teacher meeting", start_time="next thursday")]),
        _row(
            "clean_14",
            "clean",
            "Flight to New York next Monday at 6:30am",
            [_event("flight to new york", start_time="next monday at 6:30am")],
        ),
        _row(
            "clean_15",
            "clean",
            "Birthday party on November 10th at 6pm",
            [_event("birthday party", start_time="november 10th at 6pm")],
        ),
        _row(
            "clean_16",
            "clean",
            "Coffee at 10am and lunch at 12pm and gym at 6pm",
            [
                _event("coffee", start_time="10am"),
                _event("lunch", start_time="12pm"),
                _event("gym", start_time="6pm"),
            ],
        ),
        _row(
            "clean_17",
            "clean",
            "Weekly 1:1 every Wednesday at 3pm for the next 4 weeks",
            [_event("weekly 1:1", start_time="every wednesday at 3pm", recurrence_type="weekly")],
        ),
        _row(
            "clean_18",
            "clean",
            "Workshop at 1pm-5pm Friday",
            [_event("workshop", start_time="friday at 1pm", end_time="friday at 5pm")],
        ),
        _row(
            "clean_19",
            "clean",
            "Meeting every weekday at 9am",
            [_event("meeting", start_time="every weekday at 9am", recurrence_type="weekly")],
        ),
        _row(
            "clean_20",
            "clean",
            "Vacation from December 20th to January 5th",
            [_event("vacation", start_time="december 20th", end_time="january 5th")],
        ),
    ]


def typo_inputs() -> List[InputRow]:
    return [
        _row("typos_01", "typos", "Lunch meeting Wednesdya at 1pm", [_event("lunch meeting", start_time="wednesday at 1pm")]),
        _row(
            "typos_02",
            "typos",
            "Lnuch Friday at 12pm and dctor Tuesday at 9am",
            [_event("lunch", start_time="friday at 12pm"), _event("doctor", start_time="tuesday at 9am")],
        ),
        _row("typos_03", "typos", "Teem standup tomorow at 9am", [_event("team standup", start_time="tomorrow at 9am")]),
        _row("typos_04", "typos", "Dentst apointment tomorow at 2:30pm", [_event("dentist appointment", start_time="tomorrow at 2:30pm")]),
        _row("typos_05", "typos", "Meting with Sarah next Tuesady at 1pm", [_event("meeting with sarah", start_time="next tuesday at 1pm")]),
        _row(
            "typos_06",
            "typos",
            "Coffe at 10am and code reveiw at 2pm",
            [_event("coffee", start_time="10am"), _event("code review", start_time="2pm")],
        ),
        _row("typos_07", "typos", "Gm session tonigt at 7pm", [_event("gym session", start_time="tonight at 7pm")]),
        _row("typos_08", "typos", "Confrence on Januery 5th at 9am", [_event("conference", start_time="january 5th at 9am")]),
        _row("typos_09", "typos", "Lunch with Jhon on Frday at 12pm", [_event("lunch with john", start_time="friday at 12pm")]),
        _row(
            "typos_10",
            "typos",
            "Wrokshop at 1pm-5pm Frdiay",
            [_event("workshop", start_time="friday at 1pm", end_time="friday at 5pm")],
        ),
        _row("typos_11", "typos", "Evry Monday team meting at 10am", [_event("team meeting", start_time="every monday at 10am", recurrence_type="weekly")]),
        _row("typos_12", "typos", "Birthady party on Novembr 10th at 6pm", [_event("birthday party", start_time="november 10th at 6pm")]),
        _row("typos_13", "typos", "Phne call with client next Wed at 3pm", [_event("phone call with client", start_time="next wednesday at 3pm")]),
        _row("typos_14", "typos", "Parent-techer meeting next Thrusday", [_event("parent-teacher meeting", start_time="next thursday")]),
        _row("typos_15", "typos", "Gym at half past 7 tonigt", [_event("gym", start_time="tonight at 7:30pm")]),
        _row("typos_16", "typos", "Anual review on Decembr 15th at 2pm", [_event("annual review", start_time="december 15th at 2pm")]),
        _row("typos_17", "typos", "Cofee at 10am and luch at 2pm", [_event("coffee", start_time="10am"), _event("lunch", start_time="2pm")]),
        _row("typos_18", "typos", "Doktor appointment next Moday at 9am", [_event("doctor appointment", start_time="next monday at 9am")]),
        _row(
            "typos_19",
            "typos",
            "Yogo class Satuday 8am at Bondi Gym",
            [_event("yoga class", start_time="saturday at 8am", location="bondi gym")],
        ),
        _row("typos_20", "typos", "Projet kickoff nex week at 10am", [_event("project kickoff", start_time="next week at 10am")]),
    ]


def voice_inputs() -> List[InputRow]:
    return [
        _row("voice_01", "voice_to_text", "meeting four next Tuesday at to PM", [_event("meeting", start_time="next tuesday at 2pm")]),
        _row("voice_02", "voice_to_text", "call mom Sunday eight thirty aye em", [_event("call mom", start_time="sunday at 8:30am")]),
        _row(
            "voice_03",
            "voice_to_text",
            "lunch with sarah next too sday at won pm",
            [_event("lunch with sarah", start_time="next tuesday at 1pm")],
        ),
        _row("voice_04", "voice_to_text", "gym session tonight at seven pee em", [_event("gym session", start_time="tonight at 7pm")]),
        _row(
            "voice_05",
            "voice_to_text",
            "dentist appointment tomorrow at two thirty pee em",
            [_event("dentist appointment", start_time="tomorrow at 2:30pm")],
        ),
        _row(
            "voice_06",
            "voice_to_text",
            "team stand up tomorrow morning at nine ay em",
            [_event("team standup", start_time="tomorrow morning at 9am")],
        ),
        _row(
            "voice_07",
            "voice_to_text",
            "coffee at ten am and code review at two pee em",
            [_event("coffee", start_time="10am"), _event("code review", start_time="2pm")],
        ),
        _row(
            "voice_08",
            "voice_to_text",
            "board meeting first monday of each month at nine ay em",
            [_event("board meeting", start_time="first monday of each month at 9am", recurrence_type="monthly")],
        ),
        _row(
            "voice_09",
            "voice_to_text",
            "yoga class saturday at ate ay em at bondi gym",
            [_event("yoga class", start_time="saturday at 8am", location="bondi gym")],
        ),
        _row(
            "voice_10",
            "voice_to_text",
            "flight to new york next monday at six thirty ay em",
            [_event("flight to new york", start_time="next monday at 6:30am")],
        ),
        _row(
            "voice_11",
            "voice_to_text",
            "birthday party november tenth at six pee em",
            [_event("birthday party", start_time="november 10th at 6pm")],
        ),
        _row(
            "voice_12",
            "voice_to_text",
            "workshop at one pee em to five pee em friday",
            [_event("workshop", start_time="friday at 1pm", end_time="friday at 5pm")],
        ),
        _row(
            "voice_13",
            "voice_to_text",
            "weekly one on one every wednesday at three pee em",
            [_event("weekly 1:1", start_time="every wednesday at 3pm", recurrence_type="weekly")],
        ),
        _row(
            "voice_14",
            "voice_to_text",
            "vacation from december twentieth two january fifth",
            [_event("vacation", start_time="december 20th", end_time="january 5th")],
        ),
        _row(
            "voice_15",
            "voice_to_text",
            "lunch friday at twelve pee em doctor tuesday at nine ay em",
            [_event("lunch", start_time="friday at 12pm"), _event("doctor", start_time="tuesday at 9am")],
        ),
        _row(
            "voice_16",
            "voice_to_text",
            "mentoring every other tuesday at five pee em",
            [_event("mentoring", start_time="every other tuesday at 5pm", recurrence_type="weekly")],
        ),
        _row(
            "voice_17",
            "voice_to_text",
            "town hall last friday of each month at three pee em",
            [_event("town hall", start_time="last friday of each month at 3pm", recurrence_type="monthly")],
        ),
        _row(
            "voice_18",
            "voice_to_text",
            "focus block every day this week at two pee em",
            [_event("focus block", start_time="every day this week at 2pm", recurrence_type="daily")],
        ),
        _row("voice_19", "voice_to_text", "call with client in won hour", [_event("call with client", start_time="in 1 hour")]),
        _row(
            "voice_20",
            "voice_to_text",
            "parent teacher meeting next thursday at ate pee em",
            [_event("parent-teacher meeting", start_time="next thursday at 8pm")],
        ),
    ]


def ambiguous_inputs() -> List[InputRow]:
    # Clock time is vague in every ambiguous input; start_time stays null even when a
    # day is mentioned, matching the proposal example ("around 7ish" → null).
    return [
        _row("ambiguous_01", "ambiguous", "Dinner with Sarah next Thursday around 7ish", [_event("dinner with sarah")]),
        _row("ambiguous_02", "ambiguous", "Catch up with the boys sometime this weekend", [_event("catch up with the boys")]),
        _row("ambiguous_03", "ambiguous", "Lunch with Alex sometime next week", [_event("lunch with alex")]),
        _row("ambiguous_04", "ambiguous", "Meeting with the team later today", [_event("meeting with the team")]),
        _row("ambiguous_05", "ambiguous", "Coffee soon with Jamie", [_event("coffee with jamie")]),
        _row("ambiguous_06", "ambiguous", "Dinner around eight tonight", [_event("dinner")]),
        _row("ambiguous_07", "ambiguous", "Catch up with Sam when we can", [_event("catch up with sam")]),
        _row("ambiguous_08", "ambiguous", "Party this weekend sometime", [_event("party")]),
        _row("ambiguous_09", "ambiguous", "Workout early morning tomorrow", [_event("workout")]),
        _row("ambiguous_10", "ambiguous", "Call mom in the evening Sunday", [_event("call mom")]),
        _row("ambiguous_11", "ambiguous", "Study session this week sometime", [_event("study session")]),
        _row("ambiguous_12", "ambiguous", "Brunch with friends mid-morning Saturday", [_event("brunch with friends")]),
        _row("ambiguous_13", "ambiguous", "Team sync when everyone's free next week", [_event("team sync")]),
        _row("ambiguous_14", "ambiguous", "Dinner with parents around dinnertime Friday", [_event("dinner with parents")]),
        _row("ambiguous_15", "ambiguous", "Meeting after lunch next Tuesday", [_event("meeting")]),
        _row("ambiguous_16", "ambiguous", "Gym session later this week", [_event("gym session")]),
        _row("ambiguous_17", "ambiguous", "Coffee with mentor sometime Thursday", [_event("coffee with mentor")]),
        _row("ambiguous_18", "ambiguous", "Presentation afternoon next Wednesday", [_event("presentation")]),
        _row("ambiguous_19", "ambiguous", "Happy hour end of day Friday", [_event("happy hour")]),
        _row("ambiguous_20", "ambiguous", "Lunch downtown around noonish", [_event("lunch")]),
    ]


def missing_inputs() -> List[InputRow]:
    return [
        _row(
            "missing_01",
            "missing_fields",
            "Meeting with John next Tuesday (no time)",
            [_event("meeting with john", start_time="next tuesday")],
        ),
        _row(
            "missing_02",
            "missing_fields",
            "Lunch on Friday (no time, no location)",
            [_event("lunch", start_time="friday")],
        ),
        _row("missing_03", "missing_fields", "Dinner with Sarah (no date or time)", [_event("dinner with sarah")]),
        _row("missing_04", "missing_fields", "Gym session (no time)", [_event("gym session")]),
        _row("missing_05", "missing_fields", "Call mom (no time)", [_event("call mom")]),
        _row("missing_06", "missing_fields", "Team meeting next week (no time)", [_event("team meeting")]),
        _row("missing_07", "missing_fields", "Doctor appointment (no date or time)", [_event("doctor appointment")]),
        _row(
            "missing_08",
            "missing_fields",
            "Coffee with Alex tomorrow (no time)",
            [_event("coffee with alex", start_time="tomorrow")],
        ),
        _row(
            "missing_09",
            "missing_fields",
            "Workshop at the office (no time)",
            [_event("workshop", location="the office")],
        ),
        _row("missing_10", "missing_fields", "Birthday party (no date or time or location)", [_event("birthday party")]),
        _row("missing_11", "missing_fields", "Conference call (no time)", [_event("conference call")]),
        _row("missing_12", "missing_fields", "Lunch with Sarah (no time, no date)", [_event("lunch with sarah")]),
        _row("missing_13", "missing_fields", "Dentist (no details)", [_event("dentist")]),
        _row(
            "missing_14",
            "missing_fields",
            "Meeting with John and Sarah next Tuesday (no time)",
            [_event("meeting with john and sarah", start_time="next tuesday")],
        ),
        _row(
            "missing_15",
            "missing_fields",
            "Yoga at Bondi Gym (no time)",
            [_event("yoga", location="bondi gym")],
        ),
        _row("missing_16", "missing_fields", "Flight to Melbourne (no date or time)", [_event("flight to melbourne")]),
        _row("missing_17", "missing_fields", "Code review (no time)", [_event("code review")]),
        _row(
            "missing_18",
            "missing_fields",
            "Standup every Monday (no time)",
            [_event("standup", recurrence_type="weekly")],
        ),
        _row(
            "missing_19",
            "missing_fields",
            "Interview next Thursday (no time)",
            [_event("interview", start_time="next thursday")],
        ),
        _row(
            "missing_20",
            "missing_fields",
            "Pick up kids from school Friday (no time)",
            [_event("pick up kids from school", start_time="friday")],
        ),
    ]


def all_inputs() -> List[InputRow]:
    return (
        clean_inputs()
        + typo_inputs()
        + voice_inputs()
        + ambiguous_inputs()
        + missing_inputs()
    )
