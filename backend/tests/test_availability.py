"""Tests for the shared free/busy arithmetic."""

from datetime import datetime, timedelta

from backend.services.availability import (
    describe,
    free_slots,
    is_free,
    merge_busy,
    nearest_alternatives,
    spread_by_day,
)


def at(hour, minute=0):
    return datetime(2026, 10, 1, hour, minute)


def busy(*pairs):
    return [(at(*start), at(*end)) for start, end in pairs]


class TestMergeBusy:
    def test_overlapping_and_touching_blocks_join(self):
        merged = merge_busy(busy(((9, 0), (10, 0)), ((9, 30), (11, 0)), ((11, 0), (12, 0))))
        assert merged == [(at(9), at(12))]

    def test_separate_blocks_stay_separate_and_sorted(self):
        merged = merge_busy(busy(((14, 0), (15, 0)), ((9, 0), (10, 0))))
        assert merged == [(at(9), at(10)), (at(14), at(15))]

    def test_zero_length_blocks_are_dropped(self):
        assert merge_busy(busy(((9, 0), (9, 0)))) == []


class TestIsFree:
    def test_touching_a_busy_block_is_still_free(self):
        blocks = busy(((9, 0), (10, 0)))
        assert is_free(blocks, at(10), at(11))
        assert is_free(blocks, at(8), at(9))
        assert not is_free(blocks, at(9, 30), at(10, 30))


class TestFreeSlots:
    def test_finds_gaps_between_meetings(self):
        slots = free_slots(busy(((9, 0), (10, 0)), ((11, 0), (12, 0))), at(9), at(13), 60)
        assert (at(10), at(11)) in slots
        assert (at(12), at(13)) in slots
        assert (at(9), at(10)) not in slots

    def test_respects_working_hours(self):
        slots = free_slots([], at(6), at(22), 60, working_hours=(9, 17))
        assert slots[0][0].hour == 9
        assert all(slot[1].hour <= 17 for slot in slots)

    def test_buffer_keeps_slots_clear_of_meetings(self):
        without = free_slots(busy(((10, 0), (11, 0))), at(9), at(12), 60)
        with_buffer = free_slots(busy(((10, 0), (11, 0))), at(9), at(12), 60, buffer_minutes=15)
        assert (at(9), at(10)) in without
        assert (at(9), at(10)) not in with_buffer

    def test_no_room_means_no_slots(self):
        assert free_slots(busy(((9, 0), (17, 0))), at(9), at(17), 60) == []


    def test_weekdays_only_skips_the_weekend(self):
        # 1 October 2026 is a Thursday; the window runs to Wednesday morning.
        slots = free_slots(
            [], at(9), at(9) + timedelta(days=6), 60, working_hours=(9, 17),
            limit=500, weekdays_only=True,
        )
        assert {slot[0].strftime("%a") for slot in slots} == {"Thu", "Fri", "Mon", "Tue"}


class TestSpreadByDay:
    def test_keeps_a_few_per_day_across_the_whole_day(self):
        day_one = [(at(h), at(h + 1)) for h in range(9, 17)]
        day_two = [(s + timedelta(days=1), e + timedelta(days=1)) for s, e in day_one]
        spread = spread_by_day(day_one + day_two, 3)
        assert [slot[0].hour for slot in spread] == [9, 13, 16, 9, 13, 16]

    def test_leaves_short_days_alone(self):
        slots = [(at(9), at(10)), (at(14), at(15))]
        assert spread_by_day(slots, 8) == slots


class TestNearestAlternatives:
    def test_offers_one_slot_each_side_of_the_clash(self):
        alternatives = nearest_alternatives(busy(((14, 0), (15, 0))), at(14), 60)
        assert alternatives == [(at(13), at(14)), (at(15), at(16))]

    def test_skips_a_second_meeting_to_find_the_next_free_slot(self):
        alternatives = nearest_alternatives(busy(((14, 0), (15, 0)), ((15, 0), (16, 0))), at(14), 60)
        assert alternatives[-1] == (at(16), at(17))

    def test_returns_nothing_when_the_whole_window_is_busy(self):
        blocks = busy(((8, 0), (20, 0)))
        assert nearest_alternatives(blocks, at(14), 60) == []

    def test_a_suggestion_never_overlaps_the_proposed_time(self):
        for slot in nearest_alternatives(busy(((14, 0), (15, 0))), at(14), 30):
            assert slot[1] <= at(14) or slot[0] >= at(14, 30)


class TestDescribe:
    def test_payload_carries_what_the_extension_shows(self):
        payload = describe((at(15), at(16)), proposed_start=at(14))
        assert payload["start"] == at(15).isoformat()
        assert payload["duration_minutes"] == 60
        assert payload["minutes_from_proposed"] == 60
        assert "3:00 PM" in payload["formatted_time"]
