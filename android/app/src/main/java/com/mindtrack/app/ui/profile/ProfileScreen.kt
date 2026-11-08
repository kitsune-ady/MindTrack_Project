package com.mindtrack.app.ui.profile

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.MindTrackApp
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.reminders.Reminders
import com.mindtrack.app.ui.factory
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId

class ProfileViewModel(private val repo: RecordRepository) : ViewModel() {
    fun clearAll(onDone: () -> Unit) { viewModelScope.launch { repo.clearAll(); onDone() } }
    fun exportCsv(onReady: (String) -> Unit) {
        viewModelScope.launch {
            val rows = repo.observeAll().first().sortedBy { it.date }
            val header = "date,total_min,social_min,gaming_min,activity_min,stress_1to5,wellbeing_1to4,note"
            val body = rows.joinToString("\n") { r ->
                listOf<Any?>(r.date, r.totalMinutes, r.socialMinutes, r.gamingMinutes, r.activityMinutes, r.stress, r.wellbeing,
                    "\"" + (r.note ?: "").replace("\"", "\"\"") + "\"").joinToString(",") { it?.toString() ?: "" }
            }
            onReady("$header\n$body")
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen() {
    val vm: ProfileViewModel = viewModel(factory = factory { ProfileViewModel(it) })
    val ctx = LocalContext.current
    val settings = (ctx.applicationContext as MindTrackApp).settings
    val remOn by settings.reminderEnabled.collectAsStateWithLifecycle()
    val hour by settings.reminderHour.collectAsStateWithLifecycle()
    val minute by settings.reminderMinute.collectAsStateWithLifecycle()

    var confirmClear by remember { mutableStateOf(false) }
    var cleared by remember { mutableStateOf(false) }
    var showTimePicker by remember { mutableStateOf(false) }
    var permissionDenied by remember { mutableStateOf(false) }

    fun enable() {
        settings.setReminder(true, hour, minute)
        Reminders.schedule(ctx, hour, minute)
        permissionDenied = false
    }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) enable() else permissionDenied = true
    }
    fun turnOn() {
        // Ask only now, at the moment the person chooses reminders.
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS) else enable()
    }
    fun turnOff() {
        settings.setReminder(false, hour, minute); Reminders.cancel(ctx)
    }
    val timeText = "%02d:%02d".format(hour, minute)

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Profile & privacy", style = MaterialTheme.typography.headlineMedium)

        // ---- Reminders ----
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Daily reminder", style = MaterialTheme.typography.titleMedium)
                        Text("Optional. A gentle nudge — skipped if you've already logged today.",
                            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                    }
                    Switch(checked = remOn, onCheckedChange = { if (it) turnOn() else turnOff() })
                }
                if (remOn) {
                    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text("Time: $timeText", Modifier.weight(1f))
                        TextButton(onClick = { showTimePicker = true }) { Text("Change") }
                    }
                    if (!Reminders.canNotify(ctx)) {
                        Text("Notifications are turned off for MindTrack in your phone's settings, so you won't see the reminder.",
                            color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                        TextButton(onClick = {
                            ctx.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                                .putExtra(Settings.EXTRA_APP_PACKAGE, ctx.packageName))
                        }) { Text("Open notification settings") }
                    } else {
                        TextButton(onClick = { Reminders.sendTest(ctx) }) { Text("Send a test reminder") }
                    }
                }
                if (permissionDenied) Text(
                    "No problem — reminders are off. You can turn them on later if you change your mind.",
                    style = MaterialTheme.typography.bodySmall)
            }
        }

        // ---- Privacy & data ----
        Text("Your entries are stored only on this device. Nothing is uploaded, and device backup is turned off.")
        if (settings.consentAt > 0) Text(
            "Privacy notice v${settings.consentVersion} accepted on ${Instant.ofEpochMilli(settings.consentAt).atZone(ZoneId.systemDefault()).toLocalDate()}",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)

        Button(onClick = {
            vm.exportCsv { csv ->
                ctx.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                    type = "text/csv"; putExtra(Intent.EXTRA_TEXT, csv)
                }, "Export your data"))
            }
        }, Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Export my data (CSV)") }

        OutlinedButton(onClick = { confirmClear = true }, Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
            Text("Clear all logs", color = MaterialTheme.colorScheme.error)
        }
        if (cleared) Text("All logs cleared. Your dashboard and trends are back to empty.")
    }

    if (showTimePicker) {
        val state = rememberTimePickerState(initialHour = hour, initialMinute = minute, is24Hour = true)
        AlertDialog(
            onDismissRequest = { showTimePicker = false },
            title = { Text("Reminder time") },
            text = { TimePicker(state = state) },
            confirmButton = {
                TextButton(onClick = {
                    settings.setReminder(remOn, state.hour, state.minute)
                    if (remOn) Reminders.schedule(ctx, state.hour, state.minute)
                    showTimePicker = false
                }) { Text("Save") }
            },
            dismissButton = { TextButton(onClick = { showTimePicker = false }) { Text("Cancel") } },
        )
    }

    if (confirmClear) AlertDialog(
        onDismissRequest = { confirmClear = false },
        title = { Text("Clear all logs?") },
        text = { Text("This removes every daily entry and wellbeing check-in from this device, and the trends built from them. " +
            "It can't be undone. Consider exporting first.") },
        confirmButton = { TextButton(onClick = { vm.clearAll { cleared = true }; confirmClear = false }) { Text("Clear everything") } },
        dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } },
    )
}
