import frappe

import frappe
from frappe.utils import get_datetime, get_datetime_str
from datetime import datetime, timedelta

@frappe.whitelist()
def get_employee_checkin_entries(employee, attendance_date):
    # Convert string to datetime and define start and end of the day
    start_date = get_datetime(attendance_date)
    end_date = start_date + timedelta(days=1)

    # Fetch first check-in (earliest)
    in_time_doc = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [start_date, end_date]]
        },
        fields=["time"],
        order_by="time asc",
        limit_page_length=1
    )

    # Fetch last check-in (latest)
    out_time_doc = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", [start_date, end_date]]
        },
        fields=["time"],
        order_by="time desc",
        limit_page_length=1
    )

    return {
        "in_time": in_time_doc[0].time if in_time_doc else None,
        "out_time": out_time_doc[0].time if out_time_doc else None
    }

@frappe.whitelist()
def get_offday_status(employee, attendance_date,attendance):
    
    from datetime import datetime
    
    if isinstance(attendance_date, str):
        date_obj = datetime.strptime(attendance_date, "%Y-%m-%d").date()
    else:
        date_obj = attendance_date
    
    # Step 1: Check Holiday List
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    if holiday_list:
        if frappe.db.exists("Holiday", {"holiday_date": date_obj, "parent": holiday_list}):
            holiday_doc = frappe.get_doc("Holiday List",holiday_list)

            for holiday in holiday_doc.holidays:
                if attendance:
                    if holiday.weekly_off:
                        frappe.db.set_value("Attendance", attendance, {
                        "status": "Weekly Off",
                        "leave_type": None
                        })
                        frappe.db.commit()
                        return "Weekly Off"
                    else:
                        frappe.db.set_value("Attendance", attendance, {
                            "status": "Holiday",
                            "leave_type": None
                            })
                        frappe.db.commit()
                        return "Holiday"
   
    # Step 2: Check Shift Assignment for weekly off

    shift_assignment = frappe.get_all(
    "Shift Assignment",
    filters={
        "employee": employee,
        "start_date": ["<=", date_obj],
    },
    fields=["name", "shift_type", "custom_off_day", "end_date"]
    )

    valid_shift_assignments = []

    for shift in shift_assignment:
        if not shift["end_date"] or shift["end_date"] >= date_obj:
            valid_shift_assignments.append(shift)

    if valid_shift_assignments:
        weekday = date_obj.strftime('%A')
        emp_offday = valid_shift_assignments[0]["custom_off_day"]

        if weekday == emp_offday:
            if attendance:
                frappe.db.set_value("Attendance", attendance, {
                    "status": "Weekly Off",
                    "leave_type": None
                })
                frappe.db.commit()
            return "Weekly Off"

