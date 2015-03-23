import cgi
from sgmllib import SGMLParser
import phpbb_prompt

class Parser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self._parsing_form = False
    def start_form(self, attrs) :
        phpbb_prompt.PromptParser.start_form(self, attrs)
        ucp_id = False
        ucp_action = False
        for (attr_name, attr_value) in attrs :
            if attr_name == "id" and attr_value == "ucp" :
                ucp_id = True
            elif attr_name == "action" and attr_value.find("ucp.php") :
                ucp_action = True
        if ucp_id and ucp_action :
            self._parsing_form = True
    def end_form(self) :
        phpbb_prompt.PromptParser.end_form(self)
        if self._parsing_form :
            self._parsing_form = False

class DisplayNameParser(Parser) :
    def __init__(self) :
        Parser.__init__(self)
        self.__parsing_displayname = False
        self.displayname = ""
    def start_strong(self, attrs) :
        if self._parsing_form :
            self.__parsing_displayname = True
            self.displayname = ""
    def end_strong(self) :
        if self.__parsing_displayname :
            self.__parsing_displayname = False
    def handle_data(self, data) :
        if not phpbb_prompt.PromptParser.handle_data(self, data) :
            if self.__parsing_displayname :
                self.displayname += cgi.escape(data)

class AvatarParser(Parser) :
    def __init__(self) :
        Parser.__init__(self)
        self.avatar = ""
    def start_img(self, attrs) :
        if self._parsing_form :
            for (attr_name, attr_value) in attrs :
                if attr_name == "src" :
                    self.avatar = attr_value
    def handle_data(self, data) :
        phpbb_prompt.PromptParser.handle_data(self, data)
