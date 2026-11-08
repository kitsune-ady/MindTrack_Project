package com.mindtrack.app.ui.entry

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.data.DailyRecord
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.domain.Field
import com.mindtrack.app.domain.Wellbeing
import com.mindtrack.app.domain.parseUsage
import com.mindtrack.app.ui.factory
import kotlinx.coroutines.launch
import java.time.LocalDate

class EntryViewModel(private val repo: RecordRepository, val date: LocalDate) : ViewModel() {
    var total by mutableStateOf(""); var social by mutableStateOf("")
    var gaming by mutableStateOf(""); var activity by mutableStateOf("")
    var stress by mutableStateOf<Int?>(null); var wellbeing by mutableStateOf<Int?>(null)
    var note by mutableStateOf("")
    var errors by mutableStateOf<Map<Field, String>>(emptyMap())
    var exists by mutableStateOf(false)

    init {
        viewModelScope.launch {
            repo.get(date)?.let { r ->  // open the selected record's REAL values
                exists = true
                total = r.totalMinutes?.toString() ?: ""; social = r.socialMinutes?.toString() ?: ""
                gaming = r.gamingMinutes?.toString() ?: ""; activity = r.activityMinutes?.toString() ?: ""
                stress = r.stress; wellbeing = r.wellbeing; note = r.note ?: ""
            }
        }
    }

    fun save(onDone: () -> Unit) {
        val u = parseUsage(total, social, gaming, activity)
        val e = u.errors.toMutableMap()
        val empty = u.total == null && u.social == null && u.gaming == null && u.activity == null &&
            stress == null && wellbeing == null && note.isBlank()
        if (empty) e[Field.FORM] = "Add at least one thing to save"
        errors = e
        if (e.isNotEmpty()) return
        viewModelScope.launch {
            repo.save(DailyRecord(date.toString(), u.total, u.social, u.gaming, u.activity,
                stress, wellbeing, note.trim().ifEmpty { null }))
            onDone()
        }
    }

    fun delete(onDone: () -> Unit) { viewModelScope.launch { repo.delete(date); onDone() } }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun EntryScreen(date: LocalDate, onDone: () -> Unit) {
    val vm: EntryViewModel = viewModel(key = "entry-$date", factory = factory { EntryViewModel(it, date) })
    var confirmDelete by remember { mutableStateOf(false) }

    @Composable
    fun MinutesField(label: String, value: String, f: Field, set: (String) -> Unit) =
        OutlinedTextField(
            value = value, onValueChange = { set(it.filter(Char::isDigit)) },
            label = { Text("$label (minutes)") }, singleLine = true,
            isError = f in vm.errors, supportingText = { vm.errors[f]?.let { Text(it) } },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth(),
        )

    Scaffold(topBar = {
        TopAppBar(title = { Text(date.toString()) },
            navigationIcon = { IconButton(onClick = onDone) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } })
    }) { pad ->
        Column(Modifier.padding(pad).padding(horizontal = 20.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {

            Text("Technology & activity", style = MaterialTheme.typography.titleMedium)
            MinutesField("Total screen time", vm.total, Field.TOTAL) { vm.total = it }
            MinutesField("Social media", vm.social, Field.SOCIAL) { vm.social = it }
            MinutesField("Gaming", vm.gaming, Field.GAMING) { vm.gaming = it }
            MinutesField("Physical activity", vm.activity, Field.ACTIVITY) { vm.activity = it }

            Text("How are you doing?", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 8.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Wellbeing.entries.forEach { w ->
                    FilterChip(selected = vm.wellbeing == w.value,
                        onClick = { vm.wellbeing = if (vm.wellbeing == w.value) null else w.value },
                        label = { Text(w.label) })
                }
            }
            Text("Stress today (1 calm – 5 very stressed)", style = MaterialTheme.typography.bodyMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                (1..5).forEach { s ->
                    FilterChip(selected = vm.stress == s,
                        onClick = { vm.stress = if (vm.stress == s) null else s },
                        label = { Text("$s") })
                }
            }
            OutlinedTextField(vm.note, { vm.note = it }, label = { Text("Note (optional)") },
                modifier = Modifier.fillMaxWidth(), minLines = 3)

            vm.errors[Field.FORM]?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = { vm.save(onDone) }, Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Save") }
            if (vm.exists) TextButton(onClick = { confirmDelete = true }, Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                Text("Delete this entry", color = MaterialTheme.colorScheme.error)
            }
            Spacer(Modifier.height(24.dp))
        }
    }

    if (confirmDelete) AlertDialog(
        onDismissRequest = { confirmDelete = false },
        title = { Text("Delete this entry?") },
        text = { Text("The record for $date will be removed from this device.") },
        confirmButton = { TextButton(onClick = { vm.delete(onDone) }) { Text("Delete") } },
        dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } },
    )
}
