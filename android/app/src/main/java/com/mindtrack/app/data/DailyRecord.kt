package com.mindtrack.app.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * One summary per user-local date (ISO yyyy-MM-dd). All durations are stored in minutes.
 * Null means "not recorded" - never zero. Social/gaming are SUBSETS of totalMinutes.
 */
@Entity(tableName = "daily_records")
data class DailyRecord(
    @PrimaryKey val date: String,
    val totalMinutes: Int? = null,
    val socialMinutes: Int? = null,
    val gamingMinutes: Int? = null,
    val activityMinutes: Int? = null,
    val stress: Int? = null,      // 1 (calm) .. 5 (very stressed), self-reported
    val wellbeing: Int? = null,   // 1..4 ordinal, self-reported (see Wellbeing)
    val note: String? = null,
    val updatedAt: Long = System.currentTimeMillis(),
)
