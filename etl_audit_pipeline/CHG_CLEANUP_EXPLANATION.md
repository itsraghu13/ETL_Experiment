# CHG Table Cleanup - Batch-Specific Deletion

## 🎯 Important Update

The CHG_Table_Cleanup notebook has been updated to handle **batch-specific deletion** instead of deleting all data.

## ⚠️ Key Change

### **Before (Incorrect):**
```sql
-- This would delete ALL data from CHG table
DELETE FROM chg_table;
-- or
TRUNCATE TABLE chg_table;
```

### **After (Correct):** ✅
```sql
-- This deletes ONLY the specific batch that was just processed
DELETE FROM chg_table
WHERE batch_no = 123;  -- Only this batch
```

## 📊 Why This Matters

### **Scenario: Multiple Batches in CHG Table**

```
CHG Table Before Cleanup:
┌──────────┬─────────────────────┬──────────────┐
│ batch_no │ edf_job_run_item_id │ data         │
├──────────┼─────────────────────┼──────────────┤
│ 1        │ RUN_001             │ Data A       │
│ 1        │ RUN_002             │ Data B       │
│ 2        │ RUN_003             │ Data C       │ ← Still processing
│ 2        │ RUN_004             │ Data D       │ ← Still processing
│ 3        │ RUN_005             │ Data E       │ ← Not started
└──────────┴─────────────────────┴──────────────┘

After Processing Batch 1:
- Batch 1 is complete → Clean up batch 1 ONLY
- Batch 2 is still processing → Keep it
- Batch 3 hasn't started → Keep it

CHG Table After Cleanup (Batch 1):
┌──────────┬─────────────────────┬──────────────┐
│ batch_no │ edf_job_run_item_id │ data         │
├──────────┼─────────────────────┼──────────────┤
│ 2        │ RUN_003             │ Data C       │ ✅ Kept
│ 2        │ RUN_004             │ Data D       │ ✅ Kept
│ 3        │ RUN_005             │ Data E       │ ✅ Kept
└──────────┴─────────────────────┴──────────────┘
```

## 🔄 Complete Flow with Batch-Specific Cleanup

### **Example: 3 Batches Processing**

```
Time: 10:00 AM
┌─────────────────────────────────────────┐
│ Batch 1 Processing                      │
│ - Process 100 records                   │
│ - Write to CHG table (batch_no=1)       │
│ - Complete successfully                 │
└─────────────────────────────────────────┘
         ↓
Time: 10:05 AM
┌─────────────────────────────────────────┐
│ Batch 1 Cleanup                         │
│ DELETE FROM chg_table                   │
│ WHERE batch_no = 1                      │
│ → Removes 100 records (batch 1 only)    │
└─────────────────────────────────────────┘

Time: 10:10 AM
┌─────────────────────────────────────────┐
│ Batch 2 Processing                      │
│ - Process 150 records                   │
│ - Write to CHG table (batch_no=2)       │
│ - Complete successfully                 │
└─────────────────────────────────────────┘
         ↓
Time: 10:15 AM
┌─────────────────────────────────────────┐
│ Batch 2 Cleanup                         │
│ DELETE FROM chg_table                   │
│ WHERE batch_no = 2                      │
│ → Removes 150 records (batch 2 only)    │
│ → Batch 3 data still in table (safe)    │
└─────────────────────────────────────────┘
```

## 📝 Updated Notebook Parameters

### **CHG_Table_Cleanup.py Parameters:**

```python
# Required parameters
database_name = "dev_edf_silver.dps_stage"
chg_table = "customer_chg"
batch_no = "1"  # ⭐ NEW: Required parameter
cleanup_mode = "DELETE"  # DELETE or TRUNCATE
```

### **Example Usage:**

```python
# Clean up batch 1 only
dbutils.notebook.run(
    "/Workspace/ETL_Audit/CHG_Table_Cleanup",
    timeout_seconds=300,
    arguments={
        "database_name": "dev_edf_silver.dps_stage",
        "chg_table": "customer_chg",
        "batch_no": "1",  # Only clean this batch
        "cleanup_mode": "DELETE"
    }
)
```

## 🔍 SQL Queries Used

### **1. Count Records for Specific Batch**
```sql
SELECT COUNT(*) as record_count 
FROM dev_edf_silver.dps_stage.customer_chg
WHERE batch_no = 1;
```

