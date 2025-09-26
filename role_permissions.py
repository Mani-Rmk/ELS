ROLE_PERMISSIONS = {
    "employee": [
        "create_leave",          # submit leave request
        "cancel_own_leave",      # cancel pending leave
        "view_own_leave",        # view own leave requests
        "update_own_leave",      # update own pending leave
        "delete_own_leave",      # delete own pending leave
        "view_own_attendance"    # view own attendance
    ],
    "manager": [
    "approve_leave",
    "reject_leave",
    "view_team_leave",
    "view_team_attendance",
    "view_own_attendance"
    ],
    "hr": [
        "approve_leave",
        "reject_leave",
        "view_all_leave",
        "update_leave",          # update any leave
        "delete_leave",          # delete any leave
        "view_all_attendance",
        "create_employee",       # create employee
        "upload_employees",      # bulk upload employees
        "update_employee",       # update employee data
        "delete_employee",       # delete employee
        "view_all_employee"      # view all employees
    ],
    "admin": [
        "*"  # full access to everything
    ]
}
