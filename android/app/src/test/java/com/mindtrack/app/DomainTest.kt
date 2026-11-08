package com.mindtrack.app

import com.mindtrack.app.data.DailyRecord
import com.mindtrack.app.domain.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class DomainTest {
    @Test fun socialPlusGamingCannotExceedTotal() {
        val r = parseUsage("100", "80", "40", "")
        assertTrue(Field.TOTAL in r.errors)
    }
    @Test fun rejectsMoreThanADay() = assertTrue(Field.TOTAL in parseUsage("1441", "", "", "").errors)
    @Test fun blankIsNullNotZero() {
        val r = parseUsage("", "", "", "")
        assertNull(r.total); assertTrue(r.errors.isEmpty())
    }
    @Test fun missingDaysAreNullNotZero() {
        val end = LocalDate.of(2026, 11, 6)
        val b = buildUsageBuckets(Period.WEEK, end, listOf(DailyRecord("2026-11-06", totalMinutes = 120)))
        assertEquals(7, b.size); assertEquals(120, b.last().avgMinutes); assertNull(b.first().avgMinutes)
    }
    @Test fun weeklyAverageUsesLoggedDaysOnly() {
        val end = LocalDate.of(2026, 11, 6)
        val recs = listOf(DailyRecord("2026-11-06", totalMinutes = 100), DailyRecord("2026-11-05", totalMinutes = 200))
        assertEquals(150, buildUsageBuckets(Period.FOUR_WEEKS, end, recs).last().avgMinutes)
    }
}
