import string
import cgi
import re
from sgmllib import SGMLParser
import phpbb_prompt
import phpbb_content
import phpbb_time_string

class ForumParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.forum = ()
        self.__parsing_forum = False
        self.__parsing_header = False
        self.__parsing_forum_block = False
        self.__parsing_block_title = False
        self.__parsing_child_forums = False
        self.__parsing_title = False
        self.__parsing_topic_total_count = False
        self.child_forums = []
        self.__parsing_forum_index = -1
        self.__parsing_forum_title = ""
        self.__parsing_announcement_topics = False
        self.__parsing_topics = False
        self.__parsing_topic_type = -1    # 0: normal 1: announcement
        self.__parsing_topic_index = -1
        self.__parsing_topic_title = ""
        self.topics = []
    def start_h2(self, attrs) :
        phpbb_prompt.PromptParser.start_h2(self, attrs)
        self.__parsing_forum = True
    def end_h2(self) :
        phpbb_prompt.PromptParser.end_h2(self)
        self.__parsing_forum = False
    def start_div(self, attrs) :
        phpbb_prompt.PromptParser.start_div(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" :
                if attr_value == "forabg" :
                    self.__parsing_forum_block = True
                    self.__parsing_child_forums = True
                elif attr_value == "pagination" :
                    self.__parsing_topic_total_count = True
                elif attr_value == "forumbg announcement" :
                    self.__parsing_announcement_topics = True
                elif attr_value == "forumbg" :
                    self.__parsing_topics = True
    def end_div(self) :
        phpbb_prompt.PromptParser.end_div(self)
        if self.__parsing_topic_total_count :
            self.__parsing_topic_total_count = False
    def start_li(self, attrs) :
        if self.__parsing_forum_block :
            for (attr_name, attr_value) in attrs :
                if attr_name == "class" and attr_value == "header" :
                    self.__parsing_header = True
    def end_li(self) :
        if self.__parsing_header :
            self.__parsing_header = False
    def start_dt(self, attrs) :
        if self.__parsing_header :
            self.__parsing_block_title = True
    def end_dt(self) :
        if self.__parsing_block_title :
            self.__parsing_block_title = False
    def start_span(self, attrs) :
        if self.__parsing_forum_block :
            for (attr_name, attr_value) in attrs :
                if attr_name == "class" and attr_value == "corners-bottom" :
                    self.__parsing_forum_block = False
                    self.__parsing_child_forums = False
        if self.__parsing_announcement_topics or self.__parsing_topics :
            for (attr_name, attr_value) in attrs :
                if attr_name == "class" and attr_value == "corners-bottom" :
                    self.__parsing_announcement_topics = False
                    self.__parsing_topics = False
    def start_a(self, attrs) :
        if self.__parsing_forum or self.__parsing_forum_block :
            forum_link = True
            child_forum = False
            forum_index = -1
            for (attr_name, attr_value) in attrs :
                if self.__parsing_block_title or self.__parsing_child_forums :
                    child_forum = True
                if attr_name == "href" :
                    if not attr_value or (string.find(attr_value, "viewforum.php") >= 0) :
                        f_t_p_indexes_list = re.findall("f=(\d+)", attr_value)
                        for (id_index) in f_t_p_indexes_list :
                            forum_index = id_index
                    else :
                        forum_link = False
            if forum_link and (self.__parsing_forum or child_forum) :
                self.__parsing_title = True
                self.__parsing_forum_index = int(forum_index)
            if self.__parsing_block_title :
                self.__parsing_child_forums = False
        if self.__parsing_announcement_topics or self.__parsing_topics :
            topic = False
            topic_index = -1
            for (attr_name, attr_value) in attrs :
                if attr_name == "class" and attr_value == "topictitle" :
                    topic = True
                if attr_name == "href" :
                    f_t_p_indexes_list = re.findall("[^r]t=(\d+)", attr_value)
                    for (id_index) in f_t_p_indexes_list :
                        topic_index = id_index
            if topic :
                self.__parsing_title = True
                self.__parsing_topic_index = int(topic_index)
    def end_a(self) :
        if self.__parsing_title :
            if self.__parsing_announcement_topics :
                self.topics.append((self.__parsing_topic_index, 1, self.__parsing_topic_title))
                self.__parsing_topic_index = -1
                self.__parsing_topic_title = ""
            elif self.__parsing_topics :
                self.topics.append((self.__parsing_topic_index, 0, self.__parsing_topic_title))
                self.__parsing_topic_index = -1
                self.__parsing_topic_title = ""
            elif self.__parsing_forum :
                self.forum = (self.__parsing_forum_index, self.__parsing_forum_title)
                self.__parsing_forum_index = -1
                self.__parsing_forum_title = ""
            elif self.__parsing_block_title or self.__parsing_child_forums :
                self.child_forums.append((self.__parsing_forum_index, self.__parsing_forum_title))
                self.__parsing_forum_index = -1
                self.__parsing_forum_title = ""
            self.__parsing_title = False
    def handle_data(self, data) :
        if not phpbb_prompt.PromptParser.handle_data(self, data) :
            if self.__parsing_title :
                if self.__parsing_announcement_topics or self.__parsing_topics :
                    self.__parsing_topic_title = data
                else :
                    self.__parsing_forum_title = data
            if self.__parsing_topic_total_count :
                topic_total_count_list = re.findall(" (\d+) ", data)
                for (count_number) in topic_total_count_list :
                    self.topic_total_count = count_number

class TopicParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.forum_id = 0
        self.forum_title = ''
        self.topic_id = 0
        self.topic_title = ''
        self.__parsing_forum = False
        self.__raw_html = ""
        self.__parsing_topic = False
        self.__parsing_title = False
        self.__parsing_topic_title = ""
        self.__parsing_post_total_count = False
        self.__parsing_posts = False
        self.__parsing_online = False
        self.__parsing_post_body = False
        self.__parsing_post_index = -1
        self.__parsing_author_online = False
        self.__parsing_author_information = False
        self.__parsing_post_author = False
        self.__parsing_author_title = ""
        self.__parsing_publish_time = 0
        self.__parsing_time_string = ""
        self.__parsing_post_subject = False
        self.__parsing_subject_text = False
        self.__parsing_post_content = False
        self.__parsing_content_div_count = 0
        self.__parsing_content_div_stack = 0
        self.__parsing_content_string = ""
        self.posts = []
        self.post_total_count = 0
        self.__last_post_id = 0
        self.__last_post_online = False
        self.__last_post_subject = ""
        self.__last_post_author = ""
        self.__last_post_time = 0
    def feed(self, data) :
        self.__raw_html = data
        SGMLParser.feed(self, data)
    def start_h2(self, attrs) :
        phpbb_prompt.PromptParser.start_h2(self, attrs)
        self.__parsing_topic = True
    def end_h2(self) :
        phpbb_prompt.PromptParser.end_h2(self)
        self.__parsing_topic = False
    def start_h3(self, attrs) :
        if self.__parsing_post_body :
            self.__parsing_post_subject = True
    def end_h3(self) :
        if self.__parsing_post_subject :
            self.__parsing_post_subject = False
    def start_div(self, attrs) :
        phpbb_prompt.PromptParser.start_div(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" :
                if attr_value == "pagination" :
                    self.__parsing_post_total_count = True
                elif self.__parsing_posts and (string.find(attr_value, "online") >= 0) :
                    self.__parsing_author_online = True
                    self.__last_post_online = self.__parsing_author_online
                elif self.__parsing_posts and attr_value == "postbody" :
                    self.__parsing_post_body = True
                elif self.__parsing_posts and attr_value == "content" :
                    self.__parsing_post_content = True
                    self.__parsing_content_string = ""
            if attr_name == "id" :
                if attr_value == "page-body" :
                    self.__parsing_posts = True
                elif attr_value == "page-footer" :
                    self.__parsing_posts = False
                elif self.__parsing_posts and attr_value[0] == "p" :
                    self.__parsing_online = True
                    self.__parsing_post_index = int(attr_value[1:])
                    self.__parsing_author_online = False
                    self.__parsing_publish_time = 0
                    self.__raw_html = self.__raw_html[string.find(self.__raw_html, "<div id=\"" + attr_value + "\""):]
                    self.__last_post_id = self.__parsing_post_index
        if self.__parsing_post_content :
            self.__parsing_content_div_stack += 1
            self.__parsing_content_div_count += 1
    def end_div(self) :
        phpbb_prompt.PromptParser.end_div(self)
        if self.__parsing_post_total_count :
            self.__parsing_post_total_count = False
        if self.__parsing_post_content :
            self.__parsing_content_div_stack -= 1
            if self.__parsing_content_div_stack <= 0 :
                self.__parsing_post_content = False
                self.__parsing_content_string = self.__raw_html[string.find(self.__raw_html, "<div class=\"content\">") + 21:]
                div_end_tag_start = 0
                for div_end_tag_index in range(self.__parsing_content_div_count) :
                    div_end_tag_start = self.__parsing_content_string.find("</div>", div_end_tag_start) + 1
                self.__parsing_content_string = self.__parsing_content_string[:div_end_tag_start - 1]
                self.__parsing_content_div_count = 0
                parser = phpbb_content.ContentParser()
                parser.feed(self.__parsing_content_string)
                self.posts.append((self.__last_post_id, self.__last_post_online, self.__last_post_subject, self.__last_post_author, self.__last_post_time, parser.contents))
                self.__last_post_id = 0
                self.__last_post_online = False
                self.__last_post_subject = ""
                self.__last_post_author = ""
                self.__last_post_time = 0
                return parser.contents
    def start_p(self, attrs) :
        phpbb_prompt.PromptParser.start_p(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "author" :
                self.__parsing_author_information = True
                self.__parsing_author_title = ""
    def end_p(self) :
        phpbb_prompt.PromptParser.end_p(self)
        if self.__parsing_author_information :
            self.__parsing_author_information = False
            self.__last_post_time = phpbb_time_string.parse(self.__parsing_time_string)
    def start_dl(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "postprofile" :
                self.__parsing_post_body = False
    def start_a(self, attrs) :
        if self.__parsing_post_subject :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" and ((string.find(attr_value, "viewtopic.php") >= 0) or (attr_value[0] == '#' and attr_value[1] == 'p')) :
                    self.__parsing_subject_text = True
                    self.__parsing_topic_title = ""
        elif self.__parsing_author_information :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" and (string.find(attr_value, "memberlist.php") >= 0) :
                    self.__parsing_post_author = True
        elif self.__parsing_topic :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" :
                    f_t_p_indexes_list = re.findall("f=(\d+)", attr_value)
                    for (id_index) in f_t_p_indexes_list :
                        self.forum_id = int(id_index)
                    f_t_p_indexes_list = re.findall("[^r]t=(\d+)", attr_value)
                    for (id_index) in f_t_p_indexes_list :
                        self.topic_id = int(id_index)
            self.__parsing_title = True
            self.__parsing_topic_title = ""
        elif not self.__parsing_posts :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" and (string.find(attr_value, "viewforum.php") >= 0) :
                    self.__parsing_forum = True
                    self.__parsing_topic_title = ""
    def end_a(self) :
        if self.__parsing_subject_text :
            self.__parsing_subject_text = False
        elif self.__parsing_post_author :
            self.__parsing_post_author = False
        elif self.__parsing_title :
            self.__parsing_title = False
        elif self.__parsing_forum :
            self.__parsing_forum = False
    def handle_data(self, data) :
        if not phpbb_prompt.PromptParser.handle_data(self, data) :
            if self.__parsing_author_information :
                self.__parsing_time_string = data
                self.__last_post_time = self.__parsing_time_string
            if self.__parsing_post_author :
                self.__parsing_author_title += cgi.escape(data)
                self.__last_post_author = self.__parsing_author_title
            elif self.__parsing_subject_text :
                self.__parsing_topic_title += cgi.escape(data)
                self.__last_post_subject = self.__parsing_topic_title
            elif self.__parsing_title :
                self.__parsing_topic_title += cgi.escape(data)
                self.topic_title = self.__parsing_topic_title
            elif self.__parsing_forum :
                self.__parsing_topic_title += cgi.escape(data)
                self.forum_title = self.__parsing_topic_title
            if self.__parsing_post_total_count :
                post_total_count_list = re.findall("\s+(\d+) ", data)
                for (count_number) in post_total_count_list :
                    self.post_total_count = int(count_number)

class SearchParser(SGMLParser, phpbb_prompt.PromptParser) :
    def __init__(self) :
        SGMLParser.__init__(self)
        phpbb_prompt.PromptParser.__init__(self)
        self.__parsing_search_result = False
        self.__parsing_post_body = False
        self.search_result = set()
    def start_div(self, attrs) :
        phpbb_prompt.PromptParser.start_div(self, attrs)
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" :
                if attr_value.find("search") >= 0 and (attr_value[attr_value.find("search") + 6] == ' ' or attr_value[attr_value.find("search") + 6] == '\"') :
                    self.__parsing_search_result = True
                elif self.__parsing_search_result and attr_value == "postbody" :
                    self.__parsing_post_body = True
    def end_div(self) :
        phpbb_prompt.PromptParser.end_div(self)
    def start_dl(self, attrs) :
        for (attr_name, attr_value) in attrs :
            if attr_name == "class" and attr_value == "postprofile" :
                self.__parsing_post_body = False
    def start_a(self, attrs) :
        if self.__parsing_post_body :
            for (attr_name, attr_value) in attrs :
                if attr_name == "href" and ((string.find(attr_value, "viewtopic.php") >= 0) or (attr_value[0] == '#' and attr_value[1] == 'p')) :
                    self.__parsing_subject_text = True
                    self.__parsing_topic_title = ""
                    if string.find(attr_value, "#p") >= 0 :
                        f_t_p_indexes_list = re.findall("[?&](?P<id_type>[ftp])=(?P<id_index>\d+)", attr_value)
                        f_t_p_indexes = { "f" : -1, "t" : -1, "p" : -1 }
                        for (id_type, id_index) in f_t_p_indexes_list :
                            f_t_p_indexes[id_type] = int(id_index)
                        if "p" in f_t_p_indexes :
                            self.search_result.add("p=%d" % int(f_t_p_indexes["p"]))
                        elif "t" in f_t_p_indexes :
                            self.search_result.add("t=%d" % int(f_t_p_indexes["t"]))
                        elif "f" in f_t_p_indexes :
                            self.search_result.add("f=%d" % int(f_t_p_indexes["f"]))
    def handle_data(self, data) :
        phpbb_prompt.PromptParser.handle_data(self, data)
