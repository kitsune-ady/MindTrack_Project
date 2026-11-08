package com.mindtrack.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.EditNote
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.mindtrack.app.ui.entry.EntryScreen
import com.mindtrack.app.ui.home.HomeScreen
import com.mindtrack.app.ui.insights.InsightsScreen
import com.mindtrack.app.ui.log.LogScreen
import com.mindtrack.app.ui.onboarding.OnboardingScreen
import com.mindtrack.app.MindTrackApp
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import com.mindtrack.app.ui.profile.ProfileScreen
import java.time.LocalDate

private enum class Tab(val route: String, val label: String, val icon: ImageVector) {
    Home("home", "Home", Icons.Default.Home),
    Log("log", "Log", Icons.Default.EditNote),
    Insights("insights", "Insights", Icons.Default.Insights),
    Profile("profile", "Profile", Icons.Default.Person),
}

fun entryRoute(date: LocalDate = LocalDate.now()) = "entry/$date"

/** One consistent destination per tab (design review, Priority 1). */
@Composable
fun AppNavigation() {
    val nav = rememberNavController()
    val settings = (LocalContext.current.applicationContext as MindTrackApp).settings
    val startRoute = remember { if (settings.onboarded.value) Tab.Home.route else "onboarding" }
    val entry by nav.currentBackStackEntryAsState()
    val dest = entry?.destination
    val showBar = Tab.entries.any { t -> dest?.hierarchy?.any { it.route == t.route } == true }

    Scaffold(bottomBar = {
        if (showBar) NavigationBar {
            Tab.entries.forEach { tab ->
                NavigationBarItem(
                    selected = dest?.hierarchy?.any { it.route == tab.route } == true,
                    onClick = {
                        nav.navigate(tab.route) {
                            popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                            launchSingleTop = true; restoreState = true
                        }
                    },
                    icon = { Icon(tab.icon, contentDescription = null) },
                    label = { Text(tab.label) },
                )
            }
        }
    }) { padding ->
        NavHost(nav, startDestination = startRoute, modifier = Modifier.padding(padding)) {
            composable("onboarding") {
                OnboardingScreen(onFinished = { nav.navigate(Tab.Home.route) { popUpTo("onboarding") { inclusive = true } } })
            }
            composable(Tab.Home.route) { HomeScreen(onOpenEntry = { nav.navigate(entryRoute(it)) }, onOpenInsights = { nav.navigate(Tab.Insights.route) }) }
            composable(Tab.Log.route) { LogScreen(onOpenEntry = { nav.navigate(entryRoute(it)) }) }
            composable(Tab.Insights.route) { InsightsScreen() }
            composable(Tab.Profile.route) { ProfileScreen() }
            composable("entry/{date}", arguments = listOf(navArgument("date") { type = NavType.StringType })) {
                EntryScreen(date = LocalDate.parse(it.arguments!!.getString("date")), onDone = { nav.popBackStack() })
            }
        }
    }
}
