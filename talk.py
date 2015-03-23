import sys
import os
import re
import thread
import time
import uuid
import tempfile
from StringIO import StringIO
import urlparse
import pycurl
import http_response_header
import phpbb_login
import phpbb_prompt
import phpbb_profile
import phpbb_messages
import phpbb_post

lock = thread.allocate_lock()

class Talk :
    def __init__(self) :
        self.__root_url = ''
        self.__protocol = ''
        self.__logined = False
        self.__curl = None
        self.__phpbb3_cookie = ''
        self.__phpbb3_ucookie_value = ''
        self.__phpbb3_kcookie_value = ''
        self.__phpbb3_sidcookie_value = ''
        self.__last_resource_id = ''
        self.__last_selected_forum = -1
        self.__last_forum = -1
        self.__last_forum_title = ''
        self.__last_topic = -1
        self.__last_topic_title = ''
        self.__last_post_start = 0
        self.__last_post_total_count = 1
        self.__creation_time = ''
        self.__form_token = ''

    def set_root_url(self, url) :
        if url.find(':') < 0 :
            return (-1, "Invalid url")
        self.__protocol = url[:url.index(':')]
        if url[-1] == '/' :
            self.__root_url = url[:-1]
        else :
            self.__root_url = url
        return True

    def __del__(self) :
        if self.__curl :
            self.__logined = False
            self.__curl.close()

    def __cookie_reader(self, cookies) :
        for (cookie_name, cookie_value) in cookies :
            if re.match("phpbb3_.*_u", cookie_name) :
                self.__phpbb3_cookie = cookie_name[:-2]
                self.__phpbb3_ucookie_value = cookie_value
            if re.match("phpbb3_.*_k", cookie_name) :
                self.__phpbb3_cookie = cookie_name[:-2]
                self.__phpbb3_kcookie_value = cookie_value
            if re.match("phpbb3_.*_sid", cookie_name) :
                self.__phpbb3_cookie = cookie_name[:-4]
                self.__phpbb3_sidcookie_value = cookie_value

    def __extract_f_t_p_indexes(self, resource_id) :
        if resource_id[:len(self.__root_url)] == self.__root_url :
            resource_id = resource_id[len(self.__root_url) + 1:]
        elif re.match("^https?:\/\/www\.[A-Za-z0-9-]+\.[A-Za-z.]+$", self.__root_url) :
            root_url_list = re.findall("^(?P<protocol>https?):\/\/www\.(?P<domain>[A-Za-z0-9-]+)\.(?P<top_level>[A-Za-z.]+)$", self.__root_url)
            root_url = root_url_list[0][0] + "://" + root_url_list[0][1] + "." + root_url_list[0][2]
            if resource_id[:len(root_url)] == root_url :
                resource_id = resource_id[len(root_url) + 1:]
        valid_resource_id = "(view(forum|topic).php\?)?(f=\d+|t=\d+|p=\d+)"
        if re.match(valid_resource_id, resource_id) :
            f_t_p_indexes_list = re.findall("[&?](?P<id_type>[ftp])=(?P<id_index>\d+)", "&" + resource_id)
            f_t_p_indexes = { "f" : -1, "t" : -1, "p" : -1 }
            for (id_type, id_index) in f_t_p_indexes_list :
                f_t_p_indexes[id_type] = int(id_index)
            if re.match(".*#p\d+", resource_id) :
                f_t_p_indexes_list = re.findall("#p(\d+)", resource_id)
                for id_index in f_t_p_indexes_list :
                    f_t_p_indexes["p"] = int(id_index)
            return f_t_p_indexes
        else :
            raise Exception("Invalid resource id")

    def __perform_url(self, url) :
        io_buffer = StringIO()
        self.__curl.setopt(pycurl.URL, url)
        self.__curl.setopt(pycurl.WRITEFUNCTION, io_buffer.write)
        self.__curl.setopt(pycurl.CONNECTTIMEOUT, 120)
        self.__curl.perform()
        return io_buffer

    def __create_orca_messages(self, posts) :
        orca_messages = []
        for post in posts :
            (post_id, post_online, post_subject, post_author, post_time, contents) = post
            orca_message_exist = False
            for (content_type, content_text, content_url) in contents :
                if content_type == 1 :
                    orca_message_exist = True
                    break
            if orca_message_exist :
                orca_messages += [("p=" + str(post_id), content_url)]
                continue
            post_url = '%s/viewtopic.php?p=%d' % (self.__root_url, post_id)
            orca_message = "<orcamessage id=\"" + post_url + "\"" + " subject=\"" + post_subject + "\"" + \
                " author=\"" + post_author + "\"" + " online=\"" + str(post_online).lower() + "\"" + \
                " time=\"" + str(post_time) + "\">"
            message_images = "<images>"
            message_body = "<body><f>0 0 -1</f>"
            images = {}
            for (content_type, content_text, content_url) in contents :
                if content_type == 0 :
                    message_body += content_text
                elif content_type == 2 :
                    if content_url not in images :
                        image_id_list = re.findall("[;|\?]id=(\d*)", content_url)
                        if image_id_list :
                            image_url = '%s/download/file.php?mode=view&id=%s' % (self.__root_url, image_id_list[0])
                            images[content_url] = str(uuid.uuid3(uuid.NAMESPACE_URL, image_url))
                        else :
                            images[content_url] = str(uuid.uuid1())
                        message_images += "<image id=\"pic:{" + images[content_url] + "}\"" + \
                            " url=\"" + content_url + "\"/>"
                    message_body += "<a>pic:{" + str(images[content_url]) + "}</a>"
            message_images += "</images>"
            message_body += "<f></f></body>"
            if images :
                orca_message += message_images
            orca_message += message_body
            orca_message += "</orcamessage>"
            orca_messages += [("p=" + str(post_id), orca_message)]
        return orca_messages

    def __recv_messages(self, resource_id, load_all, need_lock) :
        if load_all and self.__last_resource_id != resource_id :
            self.__last_post_start = 0
            self.__last_post_total_count = 1
            self.__last_resource_id = resource_id
        resource_list = re.findall("&start=(?P<start>\d+)", resource_id)
        for start in resource_list :
            self.__last_post_start = start
        f_t_p_indexes = self.__extract_f_t_p_indexes(resource_id)
        if f_t_p_indexes :
            try :
                if need_lock :
                    lock.acquire()
                if not self.__curl :
                    self.__curl = pycurl.Curl()
                if need_lock :
                    lock.release()
                resource_id = ''
                url = ''
                if f_t_p_indexes["p"] > 0 :
                    resource_id = 'p=%d' % f_t_p_indexes["p"]
                    url = '%s/viewtopic.php?p=%d' % (self.__root_url, f_t_p_indexes["p"])
                    if load_all :
                        if need_lock :
                            lock.acquire()
                        self.__curl.setopt(pycurl.HEADER, 0)
                        io_buffer = self.__perform_url(url)
                        if need_lock :
                            lock.release()
                        parser = phpbb_messages.TopicParser()
                        parser.feed(io_buffer.getvalue())
                        if parser.prompt_message_text :
                            raise Exception(parser.prompt_message_text)
                        url = '%s/viewtopic.php?t=%d' % (self.__root_url, parser.topic_id)
                elif f_t_p_indexes["t"] > 0 :
                    resource_id = 't=%d' % f_t_p_indexes["t"]
                    url = '%s/viewtopic.php?t=%d' % (self.__root_url, f_t_p_indexes["t"])
                elif f_t_p_indexes["f"] > 0 :
                    resource_id = 'f=%d' % f_t_p_indexes["f"]
                    url = '%s/viewforum.php?f=%d' % (self.__root_url, f_t_p_indexes["f"])
                    if need_lock :
                        lock.acquire()
                    self.__curl.setopt(pycurl.HEADER, 0)
                    io_buffer = self.__perform_url(url)
                    if need_lock :
                        lock.release()
                    parser = phpbb_messages.ForumParser()
                    parser.feed(io_buffer.getvalue())
                    if parser.prompt_message_text :
                        self.__last_forum = f_t_p_indexes["f"]
                        self.__last_forum_title = ""
                        self.__last_topic = -1
                        self.__last_topic_title = ""
                        raise Exception(parser.prompt_message_text)
                    if load_all :
                        self.__last_forum, self.__last_forum_title = parser.forum
                        self.__last_topic = -1
                        self.__last_topic_title = ""
                        selected_forum = "Forum %d(%s) selected" % (self.__last_forum, self.__last_forum_title)
                        self.__last_selected_forum = self.__last_forum
                        self.__last_post_start = 0
                        self.__last_post_total_count = 1
                        self.__last_resource_id = ""
                        return (0, { "send_text" : "NewTopic", "send_tooltip" : "Post a new topic",
                                     "resource_id" : resource_id, "prompt_text" : selected_forum })
                    orca_messages = {}
                    first_topic_id = False
                    for topic in parser.topics :
                        (topic_id, topic_type, topic_title) = topic
                        first_topic_id = int(topic_id)
                        break
                    if not first_topic_id :
                        raise Exception("No topic in the forum")
                    url = '%s/viewtopic.php?t=%d' % (self.__root_url, first_topic_id)
                if url :
                    orca_messages = []
                    orca_message_count = 0
                    while True :
                        if load_all :
                            if self.__last_post_start >= self.__last_post_total_count :
                                selected_forum = ""
                                if self.__last_selected_forum != self.__last_forum :
                                    selected_forum = "Forum %d(%s) selected" % (self.__last_forum, self.__last_forum_title)
                                    self.__last_selected_forum = self.__last_forum
                                self.__last_post_start = 0
                                self.__last_post_total_count = 1
                                self.__last_resource_id = ""
                                return (0, { "send_text" : "PostReply", "send_tooltip" : "Post a reply",
                                             "resource_id" : resource_id, "prompt_text" : selected_forum })
                            page_url = '%s&start=%d' % (url, self.__last_post_start)
                        else :
                            page_url = url
                        self.__last_forum = -1
                        self.__last_forum_title = ""
                        self.__last_topic = -1
                        self.__last_topic_title = ""
                        if need_lock :
                            lock.acquire()
                        self.__curl.setopt(pycurl.HEADER, 0)
                        io_buffer = self.__perform_url(page_url)
                        if need_lock :
                            lock.release()
                        parser = phpbb_messages.TopicParser()
                        parser.feed(io_buffer.getvalue())
                        if parser.prompt_message_text :
                            raise Exception(parser.prompt_message_text)
                        if load_all :
                            self.__last_post_total_count = parser.post_total_count
                            self.__last_forum = parser.forum_id
                            self.__last_forum_title = parser.forum_title
                            self.__last_topic = parser.topic_id
                            self.__last_topic_title = parser.topic_title
                        page_orca_messages = self.__create_orca_messages(parser.posts)
                        have_resource_messages = []
                        for message_index in xrange(0, len(page_orca_messages)) :
                            message_id, message_or_url = page_orca_messages[message_index]
                            if message_or_url[:5] == "orca:" :
                                message_or_url = self.__protocol + message_or_url[4:]
                            if len(message_or_url) > len(self.__root_url) and message_or_url[:len(self.__root_url)] == self.__root_url :
                                lock.acquire()
                                io_buffer = self.__perform_url(message_or_url)
                                lock.release()
                                parser = phpbb_prompt.PromptParser()
                                parser.feed(io_buffer.getvalue())
                                if parser.prompt_message_text :
                                    raise Exception(parser.prompt_message_text)
                                page_orca_messages[message_index] = message_id, io_buffer.getvalue()
                                have_resource_messages += (message_id, )
                        if not load_all :
                            if f_t_p_indexes["p"] <= 0 : # p=n
                                if have_resource_messages :
                                    resource_id = have_resource_messages[0]
                            message = ''
                            if resource_id in have_resource_messages :
                                for message_id, message_or_url in page_orca_messages :
                                    if resource_id == message_id :
                                        message = message_or_url
                            if not message :
                                raise Exception("Invalid resource id")
                            orca_messages += [(resource_id, message)]
                            break
                        self.__last_post_start += len(page_orca_messages)
                        orca_messages += page_orca_messages
                        break
                    return orca_messages
            except pycurl.error, e :
                error_number, error_string = e
                return (-1, { "prompt_text" : error_string })
            except Exception, e :
                error_string = str(e)
                return (-1, { "prompt_text" : error_string })

    def __create_attachment_file(self, attachment_id, attachment_ext, attachment_data) :
        attachment_file = False
        try :
            if not attachment_ext or attachment_ext[0] != '.' :
                return False
            attachment_file_name = attachment_id + attachment_ext
            attachment_file_name = attachment_file_name.replace(':', '_')
            attachment_file_path = os.path.join(tempfile.gettempdir(), attachment_file_name)
            attachment_file = open(attachment_file_path, "w+b")
            attachment_file.write(attachment_data)
            return attachment_file_path
        finally :
            if attachment_file :
                attachment_file.close()

    def __add_file(self, forum, creation_time, form_token, file_path, file_ext) :
        try :
            lock.acquire()
            if not self.__curl :
                self.__curl = pycurl.Curl()
            lock.release()
            url = '%s/posting.php?f=%d&mode=post' % (self.__root_url, forum)
            lock.acquire()
            content_type = "text/plain"
            if file_ext == ".jpg" or file_ext == ".jpeg" :
                content_type = "image/jpeg"
            elif file_ext == ".gif" :
                content_type = "image/gif"
            elif file_ext == ".png" :
                content_type = "image/png"
            elif file_ext == ".tif" or file_ext == ".tiff" :
                content_type = "image/tiff"
            elif file_ext == ".gtm" or file_ext == ".orm" :
                content_type = "application/gtalkabout"
            self.__curl.setopt(pycurl.HEADER, 0)
            self.__curl.setopt(pycurl.HTTPPOST, [("creation_time", (pycurl.FORM_CONTENTS, creation_time)), \
                ("form_token", (pycurl.FORM_CONTENTS, form_token)), \
                ("fileupload", (pycurl.FORM_FILE, file_path, pycurl.FORM_CONTENTTYPE, content_type)), \
                ("filecomment", (pycurl.FORM_CONTENTS, file_path)), \
                ("add_file", (pycurl.FORM_CONTENTS, "Add the file"))])
            io_buffer = self.__perform_url(url)
            lock.release()
            parser = phpbb_post.AddFileParser()
            parser.feed(io_buffer.getvalue())
            if parser.prompt_message_text :
                raise Exception(parser.prompt_message_text)
            return parser.file_id
        except pycurl.error, e :
            error_number, error_string = e
            return (-1, error_string)

    def __pre_post(self, forum, topic) :
        try :
            lock.acquire()
            if not self.__curl :
                self.__curl = pycurl.Curl()
            lock.release()
            if topic >= 0 and forum >= 0 :
                url = '%s/posting.php?f=%d&t=%d&mode=reply' % (self.__root_url, forum, topic)
            elif forum >= 0 :
                url = '%s/posting.php?f=%d&mode=post' % (self.__root_url, forum)
            else :
                raise Exception("Can't post without a forum selected")
            lock.acquire()
            self.__curl.setopt(pycurl.HEADER, 0)
            self.__curl.setopt(pycurl.POSTFIELDS, "")
            io_buffer = self.__perform_url(url)
            lock.release()
            parser = phpbb_post.PrePostParser()
            parser.feed(io_buffer.getvalue())
            if parser.prompt_message_text :
                raise Exception(parser.prompt_message_text)
            self.__creation_time = parser.creation_time
            self.__form_token = parser.form_token
        except pycurl.error, e :
            error_number, error_string = e
            return (-1, error_string)
        except Exception, e :
            error_string = str(e)
            return (-1, error_string)

    def login(self, username, password) :
        try :
            self.__curl = pycurl.Curl()
            url = '%s/ucp.php?mode=login' % self.__root_url
            post_fields = 'username=%s&password=%s&login=true' % (username, password)
