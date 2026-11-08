package com.mindtrack.app.data

import java.time.LocalDate

/** Single source of truth: dashboard, charts and export all read through here. */
class RecordRepository(private val dao: DailyRecordDao) {
    fun observeAll() = dao.observeAll()
    fun observe(date: LocalDate) = dao.observe(date.toString())
    fun observeRange(from: LocalDate, to: LocalDate) = dao.observeRange(from.toString(), to.toString())
    suspend fun get(date: LocalDate) = dao.get(date.toString())
    suspend fun save(record: DailyRecord) = dao.upsert(record.copy(updatedAt = System.currentTimeMillis()))
    suspend fun delete(date: LocalDate) = dao.delete(date.toString())
    suspend fun clearAll() = dao.deleteAll()
}
