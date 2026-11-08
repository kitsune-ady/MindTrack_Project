package com.mindtrack.app.ui.profile

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.ui.factory
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

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

@Composable
fun ProfileScreen() {
    val vm: ProfileViewModel = viewModel(factory = factory { ProfileViewModel(it) })
    val ctx = LocalContext.current
    var confirmClear by remember { mutableStateOf(false) }
    var cleared by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Profile & privacy", style = MaterialTheme.typography.headlineMedium)
        Text("Your entries are stored only on this device. Nothing is uploaded, and device backup is turned off.")

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

    if (confirmClear) AlertDialog(
        onDismissRequest = { confirmClear = false },
        title = { Text("Clear all logs?") },
        text = { Text("This removes every daily entry and wellbeing check-in from this device, and the trends built from them. " +
            "It can't be undone. Consider exporting first.") },
        confirmButton = { TextButton(onClick = { vm.clearAll { cleared = true }; confirmClear = false }) { Text("Clear everything") } },
        dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } },
    )
}
