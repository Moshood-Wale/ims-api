import re

def sanitize_phone_number(value):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~`:;,.-]')
    if regex.search(value) != None:
        return {"message": "Invalid Phone Number"}
    if value.startswith("+") and len(value) == 14:
        return value
    elif len(value) == 10:
        return "+234" + value
    elif len(value) == 11 and value.startswith("0"):
        return "+234" + value[1:]
    elif len(value) == 13 and value.startswith("234"):
        return f"+{value}"
    return {"message": "Number {0} is invalid nigerian number".format(value)}
    