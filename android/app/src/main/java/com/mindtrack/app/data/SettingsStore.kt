package com.mindtrack.app.data

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

const val PRIVACY_POLICY_VERSION = 1

/**
 * Small on-device settings: onboarding progress, optional profile, baseline and the consent record.
 * Baseline answers live here - NOT in DailyRecord - so they never blend into logged data.
 */
class SettingsStore(context: Context) {
    private val p = context.getSharedPreferences("mindtrack_settings", Context.MODE_PRIVATE)

    private val _onboarded = MutableStateFlow(p.getBoolean("onboarded", false))
    val onboarded: StateFlow<Boolean> = _onboarded

    private val _name = MutableStateFlow(p.getString("name", "") ?: "")
    val name: StateFlow<String> = _name

    private val _reminderOn = MutableStateFlow(p.getBoolean("reminder_on", false))
    val reminderEnabled: StateFlow<Boolean> = _reminderOn
    private val _reminderHour = MutableStateFlow(p.getInt("reminder_hour", 20))
    val reminderHour: StateFlow<Int> = _reminderHour
    private val _reminderMinute = MutableStateFlow(p.getInt("reminder_minute", 0))
    val reminderMinute: StateFlow<Int> = _reminderMinute

    fun setReminder(enabled: Boolean, hour: Int, minute: Int) {
        p.edit().putBoolean("reminder_on", enabled).putInt("reminder_hour", hour).putInt("reminder_minute", minute).apply()
        _reminderOn.value = enabled; _reminderHour.value = hour; _reminderMinute.value = minute
    }

    val step: Int get() = p.getInt("step", 0)
    val baselineUsage: Int? get() = p.getInt("baseline_usage", -1).takeIf { it >= 0 }
    val baselineWellbeing: Int? get() = p.getInt("baseline_wellbeing", -1).takeIf { it >= 0 }
    val consentVersion: Int get() = p.getInt("consent_version", 0)
    val consentAt: Long get() = p.getLong("consent_at", 0L)

    /** Saved on every step change so an interruption doesn't force a restart. */
    fun saveProgress(step: Int, name: String, usageBand: Int?, wellbeing: Int?) {
        p.edit()
            .putInt("step", step)
            .putString("name", name.trim())
            .putInt("baseline_usage", usageBand ?: -1)
            .putInt("baseline_wellbeing", wellbeing ?: -1)
            .apply()
        _name.value = name.trim()
    }

    fun recordConsent() {
        p.edit().putInt("consent_version", PRIVACY_POLICY_VERSION)
            .putLong("consent_at", System.currentTimeMillis()).apply()
    }

    fun completeOnboarding() {
        p.edit().putBoolean("onboarded", true).apply()
        _onboarded.value = true
    }
}
