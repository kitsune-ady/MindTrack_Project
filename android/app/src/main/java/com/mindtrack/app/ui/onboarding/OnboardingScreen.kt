package com.mindtrack.app.ui.onboarding

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.ui.platform.LocalContext
import com.mindtrack.app.MindTrackApp
import com.mindtrack.app.data.SettingsStore
import com.mindtrack.app.domain.Wellbeing

val USAGE_BANDS = listOf("Under 2 hours", "2–4 hours", "4–6 hours", "6+ hours", "Not sure")

private const val LAST_STEP = 4   // 0 welcome, 1 about you, 2 baseline, 3 privacy & consent, 4 done

class OnboardingViewModel(private val s: SettingsStore) : ViewModel() {
    var step by mutableIntStateOf(s.step.coerceIn(0, LAST_STEP - 1)) // never resume past consent
    var name by mutableStateOf(s.name.value)
    var usageBand by mutableStateOf(s.baselineUsage)
    var wellbeing by mutableStateOf(s.baselineWellbeing)
    var understood by mutableStateOf(false) // consent is never pre-ticked or restored

    private fun persist() = s.saveProgress(step, name, usageBand, wellbeing)
    fun next() { step++; persist() }
    fun back() { if (step > 0) { step--; persist() } }
    fun acceptAndContinue() { s.recordConsent(); step = LAST_STEP; persist() }
    fun finish(onFinished: () -> Unit) { persist(); s.completeOnboarding(); onFinished() }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun OnboardingScreen(onFinished: () -> Unit) {
    val settings = (LocalContext.current.applicationContext as MindTrackApp).settings
    val vm: OnboardingViewModel = viewModel(factory = viewModelFactory { initializer { OnboardingViewModel(settings) } })

    BackHandler(enabled = vm.step in 1 until LAST_STEP) { vm.back() }

    Column(Modifier.fillMaxSize().padding(horizontal = 24.dp, vertical = 16.dp)) {
        if (vm.step in 1 until LAST_STEP) {
            Text("Step ${vm.step} of ${LAST_STEP - 1}", style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.secondary)
            LinearProgressIndicator(progress = { vm.step / (LAST_STEP - 1f) }, modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
        }

        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            when (vm.step) {
                0 -> {
                    Spacer(Modifier.height(32.dp))
                    Text("Welcome to MindTrack", style = MaterialTheme.typography.headlineLarge)
                    Text("A calm place to notice how your screen time, movement and mood fit together over time.",
                        style = MaterialTheme.typography.bodyLarge)
                    Text("• Takes about a minute to set up\n• Everything stays on this phone\n• No scores, no judgement — just your own patterns",
                        style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.secondary)
                }
                1 -> {
                    Text("What should we call you?", style = MaterialTheme.typography.headlineSmall)
                    Text("Optional. A first name or nickname is enough — it's only used for the greeting on your Home screen.")
                    OutlinedTextField(vm.name, { vm.name = it.take(30) }, label = { Text("Name or nickname") },
                        singleLine = true, modifier = Modifier.fillMaxWidth())
                    Text("We don't ask for your age, gender or location, because the app doesn't need them.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                }
                2 -> {
                    Text("Your starting point", style = MaterialTheme.typography.headlineSmall)
                    Text("Rough guesses are fine, and you can skip this. These are kept separate from your daily entries and are never counted as logged days.")
                    Text("On a typical day, how much do you use your phone?", style = MaterialTheme.typography.titleMedium)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        USAGE_BANDS.forEachIndexed { i, label ->
                            FilterChip(selected = vm.usageBand == i, onClick = { vm.usageBand = if (vm.usageBand == i) null else i },
                                label = { Text(label) })
                        }
                    }
                    Text("How have you been feeling lately?", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 8.dp))
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Wellbeing.entries.forEach { w ->
                            FilterChip(selected = vm.wellbeing == w.value, onClick = { vm.wellbeing = if (vm.wellbeing == w.value) null else w.value },
                                label = { Text(w.label) })
                        }
                    }
                }
                3 -> {
                    Text("Your privacy", style = MaterialTheme.typography.headlineSmall)
                    Text("• Your entries are stored only on this device.\n" +
                        "• MindTrack doesn't upload, share or sell anything, and device backup is off.\n" +
                        "• You can export or delete everything any time from Profile.\n" +
                        "• If this ever changes, we'll ask you separately — it will never be a condition of using the app.")
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Please note", style = MaterialTheme.typography.titleSmall)
                            Text("MindTrack helps you notice patterns. It isn't a medical or diagnostic tool and can't tell you whether " +
                                "something is wrong. If you're finding things hard, talking to someone you trust or a health professional can help — " +
                                "and in an emergency, contact your local emergency services.")
                        }
                    }
                    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(vm.understood, { vm.understood = it })
                        Text("I understand how my data is stored and that MindTrack isn't a medical tool.",
                            Modifier.weight(1f))
                    }
                }
                else -> {
                    Spacer(Modifier.height(32.dp))
                    Text(if (vm.name.isBlank()) "You're all set" else "You're all set, ${vm.name.trim()}", style = MaterialTheme.typography.headlineLarge)
                    Text("Log whenever it suits you. A missed day is just a missed day — it's never a failure.",
                        style = MaterialTheme.typography.bodyLarge)
                    Text("Reminders are optional and you can turn them on later in Profile.",
                        color = MaterialTheme.colorScheme.secondary)
                }
            }
        }

        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            val primary = Modifier.fillMaxWidth().heightIn(min = 48.dp)
            when (vm.step) {
                0 -> Button({ vm.next() }, primary) { Text("Get started") }
                1, 2 -> {
                    Button({ vm.next() }, primary) { Text("Continue") }
                    TextButton({ vm.next() }, primary) { Text("Skip") }
                }
                3 -> Button({ vm.acceptAndContinue() }, primary, enabled = vm.understood) { Text("Agree and continue") }
                else -> Button({ vm.finish(onFinished) }, primary) { Text("Go to Home") }
            }
        }
    }
}
