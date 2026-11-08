package com.mindtrack.app.domain

import com.mindtrack.app.data.DailyRecord
import java.time.LocalDate

/** Ordinal self-report. Deliberately NOT converted to a 0-100 score. */
enum class Wellbeing(val value: Int, val label: String) {
    POOR(1, "Poor"), FAIR(2, "Fair"), GOOD(3, "Good"), EXCELLENT(4, "Excellent");

    companion object { fun from(v: Int?) = entries.firstOrNull { it.value == v } }
}

const val MAX_MINUTES_PER_DAY = 24 * 60

fun formatMinutes(m: Int?): String = when {
    m == null -> "—"
    m < 60 -> "${m}m"
    else -> "${m / 60}h ${m % 60}m"
}

// ---------- validation ----------
enum class Field { TOTAL, SOCIAL, GAMING, ACTIVITY, FORM }

data class ParsedUsage(
    val total: Int?, val social: Int?, val gaming: Int?, val activity: Int?,
    val errors: Map<Field, String>,
)

fun parseUsage(total: String, social: String, gaming: String, activity: String): ParsedUsage {
    val errors = mutableMapOf<Field, String>()
    fun parse(text: String, f: Field): Int? {
        val t = text.trim()
        if (t.isEmpty()) return null
        val n = t.toIntOrNull()
        if (n == null || n < 0) { errors[f] = "Enter whole minutes (0 or more)"; return null }
        if (n > MAX_MINUTES_PER_DAY) { errors[f] = "A day has only $MAX_MINUTES_PER_DAY minutes"; return null }
        return n
    }
    val t = parse(total, Field.TOTAL)
    val s = parse(social, Field.SOCIAL)
    val g = parse(gaming, Field.GAMING)
    val a = parse(activity, Field.ACTIVITY)
    if (t == null && (s != null || g != null) && Field.TOTAL !in errors)
        errors[Field.TOTAL] = "Add total screen time first — social and gaming are part of it"
    if (t != null && ((s ?: 0) + (g ?: 0)) > t && Field.TOTAL !in errors)
        errors[Field.TOTAL] = "Social + gaming can't be more than total screen time"
    return ParsedUsage(t, s, g, a, errors)
}

// ---------- insights ----------
enum class Period(val label: String, val days: Int) { WEEK("7 days", 7), FOUR_WEEKS("4 weeks", 28) }

data class Bucket(val label: String, val avgMinutes: Int?, val daysLogged: Int)

const val MIN_DAYS_FOR_TREND = 3

/** Week: one bucket per day. 4 weeks: weekly averages of LOGGED days only. Missing = null, never zero. */
fun buildUsageBuckets(period: Period, end: LocalDate, records: List<DailyRecord>): List<Bucket> {
    val byDate = records.associateBy { it.date }
    val start = end.minusDays(period.days - 1L)
    return when (period) {
        Period.WEEK -> (0 until 7).map { i ->
            val d = start.plusDays(i.toLong())
            val m = byDate[d.toString()]?.totalMinutes
            Bucket(d.dayOfWeek.name.take(3).lowercase().replaceFirstChar { it.uppercase() }, m, if (m != null) 1 else 0)
        }
        Period.FOUR_WEEKS -> (0 until 4).map { w ->
            val vals = (0 until 7).mapNotNull { i ->
                byDate[start.plusDays((w * 7 + i).toLong()).toString()]?.totalMinutes
            }
            Bucket("W${w + 1}", if (vals.isEmpty()) null else vals.average().toInt(), vals.size)
        }
    }
}

fun daysLogged(buckets: List<Bucket>) = buckets.sumOf { it.daysLogged }
