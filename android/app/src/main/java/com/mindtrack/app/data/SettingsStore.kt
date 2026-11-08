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
