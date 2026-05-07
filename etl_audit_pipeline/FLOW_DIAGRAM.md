# ETL Audit Pipeline - Complete Flow Diagram

## 📊 End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE ETL AUDIT FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

START: Job Execution Triggered
│
├─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIALIZATION & VALIDATION (Notebook1)                            │
└─────────────────────────────────────────────────────────────────────────────┘
│
│ Step 1.1: Lookup ETL_AUDT_REF
│ ┌──────────────────────────────────────┐
│ │ SELECT * FROM ETL_AUDT_REF           │
│ │ WHERE job_name = 'YOUR_JOB'          │
│ │   AND src_table1 = 'source_table'    │
│ │   AND active_flag = 'Y'              │
│ └──────────────────────────────────────┘
│           │
│           ├─── NOT FOUND ──→ EXIT: "Job config not found" ❌
│           │
│           └─── FOUND ──→ Continue
│
│ Step 1.2: Check ETL_AUDT_FACT for Unprocessed Items
│ ┌──────────────────────────────────────┐
│ │ SELECT DISTINCT edf_job_run_item_id  │
│ │ FROM ETL_AUDT_FACT                   │
│ │ WHERE processed_flag = 'N'           │
│ └──────────────────────────────────────┘
│           │
│           ├─── Has Unprocessed Items ──→ Use these IDs
│           │
│           └─── No Unprocessed Items ──→ Get all from source
│
│ Step 1.3: Get job_run_item_ids from Source Table
│ ┌──────────────────────────────────────┐
│ │ IF unprocessed items exist:          │
│ │   SELECT DISTINCT job_run_item_id    │
│ │   FROM source_table                  │
│ │   WHERE job_run_item_id IN (...)     │
│ │ ELSE:                                │
│ │   SELECT DISTINCT job_run_item_id    │
│ │   FROM source_table                  │
│ └──────────────────────────────────────┘
│           │
│           └─── Found: 3 items (example)
│
│ Step 1.4: Insert into ETL_AUDT_FACT
│ ┌──────────────────────────────────────┐
│ │ INSERT INTO ETL_AUDT_FACT            │
│ │ (edf_job_run_item_id,                │
│ │  processed_flag,                     │
│ │  create_ts, update_ts)               │
│ │ VALUES                               │
│ │ ('ITEM_001', 'N', NULL, NOW()),      │
│ │ ('ITEM_002', 'N', NULL, NOW()),      │
│ │ ('ITEM_003', 'N', NULL, NOW())       │
│ └──────────────────────────────────────┘
│           │
│           └─── SUCCESS: 3 records inserted ✅
│
├─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: BATCH PROCESSING (Notebook2 / ADF Pipeline)                        │
└─────────────────────────────────────────────────────────────────────────────┘
│
│ Step 2.1: Get Unprocessed Batches
│ ┌──────────────────────────────────────┐
│ │ SELECT batch_no, COUNT(*) as count   │
│ │ FROM ETL_AUDT_FACT                   │
│ │ WHERE processed_flag = 'N'           │
│ │ GROUP BY batch_no                    │
│ └──────────────────────────────────────┘
│           │
│           └─── Found: Batch 1 (3 items), Batch 2 (5 items)
│
│ Step 2.2: Check Table Type (CHG or FINAL)
│ ┌──────────────────────────────────────┐
│ │ SELECT chg_final                     │
│ │ FROM ETL_AUDT_REF                    │
│ │ WHERE job_name = 'YOUR_JOB'          │
│ └──────────────────────────────────────┘
│           │
│           ├─── CHG ──→ Use OVERWRITE mode
│           │            (Replace all data)
│           │
│           └─── FINAL ──→ Use APPEND mode
│                          (Add to existing data)
│
│ Step 2.3: Process Each Batch
│ ┌──────────────────────────────────────┐
│ │ FOR EACH batch_no:                   │
│ │   1. Get items for this batch        │
│ │   2. Run processing logic            │
│ │   3. Write to target table           │
│ │   4. Update audit records            │
│ └──────────────────────────────────────┘
│           │
│           ├─── Batch 1 Processing
│           │    ┌────────────────────────┐
│           │    │ Process 3 items        │
│           │    │ Write to target        │
│           │    │ Mode: OVERWRITE/APPEND │
│           │    └────────────────────────┘
│           │              │
│           │              └─── SUCCESS ✅
│           │
│           └─── Batch 2 Processing
│                ┌────────────────────────┐
│                │ Process 5 items        │
│                │ Write to target        │
│                │ Mode: OVERWRITE/APPEND │
│                └────────────────────────┘
│                          │
│                          └─── SUCCESS ✅
│
├─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: FINALIZATION (Final Notebook)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
│
│ Step 3.1: Update ETL_AUDT_FACT
│ ┌──────────────────────────────────────┐
│ │ UPDATE ETL_AUDT_FACT                 │
│ │ SET processed_flag = 'Y',            │
│ │     job_end_time = NOW(),            │
│ │     run_status = 'SUCCESS',          │
│ │     update_ts = NOW()                │
│ │ WHERE processed_flag = 'N'           │
│ └──────────────────────────────────────┘
│           │
│           └─── Updated: 8 records ✅
│
│ Step 3.2: Validate Target Table
│ ┌──────────────────────────────────────┐
│ │ SELECT COUNT(*)                      │
│ │ FROM target_table                    │
│ │ WHERE job_run_item_id IN (...)       │
│ └──────────────────────────────────────┘
│           │
│           └─── Verified: 8 records in target ✅
│
│ Step 3.3: CHG Table Cleanup (if CHG type)
│ ┌──────────────────────────────────────┐
│ │ IF chg_final = 'CHG':                │
│ │   DELETE FROM chg_table              │
│ │   (or TRUNCATE TABLE chg_table)      │
│ │   Prepare for next run               │
│ └──────────────────────────────────────┘
│           │
│           └─── CHG table cleaned ✅
│
END: Job Completed Successfully ✅
```

## 🔄 Detailed Step-by-Step Flow

### **PHASE 1: Initialization (Notebook1)**

#### Input Parameters:
- `job_name`: "MY_SALES_JOB"
- `src_table1`: "dev_edf_bronze.staging.sales_data"
- `catalog_name`: "dev_edf_silver"
- `schema_name`: "dps_stage"

#### Process:

**Step 1: Lookup Configuration**
```sql
-- Check if job exists in ETL_AUDT_REF
SELECT * FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE job_name = 'MY_SALES_JOB'
  AND src_table1 = 'dev_edf_bronze.staging.sales_data'
  AND active_flag = 'Y';

