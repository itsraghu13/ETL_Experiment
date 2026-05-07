# ADF Looping with Databricks Job Names

## 📋 Overview

The `ETL_AUDT_REF` table now includes `databricks_job_name` and `notebook_path` columns to enable dynamic ADF pipeline looping and Databricks job triggering.

## 🗂️ Updated Table Structure

### **ETL_AUDT_REF Table Schema**

```sql
CREATE TABLE dev_edf_silver.dps_stage.ETL_AUDT_REF (
    job_name STRING,                    -- ETL job identifier
    src_table1 STRING,                  -- Source table
    target_table STRING,                -- Target table
    chg_final STRING,                   -- CHG or FINAL
    databricks_job_name STRING,         -- ⭐ Databricks job to trigger
    notebook_path STRING,               -- ⭐ Notebook path for processing
    desc_text STRING,                   -- Description
    create_ts TIMESTAMP,
    update_ts TIMESTAMP,
    active_flag STRING
);
```

## 📊 Sample Data

```sql
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES
(
    'JOB_SALES_ETL',
    'dev_edf_bronze.staging.sales_data',
    'dev_edf_silver.dps_stage.sales_fact',
    'FINAL',
    'Sales_ETL_Processing_Job',              -- Databricks job name
    '/Workspace/ETL_Jobs/Sales_Processing',  -- Notebook path
    'Daily sales ETL - append mode'
),
(
    'JOB_CUSTOMER_CDC',
    'dev_edf_bronze.staging.customer_changes',
    'dev_edf_silver.dps_stage.customer_chg',
    'CHG',
    'Customer_CDC_Job',                      -- Databricks job name
    '/Workspace/ETL_Jobs/Customer_CDC',      -- Notebook path
    'Customer CDC - overwrite mode'
);
```

## 🔄 ADF Pipeline Flow

### **Step 1: Lookup Activity**

Get all active jobs from ETL_AUDT_REF:

```json
{
    "name": "Lookup_Active_Jobs",
    "type": "Lookup",
    "typeProperties": {
        "source": {
            "type": "DatabricksSource",
            "query": "SELECT job_name, src_table1, target_table, chg_final, databricks_job_name, notebook_path FROM dev_edf_silver.dps_stage.ETL_AUDT_REF WHERE active_flag = 'Y'"
        },
        "firstRowOnly": false
    }
}
```

**Output Example:**
```json
{
    "count": 3,
    "value": [
        {
            "job_name": "JOB_SALES_ETL",
            "src_table1": "dev_edf_bronze.staging.sales_data",
            "target_table": "dev_edf_silver.dps_stage.sales_fact",
            "chg_final": "FINAL",
            "databricks_job_name": "Sales_ETL_Processing_Job",
            "notebook_path": "/Workspace/ETL_Jobs/Sales_Processing"
        },
        {
            "job_name": "JOB_CUSTOMER_CDC",
            "src_table1": "dev_edf_bronze.staging.customer_changes",
            "target_table": "dev_edf_silver.dps_stage.customer_chg",
            "chg_final": "CHG",
            "databricks_job_name": "Customer_CDC_Job",
            "notebook_path": "/Workspace/ETL_Jobs/Customer_CDC"
        }
    ]
}
```

### **Step 2: ForEach Loop**

Loop through each job and trigger corresponding Databricks job:

```json
{
    "name": "ForEach_Job",
    "type": "ForEach",
    "dependsOn": [
        {
            "activity": "Lookup_Active_Jobs",
            "dependencyConditions": ["Succeeded"]
        }
    ],
    "typeProperties": {
        "items": {
            "value": "@activity('Lookup_Active_Jobs').output.value",
            "type": "Expression"
        },
        "isSequential": false,
        "batchCount": 5,
        "activities": [
            {
                "name": "Run_Validation_Notebook",
                "type": "DatabricksNotebook",
                "typeProperties": {
                    "notebookPath": "/Workspace/Notebooks/Databricks_Notebook1_Lookup_Validation",
                    "baseParameters": {
                        "job_name": "@item().job_name",
                        "src_table1": "@item().src_table1",
                        "catalog_name": "dev_edf_silver",
                        "schema_name": "dps_stage"
                    }
                }
            },
            {
                "name": "Trigger_Databricks_Job",
                "type": "DatabricksSparkJar",
                "dependsOn": [
                    {
                        "activity": "Run_Validation_Notebook",
                        "dependencyConditions": ["Succeeded"]
                    }
                ],
                "typeProperties": {
                    "jobName": "@item().databricks_job_name"
                }
            }
        ]
    }
}
```

