package com.mindtrack.app

import android.app.Application
import com.mindtrack.app.data.AppDatabase
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.data.SettingsStore

class MindTrackApp : Application() {
    val settings: SettingsStore by lazy { SettingsStore(this) }
    val repository: RecordRepository by lazy { RecordRepository(AppDatabase.create(this).dao()) }
}
