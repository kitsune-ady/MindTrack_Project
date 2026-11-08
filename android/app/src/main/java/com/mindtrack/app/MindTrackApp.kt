package com.mindtrack.app

import android.app.Application
import com.mindtrack.app.data.AppDatabase
import com.mindtrack.app.data.RecordRepository

class MindTrackApp : Application() {
    val repository: RecordRepository by lazy { RecordRepository(AppDatabase.create(this).dao()) }
}
