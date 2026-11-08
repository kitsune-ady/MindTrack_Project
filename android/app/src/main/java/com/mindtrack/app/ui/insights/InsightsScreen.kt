package com.mindtrack.app.ui.insights

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.mindtrack.app.data.DailyRecord
import com.mindtrack.app.data.RecordRepository
import com.mindtrack.app.domain.*
import com.mindtrack.app.ui.factory
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import java.time.LocalDate

@OptIn(ExperimentalCoroutinesApi::class)
class InsightsViewModel(repo: RecordRepository) : ViewModel() {
    val period = MutableStateFlow(Period.WEEK)
    val records: StateFlow<List<DailyRecord>> = period.flatMapLatest { p ->
        val end = LocalDate.now()
        repo.observeRange(end.minusDays(p.days - 1L), end)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InsightsScreen() {
    val vm: InsightsViewModel = viewModel(factory = factory { InsightsViewModel(it) })
    val period by vm.period.collectAsStateWithLifecycle()
    val records by vm.records.collectAsStateWithLifecycle()
    val buckets = buildUsageBuckets(period, LocalDate.now(), records)
    val logged = daysLogged(buckets)

    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Insights", style = MaterialTheme.typography.headlineMedium)
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            Period.entries.forEachIndexed { i, p ->
                SegmentedButton(selected = p == period, onClick = { vm.period.value = p },
                    shape = SegmentedButtonDefaults.itemShape(i, Period.entries.size)) { Text(p.label) }
            }
        }

        if (logged < MIN_DAYS_FOR_TREND) {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Not enough to show a pattern yet", style = MaterialTheme.typography.titleMedium)
                    Text("Log screen time on at least $MIN_DAYS_FOR_TREND days in this period ($logged so far). " +
                        "Patterns from a couple of days can be misleading.")
                }
            }
        } else {
            val avg = buckets.mapNotNull { it.avgMinutes }.average().toInt()
            Text("Average screen time on logged days: ${formatMinutes(avg)}", style = MaterialTheme.typography.titleMedium)
            UsageChart(buckets)
            Text("Days without an entry appear as empty outlines, not zero.", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.secondary)

            val counts = records.mapNotNull { Wellbeing.from(it.wellbeing) }.groupingBy { it }.eachCount()
            if (counts.isNotEmpty()) {
                Text("Self-reported wellbeing", style = MaterialTheme.typography.titleMedium)
                Text(Wellbeing.entries.filter { it in counts }.joinToString(" · ") { "${it.label} ×${counts[it]}" })
            }
            Text("These are your own entries shown side by side — they describe patterns, not causes.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
        }
    }
}

@Composable
private fun UsageChart(buckets: List<Bucket>) {
    val max = (buckets.mapNotNull { it.avgMinutes }.maxOrNull() ?: 60).coerceAtLeast(60)
    val desc = buckets.joinToString("; ") { "${it.label}: ${if (it.avgMinutes == null) "no entry" else formatMinutes(it.avgMinutes)}" }
    val fill = MaterialTheme.colorScheme.primary
    val outline = MaterialTheme.colorScheme.outline
    Column(Modifier.semantics { contentDescription = "Screen time chart. $desc" }) {
        Canvas(Modifier.fillMaxWidth().height(160.dp)) {
            val slot = size.width / buckets.size
            val bar = slot * 0.6f
            buckets.forEachIndexed { i, b ->
                val x = i * slot + (slot - bar) / 2
                val m = b.avgMinutes
                if (m == null) {
                    drawRoundRect(outline, Offset(x, size.height - 12f), Size(bar, 12f), CornerRadius(6f), style = Stroke(3f))
                } else {
                    val h = size.height * m / max
                    drawRoundRect(fill, Offset(x, size.height - h), Size(bar, h), CornerRadius(8f))
                }
            }
        }
        Row(Modifier.fillMaxWidth()) {
            buckets.forEach { Text(it.label, Modifier.weight(1f), style = MaterialTheme.typography.labelSmall, textAlign = TextAlign.Center) }
        }
        Text("Minutes per day, scaled 0–${formatMinutes(max)}", style = MaterialTheme.typography.labelSmall)
    }
}
