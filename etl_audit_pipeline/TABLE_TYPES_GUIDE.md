# Table Types Guide - CHG, FINAL, and CURRENT

## 📊 Three Table Types

The system supports three table types in the `chg_final` column:

1. **CHG** (Change) - Temporary staging tables
2. **FINAL** - Permanent historical tables
3. **CURRENT** - Current state tables (latest snapshot)

## 🎯 Table Type Comparison

| Type | Write Mode | Cleanup | Use Case | Data Retention |
|------|------------|---------|----------|----------------|
| **CHG** | OVERWRITE | Delete after processing | Staging/CDC | Temporary |
| **FINAL** | APPEND | No cleanup | Historical data warehouse | Permanent |
| **CURRENT** | OVERWRITE | No cleanup | Latest snapshot | Current state only |

## 📋 Detailed Explanation

### **1. CHG (Change Tables)**

**Purpose:** Temporary staging for incremental changes

**Behavior:**
- Write Mode: `OVERWRITE` (replace all data each run)
- Cleanup: `DELETE WHERE batch_no = X` after processing
- Data: Only current batch data

**Example:**
```sql
-- CHG table configuration
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES (
    'JOB_CUSTOMER_CDC',
    'dev_edf_bronze.staging.customer_changes',
    'dev_edf_silver.dps_stage.customer_chg',
    'CHG',  -- Change table
    'Customer_CDC_Job',
    '/Workspace/ETL_Jobs/Customer_CDC',
    'Customer CDC - temporary staging'
);

-- Processing flow:
-- Run 1: Write 100 records (overwrite) → Process → Delete batch 1
-- Run 2: Write 150 records (overwrite) → Process → Delete batch 2
-- Result: Table is empty after each run
```

---

### **2. FINAL (Historical Tables)**

**Purpose:** Permanent storage of all historical data

**Behavior:**
- Write Mode: `APPEND` (add to existing data)
- Cleanup: `NO CLEANUP` (data persists)
- Data: Accumulates all historical records

**Example:**
```sql
-- FINAL table configuration
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES (
    'JOB_SALES_HISTORY',
    'dev_edf_bronze.staging.sales_data',
    'dev_edf_silver.dps_stage.sales_fact',
    'FINAL',  -- Historical table
    'Sales_ETL_Job',
    '/Workspace/ETL_Jobs/Sales_Processing',
    'Sales historical data - append mode'
);

-- Processing flow:
-- Run 1: Write 100 records (append) → Total: 100
-- Run 2: Write 150 records (append) → Total: 250
-- Run 3: Write 200 records (append) → Total: 450
-- Result: All data persists, grows over time
```

---

### **3. CURRENT (Current State Tables)** ⭐ **NEW**

**Purpose:** Maintain only the latest/current state of data

**Behavior:**
- Write Mode: `OVERWRITE` (replace all data each run)
- Cleanup: `NO CLEANUP` (but data is replaced)
- Data: Only the most recent snapshot

**Example:**
```sql
-- CURRENT table configuration
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES (
    'JOB_CUSTOMER_CURRENT',
    'dev_edf_bronze.staging.customer_master',
    'dev_edf_silver.dps_stage.customer_current',
    'CURRENT',  -- Current state table
    'Customer_Current_Job',
    '/Workspace/ETL_Jobs/Customer_Current',
    'Customer current state - latest snapshot only'
);

-- Processing flow:
-- Run 1: Write 1000 customers (overwrite) → Total: 1000
-- Run 2: Write 1050 customers (overwrite) → Total: 1050 (replaced)
-- Run 3: Write 1100 customers (overwrite) → Total: 1100 (replaced)
-- Result: Always contains only the latest snapshot
```

---

## 🔄 Processing Logic by Table Type

### **CHG Tables**
```
1. Validate job
2. Create audit records (N)
3. Process batch
4. Write to CHG table (OVERWRITE mode)
5. Update audit records (Y)
6. DELETE FROM chg_table WHERE batch_no = X  ← Cleanup
7. Ready for next batch
```

### **FINAL Tables**
```
1. Validate job
2. Create audit records (N)
3. Process batch
4. Write to FINAL table (APPEND mode)
5. Update audit records (Y)
6. No cleanup - data persists
7. Ready for next batch
```

### **CURRENT Tables** ⭐
```
1. Validate job
2. Create audit records (N)
3. Process all data (not batch-specific)
4. Write to CURRENT table (OVERWRITE mode)
5. Update audit records (Y)
6. No cleanup - data is already replaced
7. Ready for next run
```

---

## 📊 Updated Logic

### **Write Mode Determination**

```python
def get_write_mode(chg_final):
    """
    Determine write mode based on table type
    """
    if chg_final == 'CHG':
        return 'overwrite'  # Temporary staging
    elif chg_final == 'FINAL':
        return 'append'     # Historical accumulation
    elif chg_final == 'CURRENT':
        return 'overwrite'  # Latest snapshot
    else:
        raise ValueError(f"Unknown table type: {chg_final}")
```

### **Cleanup Determination**

```python
def needs_cleanup(chg_final):
    """
    Determine if cleanup is needed after processing
    """
    if chg_final == 'CHG':
        return True   # Delete processed batch
    elif chg_final == 'FINAL':
        return False  # Keep all data
    elif chg_final == 'CURRENT':
        return False  # Data already replaced
    else:
        return False
```

---

## 🎯 Use Case Examples

### **Example 1: Customer Data**

