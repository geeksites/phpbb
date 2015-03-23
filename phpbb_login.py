from sgmllib import SGMLParser

class LoginParser(SGMLParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        self.__parsing_error_message = False
        self.login_status = True
        self.error_message = ""
    def start_div(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "error" :
                self.__parsing_error_message = True
                self.login_status = False
    def end_div(self) :
        if self.__parsing_error_message :
            self.__parsing_error_message = False
    def handle_data(self, data) :
        if self.__parsing_error_message :
            self.error_message += data