#            lock.acquire()
            self.__curl.setopt(pycurl.HEADER, 1)
            self.__curl.setopt(pycurl.POSTFIELDS, post_fields)
            io_buffer = self.__perform_url(url)
#            lock.release()
            field_buffer = http_response_header.read(io_buffer.getvalue())
            html_buffer = http_response_header.fields(field_buffer, self.__cookie_reader)
            cookie_string = self.__phpbb3_cookie + "_u=" + self.__phpbb3_ucookie_value + "; " + self.__phpbb3_cookie + "_k=" + self.__phpbb3_kcookie_value + "; " + self.__phpbb3_cookie + "_sid=" + self.__phpbb3_sidcookie_value + "; style_cookie=printonly"
#            lock.acquire()
            self.__curl.setopt(pycurl.COOKIE, cookie_string)
#            lock.release()
            if http_response_header.http_status == 200 :
                parser = phpbb_login.LoginParser()
                parser.feed(io_buffer.getvalue())
                if not parser.login_status :
                    raise Exception(parser.error_message)
                self.__logined = True
                return 0
            raise Exception(str(http_response_header.http_status) + " : " + http_response_header.http_status_text)
        except pycurl.error, e :
            error_number, error_string = e
            self.__curl.close()
            self.__curl = None
            return (-1, error_string)
        except Exception, e :
            error_string = str(e)
            self.__curl.close()
            self.__curl = None
            return (-1, error_string)

    def logout(self) :
        if self.__logined and self.__curl and self.__phpbb3_sidcookie_value :
            try :
                url = '%s/ucp.php?mode=logout&sid=%s' % (self.__root_url, self.__phpbb3_sidcookie_value)
                lock.acquire()
                self.__curl.setopt(pycurl.HEADER, 0)
                self.__curl.setopt(pycurl.URL, url)
                self.__curl.setopt(pycurl.CONNECTTIMEOUT, 90)
                self.__curl.perform()
                lock.release()
            finally :
                self.__curl.close()
                self.__curl = None
                self.__logined = False
                self.__phpbb3_cookie = ''
                self.__phpbb3_ucookie_value = ''
                self.__phpbb3_kcookie_value = ''
                self.__phpbb3_sidcookie_value = ''

    def profile(self) :
        try :
            lock.acquire()
            if not self.__curl :
                self.__curl = pycurl.Curl()
            lock.release()
            url = '%s/ucp.php?i=profile&mode=reg_details' % self.__root_url
            lock.acquire()
            self.__curl.setopt(pycurl.HEADER, 0)
            io_buffer = self.__perform_url(url)
            lock.release()
            parser = phpbb_profile.DisplayNameParser()
            parser.feed(io_buffer.getvalue())
            if parser.prompt_message_text :
                raise Exception(parser.prompt_message_text)
            displayname = parser.displayname
            url = '%s/ucp.php?i=profile&mode=avatar' % self.__root_url
            lock.acquire()
            io_buffer = self.__perform_url(url)
            lock.release()
            parser = phpbb_profile.AvatarParser()
            parser.feed(io_buffer.getvalue())
            if parser.prompt_message_text :
                raise Exception(parser.prompt_message_text)
            avatar = parser.avatar
            url = urlparse.urljoin(self.__root_url, avatar)
            lock.acquire()
            io_buffer = self.__perform_url(url)
            lock.release()
            return { "displayname" : displayname, "avatar" : io_buffer.getvalue() }
        except pycurl.error, e :
            error_number, error_string = e
            return (-1, error_string)
        except Exception, e :
            error_string = str(e)
            return (-1, error_string)

    def load_resource(self, resource_id) :
        return self.__recv_messages(resource_id, False, False)

    def recv_messages(self, resource_id) :
        if not resource_id :
            self.__last_topic = -1
            self.__last_topic_title = ""
            self.__last_post_start = 0
            self.__last_selected_forum = self.__last_forum
            self.__last_post_total_count = 1
            self.__last_resource_id = ""
            if self.__last_forum < 0 :
                return (0, {  })
            selected_forum = "You'll post topics in Forum %d(%s)" % (self.__last_forum, self.__last_forum_title)
            return (0, { "send_text" : "NewTopic", "send_tooltip" : "Post a new topic",
                         "resource_id" : resource_id, "prompt_text" : selected_forum })
        return self.__recv_messages(resource_id, True, True)

    def send_attachments(self, attachments = {}) :
        try :
            lock.acquire()
            if not self.__curl :
                self.__curl = pycurl.Curl()
            lock.release()
            self.__creation_time = ""
            self.__form_token = ""
            self.__pre_post(self.__last_forum, self.__last_topic)
            time.sleep(1)
            attachment_urls = {}
            for attachment_id in attachments.keys() :
                attachment_data, attachment_ext = attachments[attachment_id]
                if attachment_id[:4] == "pic:" or attachment_id[:9] == "snapshot:" :
                    if attachment_ext :
                        attachment_file_path = self.__create_attachment_file(attachment_id, attachment_ext, attachment_data)
                        if not attachment_file_path :
                            raise Exception("Invalid attachment format")
                        file_id = self.__add_file(self.__last_forum, self.__creation_time, self.__form_token, attachment_file_path, attachment_ext)
                        file_url = '%s/download/file.php?id=%d' % (self.__root_url, file_id)
                    else :
                        file_url = attachment_data
                    attachment_urls[attachment_id] = file_url
            return attachment_urls
        except pycurl.error, e :
            error_number, error_string = e
            return (-1, error_string)
        except IOError, e :
            error_number, error_string = e
            return (-1, error_string)
        except Exception, e :
            error_string = str(e)
            return (-1, error_string)

    def send_message(self, subject, messages, attchments = {}) :
        try :
            lock.acquire()
            if not self.__curl :
                self.__curl = pycurl.Curl()
            lock.release()
            if not self.__creation_time or not self.__form_token :
                self.__pre_post(self.__last_forum, self.__last_topic)
                time.sleep(1)
            if not self.__creation_time or not self.__form_token :
                if not self.__logined :
                    raise Exception("Can't post the message, maybe you should login first")
                elif self.__last_forum < 0 :
                    raise Exception("Can't post without a forum selected")
                else :
                    raise Exception("Can't post the message")
            content = ""
            snapshot_file_url = ""
            for (message, type) in messages :
                if type == 0 :  # text
                    content += message
                elif type > 0 :
                    if message in attchments :
                        attachment_data, attachment_ext = attchments[message]
                        if attachment_ext :
                            attachment_file_path = self.__create_attachment_file(message, attachment_ext, attachment_data)
                            if not attachment_file_path :
                                raise Exception("Invalid attachment format")
                            file_id = self.__add_file(self.__last_forum, self.__creation_time, self.__form_token, attachment_file_path, attachment_ext)
                            file_url = '%s/download/file.php?id=%d' % (self.__root_url, file_id)
                        else :
                            file_url = attachment_data
                        if type == 1 :    # orca message
                            orca_id = str(uuid.uuid1())
                            content += "[quote=\"[url=https://www.gtalkabout.com]GTalkabout[/url]\"]"
                            orca_url = file_url
                            if file_url.find(':') >= 0 :
                                orca_url = "orca" + file_url[file_url.index(':'):]
                                orca_url += "%%26oid=%s" % orca_id
                            content += "Click to open by GTalkabout: [url=%s]" % orca_url
                            content += "%s[/url]\n" % orca_id
                            if snapshot_file_url :
                                content += "[url=%s][img]%s[/img][/url]" % (orca_url, snapshot_file_url)
                            content += "[/quote]"
                        elif type == 2 :  # image
                            content += "[img]"
                            content += file_url
                            content += "[/img]"
                        elif type == 3 :    # source code snapshot
                            snapshot_file_url = file_url
            post_fields = 'subject=%s&message=%s&creation_time=%s&form_token=%s&post=true' % (subject, content, self.__creation_time, self.__form_token)
            if self.__last_topic >= 0 and self.__last_forum >= 0 :
                url = '%s/posting.php?f=%d&t=%d&mode=reply' % (self.__root_url, self.__last_forum, self.__last_topic)
            elif self.__last_forum >= 0 :
                url = '%s/posting.php?f=%d&mode=post' % (self.__root_url, self.__last_forum)
            else :
                raise Exception("Can't post without a forum selected")
            lock.acquire()
            self.__curl.setopt(pycurl.POSTFIELDS, post_fields)
            io_buffer = self.__perform_url(url)
            lock.release()
            parser = phpbb_post.PostParser()
            parser.feed(io_buffer.getvalue())
            if parser.published_post >= 0 :
                return (0, { "resource_id" : 'p=%d' % parser.published_post })
            elif parser.published_topic >= 0 :
                self.__last_topic = parser.published_topic
                return (0, { "resource_id" : 't=%d' % parser.published_topic })
            elif parser.published_forum >= 0 :
                return (-2, { "prompt_text" : parser.prompt_message_text })
            elif parser.prompt_message_text :
                raise Exception(parser.prompt_message_text)
        except pycurl.error, e :
            error_number, error_string = e
            return (-1, { "prompt_text" : error_string })
        except IOError, e :
            error_number, error_string = e
            return (-1, { "prompt_text" : error_string })
        except Exception, e :
            error_string = str(e)
            return (-1, { "prompt_text" : error_string })

    def url_to_resource_id(self, url) :
        if url[:5] == "orca:" :
            if url.find("oid=") >= 0 :
                orca_id = url[url.find("oid=") + 4:]
                if orca_id.find("&") >= 0 :
                    orca_id = orca_id[:orca_id.find("&")]
                if orca_id.find("-") >= 0 :
                    keywords = orca_id[:orca_id.find("-")]
                if keywords :
                    url = '%s/search.php?keywords=%s' % (self.__root_url, keywords)
                    try :
                        lock.acquire()
                        if not self.__curl :
                            self.__curl = pycurl.Curl()
                        lock.release()
                        lock.acquire()
                        io_buffer = self.__perform_url(url)
                        lock.release()
                        parser = phpbb_messages.SearchParser()
                        parser.feed(io_buffer.getvalue())
                        if parser.prompt_message_text :
                            raise Exception(parser.prompt_message_text)
                        if not parser.search_result :
                            raise Exception("Can't find the resource")
                        for resource_id in parser.search_result :
                            return resource_id
                    except pycurl.error, e :
                        error_number, error_string = e
                        return (-1, error_string)
                    except Exception, e :
                        error_string = str(e)
                        return (-1, error_string)
