"""
database.py
-----------


"""

import logging
import sqlite3
from typing import Optional

import pandas as pd

from src.config import DB_PATH, REDACTED_COLUMNS

logger = logging.getLogger("inventra.database")


# ── Connection ────────────────────────────────────────────────────────────────
def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():

        logger.error("hospital.db not found at %s", DB_PATH)
        raise FileNotFoundError(
            "Hospital database not found. "
            "Please run notebooks/01_load_data.ipynb to initialise it."
        )
    return sqlite3.connect(
        f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False
    )


def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a safe parameterised read-only query. Auto-strips PII."""
    conn = None
    try:
        conn = _connect()
        df = pd.read_sql(sql, conn, params=params)
        pii = [c for c in REDACTED_COLUMNS if c in df.columns]
        if pii:
            df = df.drop(columns=pii)
        return df
    except sqlite3.Error as e:
        logger.error("DB error: %s", e)
        raise RuntimeError("A database error occurred. Please try again.") from e
    finally:
        if conn:
            conn.close()


# ── KPI counts ────────────────────────────────────────────────────────────────
def get_kpi_counts() -> dict:
    conn = None
    try:
        conn = _connect()
        critical = pd.read_sql(
            "SELECT COUNT(*) as n FROM inventory WHERE Urgency_Level='CRITICAL'", conn
        ).iloc[0]["n"]
        restock = pd.read_sql(
            "SELECT COUNT(*) as n FROM inventory WHERE Restock_Alert=1", conn
        ).iloc[0]["n"]
        delayed = pd.read_sql(
            "SELECT COUNT(*) as n FROM vendor WHERE Vendor_Status='DELAYED'", conn
        ).iloc[0]["n"]
        spend = pd.read_sql(
            "SELECT ROUND(SUM(Amount)/1000000,1) as s FROM financial", conn
        ).iloc[0]["s"]
    finally:
        if conn:
            conn.close()
    return {
        "critical":             int(critical),
        "restock":              int(restock),
        "delayed":              int(delayed),
        "total_spend_millions": float(spend),
    }


# ── Inventory ─────────────────────────────────────────────────────────────────
def get_critical_items(limit: int = 5) -> pd.DataFrame:
    return _query("""
        SELECT Item_Name, Current_Stock, Days_Until_Stockout,
               Restock_Lead_Time, Restock_Urgency_Days, Vendor_ID
        FROM   inventory
        WHERE  Urgency_Level = 'CRITICAL'
        ORDER  BY Days_Until_Stockout ASC
        LIMIT  ?
    """, (limit,))


def get_restock_alerts(limit: int = 10) -> pd.DataFrame:
    return _query("""
        SELECT Item_Name, Current_Stock, Days_Until_Stockout,
               Urgency_Level, Vendor_ID
        FROM   inventory
        WHERE  Restock_Alert = 1
        ORDER  BY Restock_Urgency_Days ASC
        LIMIT  ?
    """, (limit,))


def get_overstock_items(limit: int = 10) -> pd.DataFrame:
    return _query("""
        SELECT Item_Name, Current_Stock, Max_Capacity,
               (Current_Stock - Max_Capacity) AS Excess_Units,
               Unit_Cost,
               ROUND((Current_Stock - Max_Capacity) * Unit_Cost, 2) AS Capital_Tied_Up,
               Vendor_ID
        FROM   inventory
        WHERE  Flag_OverStock = 1
        ORDER  BY Capital_Tied_Up DESC
        LIMIT  ?
    """, (limit,))


def get_all_inventory() -> pd.DataFrame:
    return _query("""
        SELECT Item_Name, Item_Type, Current_Stock, Min_Required,
               Max_Capacity, Unit_Cost, Avg_Usage_Per_Day,
               Restock_Lead_Time, Days_Until_Stockout,
               Urgency_Level, Restock_Alert, Vendor_ID
        FROM   inventory
        ORDER  BY Urgency_Level DESC, Days_Until_Stockout ASC
    """)


# ── Vendor ────────────────────────────────────────────────────────────────────
def get_vendor_risks() -> pd.DataFrame:
    return _query("""
        SELECT Vendor_Name, Item_Supplied,
               Avg_Lead_Time_days, Lead_Time_Actual_Days,
               Delay_Days, Vendor_Status
        FROM   vendor
        WHERE  Vendor_Status = 'DELAYED'
        ORDER  BY Delay_Days DESC
    """)


def get_all_vendors() -> pd.DataFrame:
    return _query("""
        SELECT Vendor_ID, Vendor_Name, Item_Supplied,
               Avg_Lead_Time_days, Lead_Time_Actual_Days,
               Delay_Days, Vendor_Status
        FROM   vendor
        ORDER  BY Delay_Days DESC
    """)


# ── Financial ─────────────────────────────────────────────────────────────────
def get_spend_summary() -> pd.DataFrame:
    return _query("""
        SELECT Expense_Category,
               COUNT(*)              AS Transactions,
               ROUND(SUM(Amount), 2) AS Total_Spend,
               ROUND(AVG(Amount), 2) AS Avg_Spend
        FROM   financial
        GROUP  BY Expense_Category
        ORDER  BY Total_Spend DESC
    """)


def get_monthly_spend(year_month: Optional[str] = None) -> pd.DataFrame:
    if year_month:
        return _query("""
            SELECT Year_Month, Expense_Category, Description,
                   ROUND(SUM(Amount), 2) AS Total_Spend,
                   COUNT(*)              AS Transactions
            FROM   financial
            WHERE  Year_Month = ?
            GROUP  BY Year_Month, Expense_Category, Description
            ORDER  BY Total_Spend DESC
        """, (year_month,))
    return _query("""
        SELECT Year_Month, Expense_Category,
               ROUND(SUM(Amount), 2) AS Total_Spend,
               COUNT(*)              AS Transactions
        FROM   financial
        GROUP  BY Year_Month, Expense_Category
        ORDER  BY Year_Month DESC, Total_Spend DESC
    """)


# ── Patient ───────────────────────────────────────────────────────────────────
def get_patient_supply_usage(room_type: Optional[str] = None) -> pd.DataFrame:
    if room_type:
        return _query("""
            SELECT Primary_Diagnosis, Room_Type, Procedure_Performed,
                   Supplies_Used, Equipment_Used, Bed_Days
            FROM   patient
            WHERE  Room_Type = ?
            ORDER  BY Bed_Days DESC
            LIMIT  20
        """, (room_type,))
    return _query("""
        SELECT Primary_Diagnosis, Room_Type, Procedure_Performed,
               Supplies_Used, Equipment_Used, Bed_Days
        FROM   patient
        ORDER  BY Bed_Days DESC
        LIMIT  20
    """)


def get_patient_diagnosis_summary() -> pd.DataFrame:
    return _query("""
        SELECT Primary_Diagnosis, Room_Type,
               COUNT(*)               AS Patient_Count,
               ROUND(AVG(Bed_Days),1) AS Avg_Bed_Days
        FROM   patient
        GROUP  BY Primary_Diagnosis, Room_Type
        ORDER  BY Patient_Count DESC
    """)


# ── Staff ─────────────────────────────────────────────────────────────────────
def get_staff_overtime() -> pd.DataFrame:
    return _query("""
        SELECT Staff_Type, Current_Assignment,
               Hours_Worked, Shift_Duration_Hours,
               Overtime_Hours, Patients_Assigned
        FROM   staff
        WHERE  Flag_HoursExceedShift = 1
        ORDER  BY Overtime_Hours DESC
        LIMIT  20
    """)


def get_staff_summary() -> pd.DataFrame:
    return _query("""
        SELECT Staff_Type, Current_Assignment,
               COUNT(*)                         AS Shifts,
               ROUND(AVG(Hours_Worked), 1)      AS Avg_Hours,
               ROUND(AVG(Overtime_Hours), 1)    AS Avg_OT,
               ROUND(AVG(Patients_Assigned), 1) AS Avg_Patients,
               SUM(CASE WHEN Flag_HoursExceedShift=1
                   THEN 1 ELSE 0 END)           AS OT_Shifts
        FROM   staff
        GROUP  BY Staff_Type, Current_Assignment
        ORDER  BY Avg_OT DESC
    """)


# ── LLM context builder ───────────────────────────────────────────────────────
def build_llm_context() -> str:
    """
    Compact, decision-focused context covering ALL 5 datasets.
    PII excluded automatically. Called by chain.py on every request.
    """
    try:
        critical_df  = get_critical_items()
        vendor_df    = get_vendor_risks()
        spend_df     = get_spend_summary()
        restock_df   = get_restock_alerts()
        overstock_df = get_overstock_items()
        staff_df     = get_staff_summary()
        patient_df   = get_patient_diagnosis_summary()

        critical_lines = []
        for _, r in critical_df.iterrows():
            critical_lines.append(
                f"  - {r['Item_Name']}: {r['Current_Stock']} units, "
                f"{r['Days_Until_Stockout']:.1f} days left, "
                f"lead time {r['Restock_Lead_Time']}d, vendor {r['Vendor_ID']}"
            )

        vendor_lines = []
        for _, r in vendor_df.iterrows():
            vendor_lines.append(
                f"  - {r['Vendor_Name']} ({r['Item_Supplied']}): "
                f"promised {r['Avg_Lead_Time_days']}d, "
                f"actual {r['Lead_Time_Actual_Days']}d, "
                f"+{r['Delay_Days']}d delay"
            )

        spend_lines = []
        for _, r in spend_df.iterrows():
            spend_lines.append(
                f"  - {r['Expense_Category']}: ${r['Total_Spend']:,.0f} total, "
                f"{r['Transactions']} transactions, avg ${r['Avg_Spend']:,.0f}"
            )

        restock_count   = len(restock_df)
        restock_summary = f"{restock_count} items need restocking"
        if restock_count > 0:
            top = restock_df.iloc[0]
            restock_summary += (
                f" — most urgent: {top['Item_Name']} "
                f"({top['Days_Until_Stockout']:.1f} days, {top['Vendor_ID']})"
            )

        overstock_lines = []
        for _, r in overstock_df.iterrows():
            overstock_lines.append(
                f"  - {r['Item_Name']}: {r['Excess_Units']} excess units, "
                f"${r['Capital_Tied_Up']:,.0f} capital tied up, "
                f"vendor {r['Vendor_ID']}"
            )

        staff_lines = []
        for _, r in staff_df.iterrows():
            staff_lines.append(
                f"  - {r['Staff_Type']} / {r['Current_Assignment']}: "
                f"{r['Shifts']} shifts, avg {r['Avg_Hours']}h worked, "
                f"avg {r['Avg_OT']}h overtime, "
                f"avg {r['Avg_Patients']} patients assigned, "
                f"{r['OT_Shifts']} shifts exceeded scheduled hours"
            )

        patient_lines = []
        for _, r in patient_df.iterrows():
            patient_lines.append(
                f"  - {r['Primary_Diagnosis']} / {r['Room_Type']}: "
                f"{r['Patient_Count']} patients, "
                f"avg {r['Avg_Bed_Days']} bed days"
            )

        return (
            f"CRITICAL STOCKOUTS ({len(critical_df)} items):\n"
            + ("\n".join(critical_lines) or "  None") + "\n\n"

            + f"RESTOCK ALERTS: {restock_summary}\n\n"

            + f"OVERSTOCKED ITEMS ({len(overstock_df)} items):\n"
            + ("\n".join(overstock_lines) or "  None") + "\n\n"

            + f"VENDOR DELAYS ({len(vendor_df)} vendors):\n"
            + ("\n".join(vendor_lines) or "  None") + "\n\n"

            + "SPEND SUMMARY:\n"
            + "\n".join(spend_lines) + "\n\n"

            + "STAFF WORKLOAD & OVERTIME (by type and assignment):\n"
            + "\n".join(staff_lines) + "\n\n"

            + "PATIENT DEMAND (by diagnosis and room type):\n"
            + "\n".join(patient_lines)
        )

    except Exception as e:
        logger.error("Failed to build LLM context: %s", e)
        return "[Data temporarily unavailable. Please try again.]"