### **2. Delete Specific Batch Only**
```sql
DELETE FROM dev_edf_silver.dps_stage.customer_chg
WHERE batch_no = 1;
```

### **3. Verify Cleanup**
```sql
-- Should return 0 for cleaned batch
SELECT COUNT(*) as record_count 
FROM dev_edf_silver.dps_stage.customer_chg
WHERE batch_no = 1;

-- Should return > 0 for other batches
SELECT COUNT(*) as record_count 
FROM dev_edf_silver.dps_stage.customer_chg
WHERE batch_no IN (2, 3);
```

## ⚠️ TRUNCATE Mode Warning

The notebook now includes a safety check for TRUNCATE mode:

```python
if cleanup_mode.upper() == "TRUNCATE":
    # Warning: TRUNCATE removes ALL data, not just this batch
    print(f"WARNING: TRUNCATE will remove ALL data from {chg_table}")
    print(f"Switching to DELETE mode for safety...")
    # Automatically switches to DELETE with WHERE clause
    DELETE FROM chg_table WHERE batch_no = {batch_no}
```

**Recommendation:** Always use `DELETE` mode when multiple batches exist.

## 📊 Monitoring Queries

### **Check All Batches in CHG Table**
```sql
SELECT 
    batch_no,
    COUNT(*) as record_count,
    MIN(create_ts) as oldest_record,
    MAX(create_ts) as newest_record
FROM dev_edf_silver.dps_stage.customer_chg
GROUP BY batch_no
ORDER BY batch_no;
```

### **Check Processed vs Unprocessed Batches**
```sql
SELECT 
    f.batch_no,
    f.processed_flag,
    COUNT(*) as audit_records,
    COUNT(DISTINCT c.edf_job_run_item_id) as chg_records
FROM dev_edf_silver.dps_stage.ETL_AUDT_FACT f
LEFT JOIN dev_edf_silver.dps_stage.customer_chg c
    ON f.edf_job_run_item_id = c.edf_job_run_item_id
    AND f.batch_no = c.batch_no
GROUP BY f.batch_no, f.processed_flag
ORDER BY f.batch_no;
```

## ✅ Benefits of Batch-Specific Cleanup

1. **Safety**: Other batches remain untouched
2. **Parallel Processing**: Multiple batches can run simultaneously
3. **Error Recovery**: Failed batches don't affect successful ones
4. **Audit Trail**: Clear tracking of which batch was cleaned
5. **Flexibility**: Can reprocess specific batches without affecting others

## 🎯 Best Practices

1. **Always pass batch_no**: Required parameter for safety
2. **Use DELETE mode**: Safer than TRUNCATE for multiple batches
3. **Verify before cleanup**: Check batch status in ETL_AUDT_FACT
4. **Monitor CHG table**: Regularly check for orphaned batches
5. **Clean up completed batches**: Only delete after processed_flag='Y'

## 📋 Complete Cleanup Flow

```
1. Process Batch 1
   ↓
2. Update ETL_AUDT_FACT (processed_flag='Y' for batch 1)
   ↓
3. Run CHG_Table_Cleanup with batch_no=1
   ↓
4. Verify: batch 1 removed, other batches intact
   ↓
5. Ready for next batch
```

## 🔧 Troubleshooting

### **Issue: Batch not deleted**
```sql
-- Check if batch exists
SELECT * FROM chg_table WHERE batch_no = 1;

-- Check processed status
SELECT * FROM ETL_AUDT_FACT WHERE batch_no = 1;
```

### **Issue: Wrong batch deleted**
```sql
-- Check what was deleted (use Delta Lake time travel)
SELECT * FROM chg_table VERSION AS OF 1;

-- Restore if needed
RESTORE TABLE chg_table TO VERSION AS OF 1;
```

### **Issue: Multiple batches deleted accidentally**
```sql
-- Check Delta Lake history
DESCRIBE HISTORY chg_table;

-- Restore to before deletion
RESTORE TABLE chg_table TO TIMESTAMP AS OF '2026-05-07 10:00:00';
```

## 📚 Summary

**Key Takeaway:** The CHG_Table_Cleanup notebook now safely handles multiple batches by deleting only the specific batch_no that was just processed, ensuring other batches remain intact for continued processing.

**Always remember:** Pass the `batch_no` parameter to ensure safe, targeted cleanup! ✅