## 📝 Complete ADF Pipeline JSON

```json
{
    "name": "ETL_Audit_Pipeline_with_Job_Looping",
    "properties": {
        "activities": [
            {
                "name": "Lookup_Active_Jobs",
                "type": "Lookup",
                "typeProperties": {
                    "source": {
                        "type": "DatabricksSource",
                        "query": "SELECT job_name, src_table1, target_table, chg_final, databricks_job_name, notebook_path FROM dev_edf_silver.dps_stage.ETL_AUDT_REF WHERE active_flag = 'Y'"
                    },
                    "firstRowOnly": false
                },
                "linkedServiceName": {
                    "referenceName": "AzureDatabricks_LinkedService",
                    "type": "LinkedServiceReference"
                }
            },
            {
                "name": "ForEach_Job",
                "type": "ForEach",
                "dependsOn": [
                    {
                        "activity": "Lookup_Active_Jobs",
                        "dependencyConditions": ["Succeeded"]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('Lookup_Active_Jobs').output.value",
                        "type": "Expression"
                    },
                    "isSequential": false,
                    "batchCount": 5,
                    "activities": [
                        {
                            "name": "Notebook1_Validation",
                            "type": "DatabricksNotebook",
                            "typeProperties": {
                                "notebookPath": "/Workspace/Notebooks/Databricks_Notebook1_Lookup_Validation",
                                "baseParameters": {
                                    "job_name": {
                                        "value": "@item().job_name",
                                        "type": "Expression"
                                    },
                                    "src_table1": {
                                        "value": "@item().src_table1",
                                        "type": "Expression"
                                    },
                                    "catalog_name": "dev_edf_silver",
                                    "schema_name": "dps_stage"
                                }
                            },
                            "linkedServiceName": {
                                "referenceName": "AzureDatabricks_LinkedService",
                                "type": "LinkedServiceReference"
                            }
                        },
                        {
                            "name": "Run_Processing_Notebook",
                            "type": "DatabricksNotebook",
                            "dependsOn": [
                                {
                                    "activity": "Notebook1_Validation",
                                    "dependencyConditions": ["Succeeded"]
                                }
                            ],
                            "typeProperties": {
                                "notebookPath": {
                                    "value": "@item().notebook_path",
                                    "type": "Expression"
                                },
                                "baseParameters": {
                                    "job_name": {
                                        "value": "@item().job_name",
                                        "type": "Expression"
                                    },
                                    "target_table": {
                                        "value": "@item().target_table",
                                        "type": "Expression"
                                    },
                                    "chg_final": {
                                        "value": "@item().chg_final",
                                        "type": "Expression"
                                    }
                                }
                            },
                            "linkedServiceName": {
                                "referenceName": "AzureDatabricks_LinkedService",
                                "type": "LinkedServiceReference"
                            }
                        },
                        {
                            "name": "Final_Cleanup",
                            "type": "DatabricksNotebook",
                            "dependsOn": [
                                {
                                    "activity": "Run_Processing_Notebook",
                                    "dependencyConditions": ["Succeeded"]
                                }
                            ],
                            "typeProperties": {
                                "notebookPath": "/Workspace/Notebooks/Final_Notebook_Cleanup",
                                "baseParameters": {
                                    "database_name": "dev_edf_silver.dps_stage",
                                    "target_table": {
                                        "value": "@item().target_table",
                                        "type": "Expression"
                                    }
                                }
                            },
                            "linkedServiceName": {
                                "referenceName": "AzureDatabricks_LinkedService",
                                "type": "LinkedServiceReference"
                            }
                        }
                    ]
                }
            }
        ],
        "annotations": []
    }
}
```

## 🎯 Use Cases

### **Use Case 1: Trigger Databricks Jobs by Name**

```sql
-- Configure job to trigger specific Databricks job
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES (
    'JOB_DAILY_REPORT',
    'dev_edf_bronze.staging.report_data',
    'dev_edf_silver.dps_stage.daily_reports',
    'FINAL',
    'Daily_Report_Generation_Job',  -- This Databricks job will be triggered
    '/Workspace/Reports/Daily_Report_Generator',
    'Daily report generation'
);
```

### **Use Case 2: Run Specific Notebooks**

```sql
-- Configure job to run specific notebook
INSERT INTO dev_edf_silver.dps_stage.ETL_AUDT_REF VALUES (
    'JOB_DATA_QUALITY',
    'dev_edf_bronze.staging.raw_data',
    'dev_edf_silver.dps_stage.quality_checked_data',
    'FINAL',
    NULL,  -- No Databricks job, just notebook
    '/Workspace/Quality/Data_Quality_Checks',  -- This notebook will run
    'Data quality validation'
);
```

