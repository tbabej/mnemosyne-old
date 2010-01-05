#
# server.py - Max Usachev <maxusachev@gmail.com>
#             Ed Bartosh <bartosh@gmail.com>
#             Peter Bienstman <Peter.Bienstman@UGent.be>

import os
import cgi
import base64
import select
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from utils import create_subdirs
from synchroniser import Synchroniser
from synchroniser import PROTOCOL_VERSION


class Server(WSGIServer):

    """Note that the current implementation of the server can only handle one
    sync request at the time. it is *NOT* yet suited to deploy in a multiuser
    context over the internet, as simultaneous requests from different users
    could get mixed up.

    """
    
    program_name = "unknown-SRS-app"
    program_version = "unknown"
    capabilities = None  # TODO: list possibilies.

    stop_after_sync = False # Setting this True is useful for the testsuite. 

    def __init__(self, host, port, ui):
        WSGIServer.__init__(self, (host, port), WSGIRequestHandler)
        self.set_app(self.wsgi_app)
        self.ui = ui
        self.synchroniser = Synchroniser()
        self.stopped = False
        self.logged_in = False
        self.id = "TODO"
        self.number_of_client_log_entries_to_sync = None

    def wsgi_app(self, environ, start_response):
        status, mime, method, args = self.get_method(environ)
        response_headers = [("Content-type", mime)]
        start_response(status, response_headers)
        if method:
            return getattr(self, method)(environ, **args)
        else:
            return status

    def serve_forever(self):
        self.ui.status_bar_message("Waiting for client connection...")
        timeout = 1
        while not self.stopped:
            if select.select([self.socket], [], [], timeout)[0]:
                self.handle_request()
        self.socket.close()

    def stop(self):
        self.stopped = True

    def get_method(self, environ):

        """Checks for method existence in service and checks for right request
        params.

        """

        def compare_args(list1, list2):
            
            """Compares two lists or tuples."""
            
            for item in list1:
                if not item in list2:
                    return False
            return True

        if environ.has_key("HTTP_AUTHORIZATION"):
            login, password = base64.decodestring(\
                environ["HTTP_AUTHORIZATION"].split(" ")[-1]).split(":")
            if self.authorise(login, password):
                self.logged_in = True
                status = "200 OK"
            else:
                self.logged_in = False
                status = "403 Forbidden"
            return status, "text/plain", None, None
        else:
            if not self.logged_in:
                return "403 Forbidden", "text/plain", None, None
            method = (environ["REQUEST_METHOD"] + \
                "_".join(environ["PATH_INFO"].split("/"))).lower()
            if hasattr(self, method) and callable(getattr(self, method)):
                args = cgi.parse_qs(environ["QUERY_STRING"])
                args = dict([(key, val[0]) for key, val in args.iteritems()])
                if getattr(self, method).func_code.co_argcount-2 == len(args) \
                    and compare_args(args.keys(), getattr(self, method). \
                        func_code.co_varnames):                
                    return "200 OK", "xml/text", method, args
                else:
                    return "400 Bad Request", "text/plain", None, None
            else:
                return "404 Not Found", "text/plain", None, None

    # The following functions are to be overridden by the actual server code,
    # to implement e.g. authorisation and storage.

    def authorise(self, login, password):

        """Returns true if password correct for login."""

        raise NotImplementedError

    def open_database(self, database_name):

        """Sets self.database to a database object for the database named
        'database_name'.

        """

        raise NotImplementedError

    # The following are methods that are supported by the server through GET
    # and PUT calls. 'get_foo_bar' gets executed after a 'GET /foo/bar'
    # request. Similarly, 'put_foo_bar' gets executed after a 'PUT /foo/bar'
    # request.

    def get_server_params(self, environ):
        self.ui.status_bar_message("Sending server info to the client...")
        return ("<server id='%s' program_name='%s' " + \
            "program_version='%s' protocol_version='%s' capabilities='%s' " + \
            "server_deck_read_only='false' " + \
            "server_allows_media_upload='true'></server>") % (self.id,
            self.program_name, self.program_version, PROTOCOL_VERSION,
            self.capabilities)        

    def put_client_params(self, environ):
        self.ui.status_bar_message("Receiving client info...")
        try:
            socket = environ["wsgi.input"]
            client_params = socket.readline()
        except:
            return "CANCEL"
        self.synchroniser.set_partner_params(client_params)
        self.client_id = self.synchroniser.partner["id"]
        self.open_database(self.synchroniser.partner["database_name"])
        self.database.backup()
        self.synchroniser.database = self.database
        self.database.create_partnership_if_needed_for(self.client_id)
        return "OK"
        
    def put_number_of_client_log_entries_to_sync(self, environ):
        try:
            socket = environ["wsgi.input"]
            self.number_of_client_log_entries_to_sync = int(socket.readline())
        except:
            return "CANCEL"
        else:
            return "OK"
        
    def put_number_of_client_media_files_to_sync(self, environ):
        try:
            socket = environ["wsgi.input"]
            self.number_of_client_media_files_to_sync = int(socket.readline())
        except:
            return "CANCEL"
        else:
            return "OK
            "
    def get_number_of_server_media_files_to_sync(self, environ):
        return str(self.database.number_of_media_files_to_sync_for(self.client_id))
    
    def get_number_of_server_log_entries_to_sync(self, environ):
        return str(self.database.number_of_log_entries_to_sync_for(self.client_id))

    def get_server_log_entries(self, environ):
        self.ui.status_bar_message("Sending log entries to client...")
        log_entries = self.database.number_of_log_entries_to_sync_for(\
            self.client_id)
        progress_dialog = self.ui.get_progress_dialog()
        progress_dialog.set_range(0, log_entries)
        progress_dialog.set_text("Sending log entries to client...")      
        count = 0
        for log_entry in self.database.log_entries_to_sync_for(\
            self.client_id):
            count += 1
            progress_dialog.set_value(count)
            yield self.synchroniser.log_entry_to_XML(log_entry) + "\r\n"

    def put_client_log_entries(self, environ):
        socket = environ["wsgi.input"]
        self.ui.status_bar_message("Applying client log entries...")
        progress_dialog = self.ui.get_progress_dialog()
        progress_dialog.set_range(0, self.number_of_client_log_entries_to_sync)
        progress_dialog.set_text("Applying client log entries...")
        # In order to do conflict resolution easily, one of the sync partners
        # has to have both logs in memory. We do this at the server side, as
        # the client could be resource-limited mobile device.
        self.client_log = []
        count = 0
        while count != self.number_of_client_log_entries_to_sync:
            chunk = socket.readline()
            self.client_log.append(self.synchroniser.XML_to_log_entry(chunk))
            count += 1
            progress_dialog.set_value(count)
        self.ui.status_bar_message("Waiting for client to finish...")
        return "OK"

    def get_server_media_file(self, environ, filename):
        self.ui.status_bar_message("Sending media file to client...")
        try:
            return file(os.path.join(self.database.mediadir(),
                filename)).read()
        except IOError:
            return "CANCEL"

    def put_client_media_file(self, environ, filename):
        self.ui.status_bar_message("Receiving client media file...")
        try:
            socket = environ["wsgi.input"]
            size = int(environ["CONTENT_LENGTH"])
            data = socket.read(size)
        except:
            return "CANCEL"
        create_subdirs(self.database.mediadir(), filename)     
        file(os.path.join(self.database.mediadir(), filename), "wb").\
            write(data)
        return "OK"

    def get_sync_finish(self, environ):
        self.ui.status_bar_message("Waiting for client to finish...")
        for log_entry in self.client_log:
            self.database.apply_log_entry(log_entry)
        self.database.update_last_sync_log_entry_for(self.client_id)
        self.logged_in = False
        if self.stop_after_sync:
            self.stop()
        return "OK"
