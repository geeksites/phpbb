import cgi
from sgmllib import SGMLParser

class ContentParser(SGMLParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        self.__parsing_block_quote = False
        self.__gtalkabout_block_quote = False
        self.contents = []
    def start_blockquote(self, attrs) :
        self.__parsing_block_quote = True
    def end_blockquote(self) :
        if self.__parsing_block_quote :
            self.__parsing_block_quote = False
    def start_img(self, attrs) :
        if not self.__parsing_block_quote :
            for (attr_name, attr_value) in attrs :
                if attr_name == "src" :
                    self.contents.append((2, "", cgi.escape(attr_value)))
    def start_br(self, attrs) :
        self.contents.append((0, "\n", ""))
    def start_a(self, attrs) :
        href = ""
        for (attr_name, attr_value) in attrs :
            if attr_name == "href" :
                if attr_value.find(".gtalkabout.com") >= 0 :
                    self.__gtalkabout_block_quote = True
                else :
                    href = attr_value
        if self.__parsing_block_quote and self.__gtalkabout_block_quote :
            if href :
                self.contents.append((1, "", cgi.escape(href)))
    def handle_data(self, data) :
        if not self.__parsing_block_quote :
            self.contents.append((0, cgi.escape(data), ""))
