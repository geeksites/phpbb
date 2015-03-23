import re
import time

def parse(time_string) :
    if re.match(".*\d{2}.*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\d{4}", time_string) :
        time_struct = re.findall(".*(\d{2}).*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*(\d{4}).*?(\d{1,2}).*?(\d{1,2}).*", time_string)
        if time_struct :
            day, month_code, year, hour, minute = time_struct[0]
            month = {"Jan" : 1, "Feb" : 2, "Mar" : 3, "Apr" : 4, "May" : 5, "Jun" : 6,
                     "Jul" : 7, "Aug" : 8, "Sep" : 9, "Oct" : 10, "Nov" : 11, "Dec" : 12}[month_code]
            return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
    if re.match(".*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\d{2}.*\d{4}", time_string) :
        time_struct = re.findall(".*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*(\d{2}).*(\d{4}).*?(\d{1,2}).*?(\d{1,2}).*(am|pm)", time_string)
        if time_struct :
            month_code, day, year, hour, minute, aorp = time_struct[0]
            month = {"Jan" : 1, "Feb" : 2, "Mar" : 3, "Apr" : 4, "May" : 5, "Jun" : 6,
                     "Jul" : 7, "Aug" : 8, "Sep" : 9, "Oct" : 10, "Nov" : 11, "Dec" : 12}[month_code]
            if aorp == "pm" :
                hour = int(hour) + 12
            return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
        else :
            time_struct = re.findall(".*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*(\d{2}).*(\d{4}).*?(\d{1,2}).*?(\d{1,2}).*", time_string)
            if time_struct :
                month_code, day, year, hour, minute = time_struct[0]
                month = {"Jan" : 1, "Feb" : 2, "Mar" : 3, "Apr" : 4, "May" : 5, "Jun" : 6,
                         "Jul" : 7, "Aug" : 8, "Sep" : 9, "Oct" : 10, "Nov" : 11, "Dec" : 12}[month_code]
                return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
    if re.match(".*\d{4}.*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*\d{1,2}", time_string) :
        time_struct = re.findall(".*(\d{4}).*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*", time_string)
        if time_struct :
            year, month_code, day, hour, minute = time_struct[0]
            month = {"Jan" : 1, "Feb" : 2, "Mar" : 3, "Apr" : 4, "May" : 5, "Jun" : 6,
                     "Jul" : 7, "Aug" : 8, "Sep" : 9, "Oct" : 10, "Nov" : 11, "Dec" : 12}[month_code]
            return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
    if re.match(".*\d{4}.*\d{2}.*\d{2}", time_string) :
        time_struct = re.findall(".*?(\d{4}).*?(\d{2}).*?(\d{2}).*?(\d{1,2}).*?(\d{1,2}).*(am|pm)", time_string)
        if time_struct :
            year, month, day, hour, minute, aorp = time_struct[0]
            if aorp == "pm" :
                hour = int(hour) + 12
            return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
        else :
            time_struct = re.findall(".*?(\d{4}).*?(\d{2}).*?(\d{2}).*?(\d{1,2}).*?(\d{1,2})", time_string)
            if time_struct :
                year, month, day, hour, minute = time_struct[0]
                return int(time.mktime((int(year), int(month), int(day), int(hour), int(minute), 0, 0, 0, 0)))
    return 0
