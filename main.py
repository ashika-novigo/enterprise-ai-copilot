from tools.leave_tools import apply_leave, check_leave_balance, get_leave_history

# Direct test (no LangChain)
print(apply_leave.invoke({
    "employee_id": 101,
    "leave_type": "sick",
    "start_date": "2026-05-01",
    "end_date": "2026-05-03",
    "reason": "fever"
}))

print(check_leave_balance.invoke({
    "employee_id": 101
}))

print(get_leave_history.invoke({
    "employee_id": 101
}))