```sql
-- CHG: Temporary changes for CDC
INSERT INTO ETL_AUDT_REF VALUES (
    'CUSTOMER_CDC', 'staging.customer_changes', 
    'dps_stage.customer_chg', 'CHG', ...
);

-- CURRENT: Latest customer master
INSERT INTO ETL_AUDT_REF VALUES (
    'CUSTOMER_CURRENT', 'staging.customer_master', 
    'dps_stage.customer_current', 'CURRENT', ...
);

-- FINAL: Historical customer changes
INSERT INTO ETL_AUDT_REF VALUES (
    'CUSTOMER_HISTORY', 'staging.customer_history', 
    'dps_stage.customer_fact', 'FINAL', ...
);
```

### **Example 2: Sales Data**

```sql
-- CHG: Daily sales staging
INSERT INTO ETL_AUDT_REF VALUES (
    'SALES_STAGING', 'staging.daily_sales', 
    'dps_stage.sales_chg', 'CHG', ...
);

-- CURRENT: Current month sales summary
INSERT INTO ETL_AUDT_REF VALUES (
    'SALES_CURRENT_MONTH', 'staging.sales_summary', 
    'dps_stage.sales_current_month', 'CURRENT', ...
);

-- FINAL: All historical sales
INSERT INTO ETL_AUDT_REF VALUES (
    'SALES_HISTORY', 'staging.sales_data', 
    'dps_stage.sales_fact', 'FINAL', ...
);
```

### **Example 3: Inventory Data**

```sql
-- CURRENT: Current inventory levels (snapshot)
INSERT INTO ETL_AUDT_REF VALUES (
    'INVENTORY_CURRENT', 'staging.inventory_snapshot', 
    'dps_stage.inventory_current', 'CURRENT', ...
);

-- FINAL: Historical inventory movements
INSERT INTO ETL_AUDT_REF VALUES (
    'INVENTORY_HISTORY', 'staging.inventory_movements', 
    'dps_stage.inventory_fact', 'FINAL', ...
);
```

---

## 🔧 Updated ADF Pipeline Logic

### **Conditional Branching**

```json
{
    "name": "Determine_Write_Mode",
    "type": "Switch",
    "typeProperties": {
        "on": "@item().chg_final",
        "cases": [
            {
                "value": "CHG",
                "activities": [
                    {
                        "name": "Process_CHG_Table",
                        "type": "DatabricksNotebook",
                        "typeProperties": {
                            "baseParameters": {
                                "write_mode": "overwrite",
                                "cleanup_required": "true"
                            }
                        }
                    }
                ]
            },
            {
                "value": "FINAL",
                "activities": [
                    {
                        "name": "Process_FINAL_Table",
                        "type": "DatabricksNotebook",
                        "typeProperties": {
                            "baseParameters": {
                                "write_mode": "append",
                                "cleanup_required": "false"
                            }
                        }
                    }
                ]
            },
            {
                "value": "CURRENT",
                "activities": [
                    {
                        "name": "Process_CURRENT_Table",
                        "type": "DatabricksNotebook",
                        "typeProperties": {
                            "baseParameters": {
                                "write_mode": "overwrite",
                                "cleanup_required": "false"
                            }
                        }
                    }
                ]
            }
        ]
    }
}
```

---

## 📊 Comparison Matrix

| Feature | CHG | FINAL | CURRENT |
|---------|-----|-------|---------|
| **Write Mode** | OVERWRITE | APPEND | OVERWRITE |
| **Cleanup After Processing** | ✅ Yes (batch-specific) | ❌ No | ❌ No |
| **Data Retention** | Temporary | Permanent | Latest only |
| **Batch Processing** | ✅ Yes | ✅ Yes | ❌ No (full refresh) |
| **Historical Data** | ❌ No | ✅ Yes | ❌ No |
| **Use Case** | Staging/CDC | Data Warehouse | Current State |
| **Table Growth** | No growth | Grows over time | Fixed size |
| **Query Pattern** | Process & delete | Historical analysis | Current lookup |

---

## ✅ Updated Logic Works For All Three Types

### **Yes, the current logic works!** Here's why:

1. **CHG Tables:**
   - Write Mode: OVERWRITE ✅
   - Cleanup: DELETE WHERE batch_no = X ✅
   - Works perfectly

2. **FINAL Tables:**
   - Write Mode: APPEND ✅
   - Cleanup: None ✅
   - Works perfectly

3. **CURRENT Tables:** ⭐
   - Write Mode: OVERWRITE ✅ (same as CHG)
   - Cleanup: None ✅ (skip CHG_Table_Cleanup)
   - **Works with current logic!**

### **Key Difference:**

```python
# In Final Notebook or ADF:
if chg_final == 'CHG':
    # Run CHG_Table_Cleanup with batch_no
    run_cleanup(batch_no)
elif chg_final == 'FINAL':
    # No cleanup needed
    pass
elif chg_final == 'CURRENT':
    # No cleanup needed (data already replaced)
    pass
```

---

## 🎯 Summary

**Three Table Types Supported:**

1. **CHG** → OVERWRITE + Cleanup (batch-specific delete)
2. **FINAL** → APPEND + No Cleanup (accumulate all)
3. **CURRENT** → OVERWRITE + No Cleanup (latest snapshot)

**Current Logic:** ✅ **Works for all three types!**

Just need to update the conditional logic to handle CURRENT the same as FINAL (no cleanup), but with OVERWRITE mode instead of APPEND.

**The system is flexible and supports all three patterns!** 🎉