-- Result: Found 1 record
-- target_table: dev_edf_silver.dps_stage.sales_fact
-- chg_final: FINAL
```

**Step 2: Check for Unprocessed Items**
```sql
-- Look for existing unprocessed items
SELECT DISTINCT edf_job_run_item_id
FROM dev_edf_silver.dps_stage.ETL_AUDT_FACT
WHERE processed_flag = 'N';

-- Result: No unprocessed items found
```

**Step 3: Get Items from Source**
```sql
-- Since no unprocessed items, get all from source
SELECT DISTINCT edf_job_run_item_id
FROM dev_edf_bronze.staging.sales_data;

-- Result: Found 3 items
-- RUN_20260507_001
-- RUN_20260507_002
-- RUN_20260507_003
```

**Step 4: Create Audit Records**
```sql
-- Insert into audit table
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_FACT
(edf_job_run_item_id, processed_flag, create_ts, update_ts)
VALUES
('RUN_20260507_001', 'N', NULL, CURRENT_TIMESTAMP()),
('RUN_20260507_002', 'N', NULL, CURRENT_TIMESTAMP()),
('RUN_20260507_003', 'N', NULL, CURRENT_TIMESTAMP());

-- Result: 3 records inserted ✅
```

#### Output:
```
SUCCESS: Processed 3 job_run_item_ids
```

---

### **PHASE 2: Batch Processing (Notebook2)**

#### Input:
- Unprocessed records from ETL_AUDT_FACT

#### Process:

**Step 1: Get Batches**
```sql
SELECT batch_no, COUNT(*) as item_count
FROM dev_edf_silver.dps_stage.ETL_AUDT_FACT
WHERE processed_flag = 'N'
GROUP BY batch_no;

-- Result:
-- batch_no | item_count
-- 1        | 3
```

**Step 2: Determine Write Mode**
```sql
SELECT chg_final
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE job_name = 'MY_SALES_JOB';

-- Result: FINAL → Use APPEND mode
```

**Step 3: Process Batch 1**
```python
# Get data for batch 1
batch_data = spark.sql("""
    SELECT s.*
    FROM dev_edf_bronze.staging.sales_data s
    JOIN dev_edf_silver.dps_stage.ETL_AUDT_FACT a
      ON s.edf_job_run_item_id = a.edf_job_run_item_id
    WHERE a.batch_no = 1
      AND a.processed_flag = 'N'
""")

# Apply transformations
processed_data = batch_data.transform(...)

# Write to target (APPEND mode for FINAL tables)
processed_data.write \
    .mode("append") \
    .saveAsTable("dev_edf_silver.dps_stage.sales_fact")

