package com.mindtrack.app.data

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface DailyRecordDao {
    @Query("SELECT * FROM daily_records ORDER BY date DESC")
    fun observeAll(): Flow<List<DailyRecord>>

    @Query("SELECT * FROM daily_records WHERE date BETWEEN :from AND :to ORDER BY date")
    fun observeRange(from: String, to: String): Flow<List<DailyRecord>>

    @Query("SELECT * FROM daily_records WHERE date = :date")
    suspend fun get(date: String): DailyRecord?

    @Query("SELECT * FROM daily_records WHERE date = :date")
    fun observe(date: String): Flow<DailyRecord?>

    @Upsert suspend fun upsert(record: DailyRecord)

    @Query("DELETE FROM daily_records WHERE date = :date")
    suspend fun delete(date: String)

    @Query("DELETE FROM daily_records")
    suspend fun deleteAll()
}

@Database(entities = [DailyRecord::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun dao(): DailyRecordDao

    companion object {
        fun create(context: Context) =
            Room.databaseBuilder(context, AppDatabase::class.java, "mindtrack.db").build()
    }
}
