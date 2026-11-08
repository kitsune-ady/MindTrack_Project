package com.mindtrack.app.reminders

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.mindtrack.app.MainActivity
import com.mindtrack.app.MindTrackApp
import com.mindtrack.app.R
import com.mindtrack.app.domain.nextReminderDelayMillis
import java.time.LocalDate
import java.time.LocalDateTime
import java.util.concurrent.TimeUnit

object Reminders {
    private const val WORK_NAME = "daily_reminder"
    private const val CHANNEL_ID = "daily_checkin"

    /** Re-computed on every schedule (and on app launch) so it re-aligns after timezone/DST changes. */
    fun schedule(context: Context, hour: Int, minute: Int) {
        val delay = nextReminderDelayMillis(LocalDateTime.now(), hour, minute)
        val request = PeriodicWorkRequestBuilder<ReminderWorker>(24, TimeUnit.HOURS)
            .setInitialDelay(delay, TimeUnit.MILLISECONDS).build()
        WorkManager.getInstance(context)
            .enqueueUniquePeriodicWork(WORK_NAME, ExistingPeriodicWorkPolicy.CANCEL_AND_REENQUEUE, request)
    }

    fun cancel(context: Context) = WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)

    fun sendTest(context: Context) {
        WorkManager.getInstance(context).enqueue(
            OneTimeWorkRequestBuilder<ReminderWorker>().setInputData(Data.Builder().putBoolean("test", true).build()).build()
        )
    }

    fun canNotify(context: Context): Boolean =
        NotificationManagerCompat.from(context).areNotificationsEnabled() &&
            (Build.VERSION.SDK_INT < 33 ||
                ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED)

    internal fun show(context: Context) {
        if (!canNotify(context)) return
        val nm = context.getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Daily check-in", NotificationManager.IMPORTANCE_DEFAULT)
                    .apply { description = "A gentle optional reminder to log your day" })
        }
        val open = PendingIntent.getActivity(
            context, 0, Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        // Deliberately neutral: nothing about mood, habits or the user's data on the lock screen.
        val n = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("MindTrack")
            .setContentText("A quick check-in whenever you're ready.")
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setContentIntent(open).setAutoCancel(true).build()
        nm.notify(1001, n)
    }
}

class ReminderWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val test = inputData.getBoolean("test", false)
        val repo = (applicationContext as MindTrackApp).repository
        // Don't nudge someone who has already logged today.
        if (!test && repo.get(LocalDate.now()) != null) return Result.success()
        Reminders.show(applicationContext)
        return Result.success()
    }
}
