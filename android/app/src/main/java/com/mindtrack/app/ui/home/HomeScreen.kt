package com.mindtrack.app.ui.home

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.data.DailyRecord
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.ui.factory
import com.mindtrack.app.ui.summary
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import java.time.LocalDate

class HomeViewModel(repo: RecordRepository) : ViewModel() {
    val today = repo.observe(LocalDate.now())
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)
}

@Composable
fun HomeScreen(onOpenEntry: (LocalDate) -> Unit, onOpenInsights: () -> Unit) {
    val vm: HomeViewModel = viewModel(factory = factory { HomeViewModel(it) })
    val today: DailyRecord? by vm.today.collectAsStateWithLifecycle()

    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Today", style = MaterialTheme.typography.headlineMedium)
        Text("A few honest minutes is enough. There's no wrong way to log a day.",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.secondary)

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(if (today == null) "Not logged yet" else "Logged", style = MaterialTheme.typography.titleMedium)
                Text(today?.summary() ?: "Record your screen time, movement and how you're feeling.")
                Button(onClick = { onOpenEntry(LocalDate.now()) }, Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                    Text(if (today == null) "Start today's entry" else "Edit today's entry")
                }
            }
        }
        OutlinedButton(onClick = onOpenInsights, Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("See my patterns") }
    }
}