### **Use Case 3: Mixed Approach**

```sql
-- Some jobs trigger Databricks jobs, others run notebooks directly
SELECT 
    job_name,
    CASE 
        WHEN databricks_job_name IS NOT NULL THEN 'Trigger Job: ' || databricks_job_name
        WHEN notebook_path IS NOT NULL THEN 'Run Notebook: ' || notebook_path
        ELSE 'No processing defined'
    END as processing_method
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE active_flag = 'Y';
```

## 📊 Query Examples

### **Get Jobs for ADF Looping**

```sql
-- Get all active jobs with their Databricks configurations
SELECT 
    job_name,
    src_table1,
    target_table,
    chg_final,
    databricks_job_name,
    notebook_path,
    CASE 
        WHEN chg_final = 'CHG' THEN 'OVERWRITE'
        WHEN chg_final = 'FINAL' THEN 'APPEND'
        ELSE 'UNKNOWN'
    END as write_mode
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE active_flag = 'Y'
ORDER BY job_name;
```

### **Get Jobs by Type**

```sql
-- Get only CHG jobs
SELECT job_name, databricks_job_name, notebook_path
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE active_flag = 'Y' AND chg_final = 'CHG';

-- Get only FINAL jobs
SELECT job_name, databricks_job_name, notebook_path
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE active_flag = 'Y' AND chg_final = 'FINAL';
```

### **Validate Configuration**

```sql
-- Check for jobs without processing configuration
SELECT 
    job_name,
    CASE 
        WHEN databricks_job_name IS NULL AND notebook_path IS NULL THEN 'Missing Configuration'
        WHEN databricks_job_name IS NOT NULL AND notebook_path IS NOT NULL THEN 'Both Configured (Use Job)'
        WHEN databricks_job_name IS NOT NULL THEN 'Job Configured'
        WHEN notebook_path IS NOT NULL THEN 'Notebook Configured'
    END as config_status
FROM dev_edf_silver.dps_stage.ETL_AUDT_REF
WHERE active_flag = 'Y';
```

## 🔧 Configuration Best Practices

### **1. Naming Conventions**

```
Databricks Job Names:
- Use descriptive names: Sales_ETL_Processing_Job
- Include purpose: Customer_CDC_Job
- Avoid spaces: Use underscores

Notebook Paths:
- Organize by function: /Workspace/ETL_Jobs/
- Use clear names: /Workspace/ETL_Jobs/Sales_Processing
- Keep consistent structure
```

### **2. Priority: Job vs Notebook**

```sql
-- If both are configured, ADF should prioritize databricks_job_name
-- Databricks jobs provide better monitoring and scheduling

CASE 
    WHEN databricks_job_name IS NOT NULL THEN 
        'Trigger Databricks Job'
    WHEN notebook_path IS NOT NULL THEN 
        'Run Notebook Directly'
    ELSE 
        'No Processing Configured'
END
```

### **3. Update Configuration**

```sql
-- Update Databricks job name
UPDATE dev_edf_silver.dps_stage.ETL_AUDT_REF
SET databricks_job_name = 'New_Job_Name',
    update_ts = CURRENT_TIMESTAMP()
WHERE job_name = 'JOB_SALES_ETL';

-- Update notebook path
UPDATE dev_edf_silver.dps_stage.ETL_AUDT_REF
SET notebook_path = '/Workspace/ETL_Jobs/New_Path',
    update_ts = CURRENT_TIMESTAMP()
WHERE job_name = 'JOB_SALES_ETL';
```

## 📋 Summary

**Key Benefits:**

1. ✅ **Dynamic Job Triggering**: ADF can trigger different Databricks jobs based on configuration
2. ✅ **Flexible Processing**: Support both Databricks jobs and direct notebook execution
3. ✅ **Easy Maintenance**: Update job configurations without changing ADF pipeline
4. ✅ **Parallel Processing**: ForEach loop can process multiple jobs simultaneously
5. ✅ **Audit Trail**: All job configurations tracked in ETL_AUDT_REF

**What ADF Will Do:**

1. Query ETL_AUDT_REF for active jobs
2. Loop through each job
3. Run Notebook1 for validation
4. Trigger the specified Databricks job or run the notebook
5. Run Final Notebook for cleanup
6. Process next job in parallel (up to batchCount limit)

**This enables fully dynamic, configuration-driven ETL orchestration!** 🚀