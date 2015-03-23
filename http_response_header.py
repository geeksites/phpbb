import re

http_status = 0
http_status_text = ''

def status_line(buffer) :
    result = re.match("(?P<http_version>[^ ]*) (?P<status_code>[^ ]*) (?P<reason_phase>[^\r\n]*)", buffer)
    global http_status
    global http_status_text
    http_status = int(result.groupdict()['status_code'])
    http_status_text = str(result.groupdict()['reason_phase'])
    if re.search('[\r\n]+', buffer) :
        return re.split('[\r\n]+', buffer, 1)[1]

def set_cookie_field(cookie_buffer, cookie_reader) :
    cookies = re.findall("(?P<cookie_name>.*?)=(?P<cookie_value>[^;\r\n]*);? *", cookie_buffer)
    cookie_reader(cookies)

def fields(buffer, cookie_reader) :
    if re.search('<', buffer) :
        [field_buffer, html_buffer] = re.split('<', buffer, 1)
    else :
        [field_buffer, html_buffer] = [buffer, None]
    fields = re.findall("(?P<field_name>.*?): (?P<field_value>[^\r\n]*)", field_buffer)
    for (field_name, field_value) in fields:
        if field_name == "Set-Cookie" :
            set_cookie_field(field_value, cookie_reader)
    if html_buffer :
        return '<' + html_buffer

def read(buffer) :
    return status_line(buffer)
