package com.mindtrack.app.ui.log

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.ui.factory
import com.mindtrack.app.ui.summary
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import java.time.LocalDate

class LogViewModel(repo: RecordRepository) : ViewModel() {
    val records = repo.observeAll().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)
}

@Composable
fun LogScreen(onOpenEntry: (LocalDate) -> Unit) {
    val vm: LogViewModel = viewModel(factory = factory { LogViewModel(it) })
    val records by vm.records.collectAsStateWithLifecycle()
    val list = records

    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
            Text("Log", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.padding(top = 20.dp, bottom = 12.dp))
            when {
                list == null -> Box(Modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator() }
                list.isEmpty() -> Text("No entries yet. Tap Add entry to record today — you can always edit it later.",
                    color = MaterialTheme.colorScheme.secondary)
                else -> LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), contentPadding = PaddingValues(bottom = 96.dp)) {
                    items(list, key = { it.date }) { r ->
                        Card(Modifier.fillMaxWidth().clickable { onOpenEntry(LocalDate.parse(r.date)) }) {
                            Column(Modifier.padding(16.dp).heightIn(min = 48.dp)) {
                                Text(r.date, style = MaterialTheme.typography.titleMedium)
                                Text(r.summary(), style = MaterialTheme.typography.bodyMedium)
                            }
                        }
                    }
                }
            }
        }
        ExtendedFloatingActionButton(
            onClick = { onOpenEntry(LocalDate.now()) },
            icon = { Icon(Icons.Default.Add, null) }, text = { Text("Add entry") },
            modifier = Modifier.align(Alignment.BottomEnd).padding(20.dp),
        )
    }
}
