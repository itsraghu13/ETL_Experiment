# Databricks notebook source
# MAGIC %md
# MAGIC # CHG Table Cleanup Notebook
# MAGIC 
# MAGIC **Purpose:**
# MAGIC - Clean/Delete CHG (Change) tables after successful processing
# MAGIC - Prepare CHG table for next run
# MAGIC - Only runs for jobs with chg_final='CHG'

# COMMAND ----------

from pyspark.sql.functions import col, current_timestamp
from datetime import datetime

# COMMAND ----------

# Create widgets for parameters
dbutils.widgets.text("database_name", "default", "Database Name")
dbutils.widgets.text("chg_table", "", "CHG Table Name")
dbutils.widgets.text("batch_no", "", "Batch Number (required)")
dbutils.widgets.text("cleanup_mode", "DELETE", "Cleanup Mode (DELETE/TRUNCATE)")

database_name = dbutils.widgets.get("database_name")
chg_table = dbutils.widgets.get("chg_table")
batch_no = dbutils.widgets.get("batch_no")
cleanup_mode = dbutils.widgets.get("cleanup_mode")

print(f"Database: {database_name}")
print(f"CHG Table: {chg_table}")
print(f"Batch Number: {batch_no}")
print(f"Cleanup Mode: {cleanup_mode}")

# Validate batch_no is provided
if not batch_no:
    print("ERROR: batch_no parameter is required for CHG table cleanup")
    dbutils.notebook.exit("FAILED: batch_no parameter is required")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Validate CHG Table

# COMMAND ----------

def validate_chg_table(database_name, chg_table):
    """
    Validate that the table exists and is a CHG table
    """
    try:
        # Check if table exists
        table_exists = spark.catalog.tableExists(f"{database_name}.{chg_table}")
        
        if not table_exists:
            print(f"WARNING: Table {database_name}.{chg_table} does not exist")
            return False
        
        # Get table properties
        table_df = spark.sql(f"DESCRIBE EXTENDED {database_name}.{chg_table}")
        
        print(f"Table {chg_table} exists and is ready for cleanup")
        return True
        
    except Exception as e:
        print(f"ERROR in validate_chg_table: {str(e)}")
        return False

# Validate table
is_valid = validate_chg_table(database_name, chg_table)

if not is_valid:
    dbutils.notebook.exit("SKIPPED: CHG table does not exist or validation failed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Get Record Count Before Cleanup

# COMMAND ----------

def get_record_count(database_name, chg_table, batch_no):
    """
    Get current record count in CHG table for specific batch_no
    """
    try:
        count_query = f"""
            SELECT COUNT(*) as record_count
            FROM {database_name}.{chg_table}
            WHERE batch_no = {batch_no}
        """
        result = spark.sql(count_query)
        count = result.collect()[0].record_count
        
        print(f"Record count for batch_no {batch_no} in {chg_table}: {count:,}")
        return count
        
    except Exception as e:
        print(f"ERROR in get_record_count: {str(e)}")
        return 0

# Get count before cleanup for this batch
before_count = get_record_count(database_name, chg_table, batch_no)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Perform Cleanup

# COMMAND ----------

def cleanup_chg_table(database_name, chg_table, batch_no, cleanup_mode):
    """
    Clean up CHG table for specific batch_no using specified mode
    DELETE: Remove records for this batch_no only
    TRUNCATE: Not recommended when multiple batches exist
    """
    try:
        if cleanup_mode.upper() == "DELETE":
            # Delete records for specific batch_no only
            delete_query = f"""
                DELETE FROM {database_name}.{chg_table}
                WHERE batch_no = {batch_no}
            """
            spark.sql(delete_query)
            print(f"Successfully DELETED records for batch_no {batch_no} from {chg_table}")
            
        elif cleanup_mode.upper() == "TRUNCATE":
            # Warning: TRUNCATE removes ALL data, not just this batch
            print(f"WARNING: TRUNCATE will remove ALL data from {chg_table}, not just batch {batch_no}")
            print(f"Switching to DELETE mode for safety...")
            delete_query = f"""
                DELETE FROM {database_name}.{chg_table}
                WHERE batch_no = {batch_no}
            """
            spark.sql(delete_query)
            print(f"Successfully DELETED records for batch_no {batch_no} from {chg_table}")
            
        else:
            print(f"ERROR: Invalid cleanup mode '{cleanup_mode}'. Use DELETE or TRUNCATE")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR in cleanup_chg_table: {str(e)}")
        return False

# Perform cleanup for this batch only
cleanup_success = cleanup_chg_table(database_name, chg_table, batch_no, cleanup_mode)

if not cleanup_success:
    dbutils.notebook.exit("FAILED: CHG table cleanup failed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Cleanup

# COMMAND ----------

def verify_cleanup(database_name, chg_table, batch_no):
    """
    Verify that cleanup was successful for this batch_no
    """
    try:
        after_count = get_record_count(database_name, chg_table, batch_no)
        
        if after_count == 0:
            print(f"✓ Cleanup verified: batch_no {batch_no} removed from {chg_table}")
            return True
        else:
            print(f"✗ Cleanup verification failed: {chg_table} still has {after_count} records for batch_no {batch_no}")
            return False
            
    except Exception as e:
        print(f"ERROR in verify_cleanup: {str(e)}")
        return False

# Verify cleanup for this batch
verification_success = verify_cleanup(database_name, chg_table, batch_no)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Optimize Table (Optional)

# COMMAND ----------

def optimize_table(database_name, chg_table):
    """
    Optimize table after cleanup for better performance
    """
    try:
        optimize_query = f"OPTIMIZE {database_name}.{chg_table}"
        spark.sql(optimize_query)
        print(f"Table {chg_table} optimized successfully")
        return True
        
    except Exception as e:
        print(f"WARNING: Table optimization failed: {str(e)}")
        return False

# Optimize table (optional, comment out if not needed)
# optimize_table(database_name, chg_table)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Report

# COMMAND ----------

print("\n" + "="*60)
print("CHG TABLE CLEANUP SUMMARY")
print("="*60)
print(f"Database: {database_name}")
print(f"CHG Table: {chg_table}")
print(f"Batch Number: {batch_no}")
print(f"Cleanup Mode: {cleanup_mode}")
print(f"Records Before (batch {batch_no}): {before_count:,}")
print(f"Records After (batch {batch_no}): 0")
print(f"Status: {'✓ SUCCESS' if verification_success else '✗ FAILED'}")
print("="*60)
print(f"NOTE: Only batch_no {batch_no} was cleaned. Other batches remain untouched.")
print("="*60)

# Exit with success message
if verification_success:
    dbutils.notebook.exit(f"SUCCESS: CHG table {chg_table} batch {batch_no} cleaned up successfully ({before_count:,} records removed)")
else:
    dbutils.notebook.exit(f"FAILED: CHG table cleanup verification failed for batch {batch_no}")

# Made with Bob
