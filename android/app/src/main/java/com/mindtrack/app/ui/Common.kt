package com.mindtrack.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewmodel.CreationExtras
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.mindtrack.app.MindTrackApp
import com.mindtrack.app.data.DailyRecord
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.domain.Wellbeing
import com.mindtrack.app.domain.formatMinutes

fun CreationExtras.repo(): RecordRepository = (this[APPLICATION_KEY] as MindTrackApp).repository

inline fun <reified VM : ViewModel> factory(crossinline create: (RecordRepository) -> VM) =
    viewModelFactory { initializer { create(repo()) } }

fun DailyRecord.summary(): String = buildList {
    totalMinutes?.let { add("Screen ${formatMinutes(it)}") }
    activityMinutes?.let { add("Active ${formatMinutes(it)}") }
    Wellbeing.from(wellbeing)?.let { add("Wellbeing: ${it.label}") }
}.ifEmpty { listOf("Nothing recorded") }.joinToString(" · ")
