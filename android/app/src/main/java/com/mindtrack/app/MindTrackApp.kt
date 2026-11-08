package com.mindtrack.app

import android.app.Application
import com.mindtrack.app.data.AppDatabase
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.data.SettingsStore
import com.mindtrack.app.reminders.Reminders

class MindTrackApp : Application() {
    override fun onCreate() {
        super.onCreate()
        if (settings.reminderEnabled.value) Reminders.schedule(this, settings.reminderHour.value, settings.reminderMinute.value)
    }

    val settings: SettingsStore by lazy { SettingsStore(this) }
    val repository: RecordRepository by lazy { RecordRepository(AppDatabase.create(this).dao()) }
}
