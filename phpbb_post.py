import string
import cgi
import re
from sgmllib import SGMLParser
import phpbb_prompt

class PrePostParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.creation_time = ""
        self.form_token = ""
    def start_input(self, attrs) :
        creation_time = False
        form_token = False
        value = ""
        for (attr_name, attr_value) in attrs :
            if attr_name == "name" and attr_value == "creation_time" :
                creation_time = True
            elif attr_name == "name" and attr_value == "form_token" :
                form_token = True
            if attr_name == "value" :
                value = attr_value
        if creation_time :
            self.creation_time = value
        elif form_token :
            self.form_token = value
    def handle_data(self, data) :
        phpbb_prompt.PromptParser.handle_data(self, data)

class PostParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.__parsing_information = False
        self.__parsing_error = False
        self.published_forum = -1
        self.published_topic = -1
        self.published_post = -1
    def start_div(self, attrs) :
        phpbb_prompt.PromptParser.start_div(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "id" and attr_value == "message" :
                self.__parsing_information = True
    def end_div(self) :
        phpbb_prompt.PromptParser.end_div(self)
        if self.__parsing_information :
            self.__parsing_information = False
    def start_p(self, attrs) :
        phpbb_prompt.PromptParser.start_p(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "error" :
                self.__parsing_error = True
    def end_p(self) :
        phpbb_prompt.PromptParser.end_p(self)
        if self.__parsing_error :
            self.__parsing_error = False
    def start_a(self, attrs) :
        if self.__parsing_information :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" :
                    if string.find(attr_value, "viewtopic.php") >= 0 :
                        f_t_p_indexes_list = re.findall("[^r]t=(\d+)", attr_value)
                        for (id_index) in f_t_p_indexes_list :
                            self.published_topic = int(id_index)
                        f_t_p_indexes_list = re.findall("p=(\d+)", attr_value)
                        for (id_index) in f_t_p_indexes_list :
                            self.published_post = int(id_index)
                    elif string.find(attr_value, "viewforum.php") >= 0 :
                        f_t_p_indexes_list = re.findall("f=(\d+)", attr_value)
                        for (id_index) in f_t_p_indexes_list :
                            self.published_forum = int(id_index)
    def handle_data(self, data) :
        phpbb_prompt.PromptParser.handle_data(self, data)
        if self.__parsing_error :
            self.prompt_message_text += data

class AddFileParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.file_id = -1
        self.__parsing_file = False
        self.__parsing_error = False
    def start_textarea(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "id" and string.find(attr_value, "comment_list") >= 0 :
                self.__parsing_file = True
    def start_p(self, attrs) :
        phpbb_prompt.PromptParser.start_p(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "error" :
                self.__parsing_error = True
    def end_p(self) :
        phpbb_prompt.PromptParser.end_p(self)
        if self.__parsing_error :
            self.__parsing_error = False
    def start_a(self, attrs) :
        if self.__parsing_file :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" and string.find(attr_value, "download/file.php") >= 0 :
                    file_id_list = re.findall("[^s]id=(\d+)", attr_value)
                    for (file_id) in file_id_list :
                        self.file_id = int(file_id)
            self.__parsing_file = False
    def handle_data(self, data) :
        phpbb_prompt.PromptParser.handle_data(self, data)
        if self.__parsing_error :
            self.prompt_message_text += data