# Result: 3 records written ✅
```

#### Output:
```
SUCCESS: Processed 1 batches: 1 successful, 0 failed
```

---

### **PHASE 3: Finalization (Final Notebook)**

#### Process:

**Step 1: Update Audit Records**
```sql
UPDATE dev_edf_silver.dps_stage.ETL_AUDT_FACT
SET 
    processed_flag = 'Y',
    job_end_time = CURRENT_TIMESTAMP(),
    run_status = 'SUCCESS',
    update_ts = CURRENT_TIMESTAMP()
WHERE processed_flag = 'N';

-- Result: 3 records updated ✅
```

**Step 2: Validate Target Data**
```sql
SELECT COUNT(*) as target_count
FROM dev_edf_silver.dps_stage.sales_fact
WHERE edf_job_run_item_id IN (
    'RUN_20260507_001',
    'RUN_20260507_002',
    'RUN_20260507_003'
);

-- Result: 3 records found in target ✅
```

**Step 3: CHG Table Cleanup (if applicable)**
```sql
-- Only runs if chg_final = 'CHG'
-- For FINAL tables, this step is skipped

-- If CHG table:
DELETE FROM dev_edf_silver.dps_stage.customer_chg;
-- or
TRUNCATE TABLE dev_edf_silver.dps_stage.customer_chg;
```

#### Output:
```
SUCCESS: Updated 3 records to Processed_Flag='Y'
```

---

## 📋 State Transitions

```
┌─────────────┐
│   INITIAL   │ Job not in ETL_AUDT_REF
└──────┬──────┘
       │
       ↓ (Add to ETL_AUDT_REF)
┌─────────────┐
│ CONFIGURED  │ Job exists in ETL_AUDT_REF
└──────┬──────┘
       │
       ↓ (Run Notebook1)
┌─────────────┐
│  PENDING    │ processed_flag = 'N'
│   (N)       │ Records in ETL_AUDT_FACT
└──────┬──────┘
       │
       ↓ (Run Notebook2)
┌─────────────┐
│ PROCESSING  │ Batch processing in progress
└──────┬──────┘
       │
       ↓ (Complete processing)
┌─────────────┐
│ PROCESSED   │ Data written to target
└──────┬──────┘
       │
       ↓ (Run Final Notebook)
┌─────────────┐
│ COMPLETED   │ processed_flag = 'Y'
│   (Y)       │ run_status = 'SUCCESS'
└──────┬──────┘
       │
       ↓ (If CHG table)
┌─────────────┐
│  CLEANED    │ CHG table emptied
│             │ Ready for next run
└─────────────┘
```

## 🔀 CHG vs FINAL Flow Comparison

### CHG Table Flow (Overwrite Mode)
```
Source Data → Notebook1 (Validate) → ETL_AUDT_FACT (N)
                                            ↓
                                     Notebook2 (Process)
                                            ↓
                                     CHG Table (OVERWRITE)
                                     ├─ Run 1: Replace all data
                                     ├─ Run 2: Replace all data
                                     └─ Run 3: Replace all data
                                            ↓
                                     Final Notebook
                                     ├─ Update flags (Y)
                                     └─ DELETE/TRUNCATE CHG table
                                            ↓
                                     Ready for next run (empty)
```

### FINAL Table Flow (Append Mode)
```
Source Data → Notebook1 (Validate) → ETL_AUDT_FACT (N)
                                            ↓
                                     Notebook2 (Process)
                                            ↓
                                     FINAL Table (APPEND)
                                     ├─ Run 1: Add 100 records
                                     ├─ Run 2: Add 150 records
                                     └─ Run 3: Add 200 records
                                            ↓
                                     Final Notebook
                                     └─ Update flags (Y)
                                            ↓
                                     Data persists (450 total records)
```

## 📊 Data Flow Example

### Example: Daily Sales ETL

**Day 1:**
```
Source: 100 sales records
↓
Notebook1: Create 100 audit records (N)
↓
Notebook2: Process 100 records → Write to sales_fact (APPEND)
↓
Final: Update 100 audit records (Y)
↓
Result: sales_fact has 100 records
```

**Day 2:**
```
Source: 150 new sales records
↓
Notebook1: Create 150 audit records (N)
↓
Notebook2: Process 150 records → Write to sales_fact (APPEND)
↓
Final: Update 150 audit records (Y)
↓
Result: sales_fact has 250 records (100 + 150)
```

**Day 3:**
```
Source: 200 new sales records
↓
Notebook1: Create 200 audit records (N)
↓
Notebook2: Process 200 records → Write to sales_fact (APPEND)
↓
Final: Update 200 audit records (Y)
↓
Result: sales_fact has 450 records (100 + 150 + 200)
```

---

**This is the complete flow of your ETL Audit Pipeline system!** 🎯