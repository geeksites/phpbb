from sgmllib import SGMLParser

class PromptParser(SGMLParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        self.__parsing_login = False
        self.__parsing_information = False
        self.__parsing_message_text = False
        self.prompt_message_text = ""
    def start_form(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "id" and attr_value == "login" :
                self.__parsing_login = True
    def end_form(self) :
        if self.__parsing_login :
            self.__parsing_login = False
    def start_h2(self, attrs) :
        if self.__parsing_login :
            self.__parsing_message_text = True
    def end_h2(self) :
        if self.__parsing_message_text :
            self.__parsing_message_text = False
    def start_div(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "id" and attr_value == "message" :
                self.__parsing_information = True
    def end_div(self) :
        if self.__parsing_information :
            self.__parsing_information = False
    def start_p(self, attrs) :
        if self.__parsing_information :
            self.__parsing_message_text = True
    def end_p(self) :
        if self.__parsing_message_text :
            self.__parsing_message_text = False
    def handle_data(self, data) :
        if self.__parsing_message_text :
            self.prompt_message_text += data
            self.__parsing_message_text = False
            self.__parsing_information = False
            self.__parsing_login = False
            return True
        return False
