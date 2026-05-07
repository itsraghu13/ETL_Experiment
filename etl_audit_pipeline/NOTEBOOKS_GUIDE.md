# Notebooks Guide - Which Ones to Use?

## 📓 Notebook Overview

### **Main Notebooks (Use These for Databricks)**

These are the **4 main notebooks** you need for your Azure Databricks implementation:

1. ✅ **`Databricks_Notebook1_Lookup_Validation.py`** ⭐ **USE THIS**
   - **Purpose**: Initial validation and audit record creation
   - **Optimized for**: Azure Databricks with Unity Catalog
   - **Catalog/Schema**: `dev_edf_silver.dps_stage`
   - **Key Features**:
     - No SparkSession import (Databricks provides it)
     - Unity Catalog path support
     - Widget parameters for job configuration

2. ✅ **`Notebook2_Processing_Loop.py`**
   - **Purpose**: Batch processing orchestration
   - **Function**: Loop through unprocessed batches and execute processing
   - **Key Features**:
     - Batch-level processing
     - Parallel execution support
     - Error handling and retry logic

3. ✅ **`Final_Notebook_Cleanup.py`**
   - **Purpose**: Finalization and status updates
   - **Function**: Update processed_flag, set timestamps, validate data
   - **Key Features**:
     - Update audit records to 'Y'
     - Set job_end_time and run_status
     - Validate target table data

4. ✅ **`CHG_Table_Cleanup.py`**
   - **Purpose**: Clean CHG (Change) tables after processing
   - **Function**: DELETE or TRUNCATE CHG tables
   - **Key Features**:
     - Only runs for CHG table types
     - Prepares table for next run
     - Verification and optimization

---

## 🔄 Duplicate Notebook Explanation

### **Notebook1 - Two Versions**

#### Version 1: `Notebook1_Lookup_Validation.py` (Generic)
- **Status**: ⚠️ Generic version (for reference)
- **Use Case**: Template for non-Databricks environments
- **Features**: Generic database_name parameter
- **Recommendation**: **Don't use for Databricks**

#### Version 2: `Databricks_Notebook1_Lookup_Validation.py` ⭐
- **Status**: ✅ **USE THIS FOR DATABRICKS**
- **Use Case**: Azure Databricks with Unity Catalog
- **Features**: 
  - Catalog and schema parameters
  - No SparkSession import
  - Full Unity Catalog path support
- **Recommendation**: **Use this one!**

---

## 📋 Which Notebooks to Upload to Databricks?

### **Upload These 4 Notebooks:**

```
✅ Databricks_Notebook1_Lookup_Validation.py  (Main validation)
✅ Notebook2_Processing_Loop.py               (Batch processing)
✅ Final_Notebook_Cleanup.py                  (Finalization)
✅ CHG_Table_Cleanup.py                       (CHG cleanup)
```

### **Don't Upload:**

```
❌ Notebook1_Lookup_Validation.py  (Generic version - keep for reference only)
```

---

## 🎯 Execution Order

### **Standard Flow:**

```
1. Databricks_Notebook1_Lookup_Validation.py
   ↓
2. Notebook2_Processing_Loop.py
   ↓
3. Final_Notebook_Cleanup.py
   ↓
4. CHG_Table_Cleanup.py (only if CHG table)
```

### **Example Execution:**

```python
# Step 1: Validation
result1 = dbutils.notebook.run(
    "/Workspace/ETL_Audit/Databricks_Notebook1_Lookup_Validation",
    timeout_seconds=600,
    arguments={
        "job_name": "MY_JOB",
        "src_table1": "dev_edf_bronze.staging.my_source",
        "catalog_name": "dev_edf_silver",
        "schema_name": "dps_stage"
    }
)

# Step 2: Processing
result2 = dbutils.notebook.run(
    "/Workspace/ETL_Audit/Notebook2_Processing_Loop",
    timeout_seconds=3600,
    arguments={
        "database_name": "dev_edf_silver.dps_stage",
        "max_parallel_batches": "5"
    }
)

# Step 3: Finalization
result3 = dbutils.notebook.run(
    "/Workspace/ETL_Audit/Final_Notebook_Cleanup",
    timeout_seconds=600,
    arguments={
        "database_name": "dev_edf_silver.dps_stage",
        "target_table": "my_target_table"
    }
)

# Step 4: CHG Cleanup (if needed)
if chg_table:
    result4 = dbutils.notebook.run(
        "/Workspace/ETL_Audit/CHG_Table_Cleanup",
        timeout_seconds=300,
        arguments={
            "database_name": "dev_edf_silver.dps_stage",
            "chg_table": "my_chg_table",
            "cleanup_mode": "DELETE"
        }
    )
```

---

## 📊 Notebook Comparison

| Feature | Notebook1_Lookup_Validation.py | Databricks_Notebook1_Lookup_Validation.py |
|---------|-------------------------------|------------------------------------------|
| **Environment** | Generic SQL | Azure Databricks Unity Catalog |
| **SparkSession Import** | ❌ Yes (not needed) | ✅ No (correct) |
| **Catalog Support** | ❌ No | ✅ Yes |
| **Parameters** | database_name | catalog_name, schema_name |
| **Path Format** | `database.table` | `catalog.schema.table` |
| **Recommendation** | Reference only | **Use this!** ⭐ |

---

## 🗂️ Databricks Workspace Structure

### **Recommended Folder Structure:**

```
/Workspace/
└── Users/
    └── [your_email]/
        └── ETL_Audit_Pipeline/
            ├── Databricks_Notebook1_Lookup_Validation  ⭐
            ├── Notebook2_Processing_Loop
            ├── Final_Notebook_Cleanup
            └── CHG_Table_Cleanup
```

---

## 🔍 Quick Reference

### **For Azure Databricks with Unity Catalog:**

| Notebook | Purpose | Required? | Upload? |
|----------|---------|-----------|---------|
| `Databricks_Notebook1_Lookup_Validation.py` | Validation | ✅ Yes | ✅ Yes |
| `Notebook2_Processing_Loop.py` | Processing | ✅ Yes | ✅ Yes |
| `Final_Notebook_Cleanup.py` | Finalization | ✅ Yes | ✅ Yes |
| `CHG_Table_Cleanup.py` | CHG Cleanup | ⚠️ If CHG tables | ✅ Yes |
| `Notebook1_Lookup_Validation.py` | Generic | ❌ No | ❌ No |

---

## ✅ Summary

**You need exactly 4 notebooks for Databricks:**

1. **Databricks_Notebook1_Lookup_Validation.py** (not the generic Notebook1)
2. **Notebook2_Processing_Loop.py**
3. **Final_Notebook_Cleanup.py**
4. **CHG_Table_Cleanup.py**

**The generic `Notebook1_Lookup_Validation.py` is a duplicate/reference version - don't use it for Databricks!**

---

## 🎯 Action Items

1. ✅ Upload the 4 main notebooks to Databricks
2. ❌ Ignore/delete the generic `Notebook1_Lookup_Validation.py`
3. ✅ Use `Databricks_Notebook1_Lookup_Validation.py` instead
4. ✅ Configure parameters for your environment
5. ✅ Test the flow end-to-end

**That's it! You have everything you need.** 🚀