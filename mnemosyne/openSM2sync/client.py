#
# client.py - Max Usachev <maxusachev@gmail.com>
#             Ed Bartosh <bartosh@gmail.com>
#             Peter Bienstman <Peter.Bienstman@UGent.be>
#

import os
import socket
import tarfile
import httplib
from xml.etree import cElementTree

from partner import Partner
from text_formats.xml_format import XMLFormat
from utils import tar_file_size, traceback_string, SyncError

socket.setdefaulttimeout(60)

# Avoid delays caused by Nagle's algorithm.
# http://www.cmlenz.net/archives/2008/03/python-httplib-performance-problems

realsocket = socket.socket
def socketwrap(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
    sockobj = realsocket(family, type, proto)
    sockobj.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sockobj
socket.socket = socketwrap

# Buffer the response socket.
# http://mail.python.org/pipermail/python-bugs-list/2006-September/035156.html
# Fix included here for systems running Python 2.5.

class HTTPResponse(httplib.HTTPResponse):
    
    def __init__(self, sock, **kw):
        httplib.HTTPResponse.__init__(self, sock, **kw)
        self.fp = sock.makefile("rb") # Was unbuffered: sock.makefile("rb", 0)

httplib.HTTPConnection.response_class = HTTPResponse

# Register binary formats.

from binary_formats.mnemosyne_format import MnemosyneFormat
BinaryFormats = [MnemosyneFormat]


class Client(Partner):
    
    program_name = "unknown-SRS-app"
    program_version = "unknown"
    BUFFER_SIZE = 8192
    # The capabilities supported by the client. Note that we assume that the
    # server supports "mnemosyne_dynamic_cards".
    capabilities = "mnemosyne_dynamic_cards"  # "facts", "cards"
    # The following setting can be set to False to speed up the syncing
    # process on e.g. mobile clients where the media files don't get edited
    # externally.
    check_for_edited_local_media_files = True
    # Setting the following to False will speed up the initial sync, but in that
    # case the client will not have access to all of the review history in order
    # to e.g. display statistics. Also, it will not be possible to keep the
    # local database when there are sync conflicts. If a client makes it
    # possible for the user to change this value, doing so should result in
    # redownloading the entire database from scratch.
    interested_in_old_reps = True
    # Store prerendered question, answer and tag fields in database. The only
    # benefit of this is fast operation for a 'browse cards' dialog which
    # directly operates at the SQL level. If you don't use this, set to False
    # to reduce the database size.
    store_pregenerated_data = True
    # On mobile clients with slow SD cards copying a large database for the
    # backup before sync can take longer than the sync itself, so we offer
    # reckless users the possibility to skip this.
    do_backup = True
    # Setting this to False will leave all the uploading of anonymous science
    # logs to the sync server. Recommended to set this to False for mobile
    # clients, which are not always guaranteed to have an internet connection.
    upload_science_logs = True
    
    def __init__(self, machine_id, database, ui):
        Partner.__init__(self, ui)
        self.machine_id = machine_id
        self.database = database
        self.text_format = XMLFormat()
        self.server_info = {}
        self.con = None
        self.behind_proxy = None  # Explicit variable for testability.
        
    def request_connection(self):

        """If we are not behind a proxy, create the connection once and reuse
        it for all requests. If we are behind a proxy, we need to revert to
        HTTP 1.0 and use a separate connection for each request.
        
        """

        if self.behind_proxy is None:
            # TODO: determine automatically
            self.behind_proxy = False
        if self.behind_proxy:
            httplib.HTTPConnection._http_vsn = 10
            httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'
        else:
            httplib.HTTPConnection._http_vsn = 11
            httplib.HTTPConnection._http_vsn_str = 'HTTP/1.1'            
        if self.behind_proxy or (not self.behind_proxy and not self.con):
            self.con = httplib.HTTPConnection(self.server, self.port)

    def sync(self, server, port, username, password):
        try:
            self.server = socket.gethostbyname(server)
            self.port = port           
            if self.do_backup:
                self.ui.set_progress_text("Creating backup...") 
                backup_file = self.database.backup()
            # We check if files were edited outside of the program. This can
            # generate EDITED_MEDIA_FILES log entries, so it should be done
            # first. 
            if self.check_for_edited_local_media_files:
                self.ui.set_progress_text("Checking for edited media files...")
                self.database.check_for_edited_media_files()
            self.login(username, password)
            # First sync.
            if self.database.is_empty():
                self.get_server_media_files()
                if self.server_info["supports_binary_transfer"]:
                    self.get_server_entire_database_binary()
                else:
                    self.get_server_entire_database()
                self.get_sync_finish()
            else:
                # Upload local changes and check for conflicts.
                result = self.put_client_log_entries()            
                # No conflicts.
                if result == "OK":
                    self.put_client_media_files()
                    self.get_server_media_files()
                    self.get_server_log_entries()
                    self.get_sync_finish()
                # Conflicts, keep remote.
                elif result == "KEEP_REMOTE":
                    self.get_server_media_files(redownload_all=True)                
                    if self.server_info["supports_binary_transfer"]:
                        self.get_server_entire_database_binary()
                    else:
                        self.get_server_entire_database()
                    self.get_sync_finish()
                # Conflicts, keep local. Only becomes a valid option when
                # binary transfer is possible too. All the conditions are
                # checked in 'put_client_log_entries'.
                elif result == "KEEP_LOCAL":
                    self.put_client_media_files(reupload_all=True) 
                    self.put_client_entire_database_binary()
                    self.get_sync_finish()
                # Conflict, cancel.
                elif result == "CANCEL":
                    self.get_sync_cancel()
        except Exception, exception:
            self.ui.close_progress()
            if type(exception) == type(socket.gaierror()):
                self.ui.show_error("Could not find server!") 
            elif type(exception) == type(socket.error()):
                self.ui.show_error("Could not connect to server!")            
            elif type(exception) == type(socket.timeout()):
                self.ui.show_error("Timeout while waiting for server!")
            elif type(exception) == type(SyncError()):
                self.ui.show_error(str(exception))
            else:
                self.ui.show_error(traceback_string())
            if self.do_backup:
                self.database.restore(backup_file)
        finally:
            self.con.close()
            self.ui.close_progress()
            self.ui.show_information("Sync finished!")

    def _check_response_for_errors(self):
        response = self.con.getresponse().read()
        message, traceback = self.text_format.parse_message(response)        
        if "server error" in message.lower():
            raise SyncError(message)
        # We don't scare the client user with server log traces here, those
        # should have already been logged at the server side.

    def login(self, username, password):
        self.ui.set_progress_text("Logging in...")
        client_info = {}
        client_info["username"] = username
        client_info["password"] = password
        client_info["user_id"] = self.database.user_id()
        client_info["machine_id"] = self.machine_id
        client_info["program_name"] = self.program_name
        client_info["program_version"] = self.program_version
        client_info["database_name"] = self.database.name()
        client_info["database_version"] = self.database.version
        client_info["capabilities"] = self.capabilities
        client_info["partners"] = self.database.partners()
        client_info["interested_in_old_reps"] = self.interested_in_old_reps
        client_info["store_pregenerated_data"] = self.store_pregenerated_data
        client_info["upload_science_logs"] = self.upload_science_logs     
        # Signal if the database is empty, so that the server does not give a
        # spurious sync cycle warning if the client database was reset.
        client_info["database_is_empty"] = self.database.is_empty()
        # Not yet implemented: preferred renderer.
        client_info["render_chain"] = ""
        # Add optional program-specific information.
        client_info = self.database.append_to_sync_partner_info(client_info)
        self.request_connection()
        self.con.request("PUT", "/login",
            self.text_format.repr_partner_info(client_info).\
            encode("utf-8") + "\n")
        response = self.con.getresponse().read()
        if "message" in response:
            message, traceback = self.text_format.parse_message(response)
            message = message.lower()
            if "server error" in message:
                raise SyncError("Logging in: server error.")
            if "access denied" in message:
                raise SyncError("Wrong username or password.")
            if "cycle" in message:
                raise SyncError(\
                    "Sync cycle detected. Sync through intermediate partner.")         
        self.server_info = self.text_format.parse_partner_info(response)
        self.database.set_sync_partner_info(self.server_info)
        if self.database.is_empty():
            self.database.set_user_id(self.server_info["user_id"])
        elif self.server_info["user_id"] != client_info["user_id"]:
            raise SyncError("Error: mismatched user ids.\n" + \
                "The first sync should happen on an empty database.")
        self.database.create_if_needed_partnership_with(\
            self.server_info["machine_id"])
        self.database.merge_partners(self.server_info["partners"])
        
    def put_client_log_entries(self):
        number_of_entries = self.database.number_of_log_entries_to_sync_for(\
            self.server_info["machine_id"])
        if number_of_entries == 0:
            return
        self.ui.set_progress_text("Sending log entries...")
        self.ui.set_progress_range(0, number_of_entries)
        self.ui.set_progress_update_interval(number_of_entries/50)
        buffer = ""
        count = 0
        for log_entry in self.database.log_entries_to_sync_for(\
                self.server_info["machine_id"]):
            buffer += self.text_format.repr_log_entry(log_entry)
            count += 1
            self.ui.set_progress_value(count)
            if len(buffer) > self.BUFFER_SIZE or count == number_of_entries:
                buffer = \
                    self.text_format.log_entries_header(number_of_entries) \
                    + buffer + self.text_format.log_entries_footer()
                self.request_connection()
                self.con.request("PUT", "/client_log_entries?session_token=%s" \
                    % (self.server_info["session_token"],),
                    buffer.encode("utf-8"))
                buffer = ""
                response = self.con.getresponse().read()
                message, traceback = self.text_format.parse_message(response)        
                message = message.lower()     
        if "server error" in message:
            raise SyncError(message)
        if "conflict" in message:
            if self.capabilities == "mnemosyne_dynamic_cards" and \
               self.interested_in_old_reps and self.store_pregenerated_data \
               and self.program_name == self.server_info["program_name"] and \
               self.program_version == self.server_info["program_version"]:
                result = self.ui.show_question(\
                    "Conflicts detected during sync!",
                    "Keep local version", "Fetch remote version", "Cancel")
                results = {0: "KEEP_LOCAL", 1: "KEEP_REMOTE", 2: "CANCEL"}
                return results[result]
            else:
                result = self.ui.show_question(\
                    "Conflicts detected during sync! Your client only " +\
                    "stores part of the server database, so you can only " +\
                    "fetch the remote version.",
                    "Fetch remote version", "Cancel", "")
                results = {0: "KEEP_REMOTE", 1: "CANCEL"}
                return results[result]
        return "OK"

    def put_client_entire_database_binary(self):
        self.ui.set_progress_text("Sending entire binary database...")
        for BinaryFormat in BinaryFormats:
            binary_format = BinaryFormat(self.database)
            if binary_format.supports(self.server_info["program_name"],
                self.server_info["program_version"],
                self.server_info["database_version"]):
                assert self.store_pregenerated_data == True
                assert self.interested_in_old_reps == True
                binary_file, file_size = binary_format.binary_file_and_size(\
                    self.store_pregenerated_data, self.interested_in_old_reps)
                break
        self.request_connection()
        self.con.putrequest("PUT",
                "/client_entire_database_binary?session_token=%s" \
                % (self.server_info["session_token"], ))
        self.con.putheader("content-length", file_size)
        self.con.endheaders()   
        for buffer in self.stream_binary_file(binary_file, file_size):
            self.con.send(buffer)
        binary_format.clean_up()
        self._check_response_for_errors()
        
    def get_server_log_entries(self):
        self.ui.set_progress_text("Getting log entries...")
        if self.upload_science_logs:
            self.database.dump_to_science_log()
        self.request_connection()
        self.con.request("GET", "/server_log_entries?session_token=%s" \
            % (self.server_info["session_token"], ))
        def callback(context, log_entry):
            context.database.apply_log_entry(log_entry)
        self.download_log_entries(self.con.getresponse(), callback,
            context=self)   
        # The server will always upload the science logs of the log events
        # which originated at the server side.
        self.database.skip_science_log()
        
    def get_server_entire_database(self):
        self.ui.set_progress_text("Getting entire database...")
        filename = self.database.path()
        # Create a new database. Note that this also resets the
        # partnerships, as required.
        self.database.new(filename)
        self.request_connection()
        self.con.request("GET", "/server_entire_database?" + \
            "session_token=%s" % (self.server_info["session_token"], ))
        def callback(context, log_entry):
            context.database.apply_log_entry(log_entry)
        self.download_log_entries(self.con.getresponse(), callback,
            context=self)            
        self.database.load(filename)
        # The server will always upload the science logs of the log events
        # which originated at the server side.
        self.database.skip_science_log()
        # Since we start from a new database, we need to create the
        # partnership again.
        self.database.create_if_needed_partnership_with(\
            self.server_info["machine_id"])
        
    def get_server_entire_database_binary(self):
        self.ui.set_progress_text("Getting entire binary database...")
        filename = self.database.path()
        self.database.abandon()
        self.request_connection()
        self.con.request("GET", "/server_entire_database_binary?" + \
            "session_token=%s" % (self.server_info["session_token"], ))
        response = self.con.getresponse()
        size = int(response.getheader("mnemosyne-content-length"))
        self.download_binary_file(filename, response, size)
        self.database.load(filename)
        self.database.create_if_needed_partnership_with(\
            self.server_info["machine_id"])
        self.database.remove_partnership_with(self.machine_id)
        
    def put_client_media_files(self, reupload_all=False):
        # Size of tar archive.
        if reupload_all:
            filenames = self.database.all_media_filenames()
        else:
            filenames = self.database.media_filenames_to_sync_for(\
                self.server_info["machine_id"])
        size = tar_file_size(self.database.media_dir(), filenames)
        if size == 0:
            return
        self.ui.set_progress_text("Sending media files...")
        self.request_connection()
        self.con.putrequest("PUT", "/client_media_files?session_token=%s" \
            % (self.server_info["session_token"], ))
        self.con.putheader("content-length", size)
        self.con.endheaders()     
        socket = self.con.sock.makefile("wb", bufsize=self.BUFFER_SIZE)
        # Bundle the media files in a single tar stream, and send it over a
        # buffered socket in order to save memory. Note that this is a short
        # cut for efficiency reasons and bypasses the routines in Partner, and
        # in fact even httplib.HTTPConnection.send.
        saved_path = os.getcwdu()
        os.chdir(self.database.media_dir())
        tar_pipe = tarfile.open(mode="w|",  # Open in streaming mode.
             format=tarfile.PAX_FORMAT, fileobj=socket)
        for filename in filenames:
            tar_pipe.add(filename)
        tar_pipe.close()
        os.chdir(saved_path)
        self._check_response_for_errors()

    def get_server_media_files(self, redownload_all=False):
        url = "/server_media_files?session_token=%s" \
            % (self.server_info["session_token"], )
        if redownload_all:
            url += "&redownload_all=1"
        self.request_connection()
        self.con.request("GET", url)
        response = self.con.getresponse()
        size = int(response.getheader("mnemosyne-content-length"))
        if size == 0:
            # Make sure to read the full message, even if it's empty,
            # since we reuse our connection.
            response.read()
            return
        self.ui.set_progress_text("Getting media files...")
        tar_pipe = tarfile.open(mode="r|", fileobj=response)
        # Work around http://bugs.python.org/issue7693.
        tar_pipe.extractall(self.database.media_dir().encode("utf-8"))

    def get_sync_cancel(self):
        self.ui.set_progress_text("Cancelling sync...")
        self.request_connection()
        self.con.request("GET", "/sync_cancel?session_token=%s" \
            % (self.server_info["session_token"], ),
            headers={"connection": "close"})
        self._check_response_for_errors()
                
    def get_sync_finish(self):
        self.ui.set_progress_text("Finishing sync...")
        self.request_connection()
        self.con.request("GET", "/sync_finish?session_token=%s" \
            % (self.server_info["session_token"], ),
            headers={"connection": "close"})
        self._check_response_for_errors()
        # Only update after we are sure there have been no errors.
        self.database.update_last_log_index_synced_for(\
            self.server_info["machine_id"])
