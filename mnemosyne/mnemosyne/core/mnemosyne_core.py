##############################################################################
#
# Mnemosyne core <Peter.Bienstman@UGent.be>
#
##############################################################################

import random, time, os, string, sys, cPickle, md5, struct, logging
import traceback, shutil
logger = logging.getLogger("mnemosyne")


##############################################################################
#
# Global variables
#
##############################################################################

time_of_start = None
import_time_of_start = None

thinking_time = 0
time_of_last_question = 0

upload_thread = None
load_failed = False

items = []
revision_queue = []

categories = []
category_by_name = {}

config = {}



##############################################################################
#
# initialise
#
##############################################################################

def initialise():

    import mnemosyne_log

    global upload_thread, load_failed

    load_failed = False

    join   = os.path.join
    exists = os.path.exists
    
    # Set default paths.

    basedir = os.path.join(os.path.expanduser("~"), ".mnemosyne")

    if not exists(basedir):
        os.mkdir(basedir)
    
    if not exists(join(basedir,"config")):
        init_config()
        save_config()    
     
    if not exists(join(basedir,"default.mem")):
        new_database(join(basedir,"default.mem"))
    
    if not exists(join(basedir,"history")):
        os.mkdir(join(basedir,"history"))

    if not exists(join(basedir,"latex")):
        os.mkdir(join(basedir,"latex"))

    lockfile = file(join(basedir,"MNEMOSYNE_LOCK"),'w')
    lockfile.close()

    load_config()

    mnemosyne_log.archive_old_log()
    
    mnemosyne_log.start_logging()

    if get_config("upload_logs") == True:
        upload_thread = mnemosyne_log.Uploader()
        upload_thread.start()

    import mnemosyne.version
    logger.info("Program started : Mnemosyne " + mnemosyne.version.version)



##############################################################################
#
# init_config
#
##############################################################################

def init_config():
    global config

    basedir = os.path.join(os.path.expanduser("~"), ".mnemosyne")
 
    if not config.has_key("first_run"):        
        config["first_run"] = True
    if not config.has_key("path"):
        config["path"] = os.path.join(basedir, "default.mem")
    if not config.has_key("import_dir"):        
        config["import_dir"] = basedir
    if not config.has_key("user_id"):                          
        config["user_id"] = md5.new(str(random.random())).hexdigest()[0:8]
    if not config.has_key("keep_logs"):              
        config["keep_logs"] = True
    if not config.has_key("upload_logs"):              
        config["upload_logs"] = True
    if not config.has_key("upload_server"):              
        config["upload_server"] = "mnemosyne-proj.dyndns.org:80"    
    if not config.has_key("log_index"):              
        config["log_index"] = 1
    if not config.has_key("hide_toolbar"):         
        config["hide_toolbar"] = False
    if not config.has_key("QA_font"):               
        config["QA_font"] = None
    if not config.has_key("list_font"):               
        config["list_font"] = None
    if not config.has_key("left_align"):        
        config["left_align"] = False
    if not config.has_key("check_duplicates_when_adding"):      
        config["check_duplicates_when_adding"] = True
    if not config.has_key("allow_duplicates_in_diff_cat"):     
        config["allow_duplicates_in_diff_cat"] = True
    if not config.has_key("grade_0_items_at_once"):
        config["grade_0_items_at_once"] = 5


##############################################################################
#
# get_config
#
##############################################################################

def get_config(key):
    return config[key]



##############################################################################
#
# set_config
#
##############################################################################

def set_config(key, value):
    global config
    config[key] = value



##############################################################################
#
# load_config
#
##############################################################################

def load_config():
    global config

    basedir = os.path.join(os.path.expanduser("~"), ".mnemosyne")

    try:
        config_file = file(os.path.join(basedir, "config"), 'rb')
        for k,v in cPickle.load(config_file).iteritems():
            config[k] = v
    except:
        pass

    init_config()



##############################################################################
#
# save_config
#
##############################################################################

def save_config():
    basedir = os.path.join(os.path.expanduser("~"), ".mnemosyne")
    config_file = file(os.path.join(basedir,"config"), 'wb')
    cPickle.dump(config, config_file)



##############################################################################
#
# StartTime
#
##############################################################################

class StartTime:

    def __init__(self, start_time):

        # Reset to 3.30 am

        t = time.localtime(start_time)
        self.time = time.mktime([t[0],t[1],t[2], 3,30,0, t[6],t[7],t[8]])

    def days_since(self):
        return long( (time.time() - self.time) / 60. / 60. / 24. )

        
    
##############################################################################
#
# Item
#
##############################################################################

class Item:

    ##########################################################################
    #
    # __init__
    #
    ##########################################################################

    def __init__(self):

        self.id = 0
        
        self.q         = None
        self.a         = None
        self.cat       = None
        
        self.reset_learning_data()

    ##########################################################################
    #
    # reset_learning_data
    #
    ##########################################################################

    def reset_learning_data(self):

        self.grade                = 0
        self.easiness             = 2.5
        
        self.acq_reps             = 0
        self.ret_reps             = 0
        self.lapses               = 0
        self.acq_reps_since_lapse = 0
        self.ret_reps_since_lapse = 0
        
        self.last_rep  = 0 # In days since beginning.
        self.next_rep  = 0 #

    ##########################################################################
    #
    # new_id
    #
    ##########################################################################
    
    def new_id(self):

        digest = md5.new(self.q.encode("utf-8") + self.a.encode("utf-8") + \
                         time.ctime()).hexdigest()
        self.id = digest[0:8]
        
    ##########################################################################
    #
    # sort_key
    #
    ##########################################################################

    def sort_key(self):
        return self.next_rep
    
    ##########################################################################
    #
    # is_due_for_acquisition_rep
    #
    ##########################################################################
    
    def is_due_for_acquisition_rep(self):
        return (self.grade < 2) and (self.cat.active == True)
    
    ##########################################################################
    #
    # is_due_for_retention_rep
    #
    #  Due for a retention repetion within 'days' days?
    #
    ##########################################################################
    
    def is_due_for_retention_rep(self, days=0):
        return (self.grade >= 2) and (self.cat.active == True) and \
               (time_of_start.days_since() >= self.next_rep - days)
    
    ##########################################################################
    #
    # is_in_active_category
    #
    ##########################################################################

    def is_in_active_category(self):
        return (self.cat.active == True)

    ##########################################################################
    #
    # qualifies_for_learn_ahead
    #
    ##########################################################################
    
    def qualifies_for_learn_ahead(self):
        return (self.grade >= 2) and (self.cat.active == True) and \
               (time_of_start.days_since() < self.next_rep) 
        
    ##########################################################################
    #
    # change_category
    #
    ##########################################################################
    
    def change_category(self, new_cat_name):

        global categories, category_by_name

        # Case 1: a new category was created.

        if new_cat_name not in category_by_name.keys():
            cat = Category(new_cat_name)
            categories.append(cat)
            category_by_name[new_cat_name] = cat

        old_cat = self.cat
        self.cat = category_by_name[new_cat_name]
    
        # Case 2: deleted last item of old_cat.

        if old_cat.in_use() == False:
            del category_by_name[old_cat.name]
            categories.remove(old_cat)



##############################################################################
#
# items_are_inverses
#
##############################################################################

def items_are_inverses(item1, item2):

    if item1.q == item2.a and item2.q == item1.a:
        return True
    else:
        return False



##############################################################################
#
# get_items
#
##############################################################################

def get_items():
    return items



##############################################################################
#
# get_item_by_id
#
##############################################################################

def get_item_by_id(id):
    try:
        return [i for i in items if i.id == id][0]
    except:
        return None



##############################################################################
#
# number_of_items
#
##############################################################################

def number_of_items():
    return len(items)



##############################################################################
#
# non_memorised_items
#
##############################################################################

def non_memorised_items():
    return sum(1 for i in items if i.is_due_for_acquisition_rep())



##############################################################################
#
# scheduled_items
#
#   Number of items scheduled within 'days' days.
#
##############################################################################

def scheduled_items(days=0):
    return sum(1 for i in items if i.is_due_for_retention_rep(days))



##############################################################################
#
# active_items
#
#   Number of items in an active category.
#
##############################################################################

def active_items():
    return sum(1 for i in items if i.is_in_active_category())



##############################################################################
#
# average_easiness
#
##############################################################################

def average_easiness():

    if len(items) == 0:
        return 2.5
    if len(items) == 1:
        return items[0].easiness
    else:
        return sum(i.easiness for i in items) / len(items)



##############################################################################
#
# Category
#
##############################################################################

class Category:
    
    ##########################################################################
    #
    # __init__
    #
    ##########################################################################
    
    def __init__(self, name, active=True):

        self.name = name
        self.active = active

    ##########################################################################
    #
    # in_use
    #
    ##########################################################################

    def in_use(self):

        used = False

        for e in items:
            if self.name == e.cat.name:
                used = True
                break

        return used



##############################################################################
#
# get_categories
#
##############################################################################

def get_categories():
    return categories



##############################################################################
#
# get_category_by_name
#
##############################################################################

def get_category_by_name(name):
    return category_by_name[name]



##############################################################################
#
# get_category_names
#
##############################################################################

def get_category_names():
    return category_by_name.keys()



##############################################################################
#
# new_database
#
##############################################################################

def new_database(path):

    global config, time_of_start, load_failed

    if len(items) > 0:
        unload_database()

    load_failed = False

    time_of_start = StartTime(time.time())
    config["path"] = path

    logger.info("New database")

    save_database(path)



##############################################################################
#
# load_database
#
##############################################################################

def load_database(path):

    global config, time_of_start, categories, category_by_name, items
    global load_failed

    if list_is_loaded():
        unload_database()

    try:
        infile = file(path, 'rb')
        db = cPickle.load(infile)

        time_of_start = db[0]
        categories    = db[1]
        items         = db[2]
        
        infile.close()

        load_failed = False

    except:

        load_failed = True
        
        return False

    for c in categories:
        if not c.in_use():
            categories.remove(c)
        else:
            category_by_name[c.name] = c

    config["path"] = path

    logger.info("Loaded database %d %d %d", scheduled_items(), \
                non_memorised_items(), number_of_items())
    
    return True



##############################################################################
#
# save_database
#
##############################################################################

def save_database(path):

    global config

    if load_failed == True: # Don't erase a database which failed to load.
        return False
        
    try:
        outfile = file(path,'wb')

        db = [time_of_start, categories, items]
        cPickle.dump(db, outfile)

        outfile.close()
    except:
        return False

    config["path"] = path
    
    return True



##############################################################################
#
# unload_database
#
##############################################################################

def unload_database():

    global items, revision_queue, categories, category_by_name
        
    status = save_database(config["path"])
    if status == False:
        return False
    
    logger.info("Saved database %d %d %d", scheduled_items(), \
                non_memorised_items(), number_of_items())        
    items = []
    revision_queue = []
        
    categories = []
    category_by_name = {}
    
    return True



##############################################################################
#
# list_is_loaded
#
##############################################################################

def list_is_loaded():
    return len(items) != 0



##############################################################################
#
# expand_path
#
#   Make relative path absolute and normalise slashes.
#
##############################################################################

def expand_path(p):

    if p[0] == "/" or p[1] == ":": # Unix or Windows absolute path.
        return os.path.normpath(p)
    else:
        prefix = os.path.dirname(get_config("path"))   
        return os.path.normpath(os.path.join(prefix, p))



##############################################################################
#
# process_latex
#
##############################################################################

def process_latex(latex_command):
    
    basedir   = os.path.join(os.path.expanduser("~"), ".mnemosyne")
    latexdir  = os.path.join(basedir, "latex")
    imag_name = md5.new(latex_command).hexdigest() + ".png"
    imag_file = os.path.join(latexdir, imag_name)

    if not os.path.exists(imag_file):
        
        os.chdir(latexdir)
    
        f = file("tmp.tex", 'w')
        print >> f, "\\documentclass[12pt]{article}"
        print >> f, "\\pagestyle{empty} \\begin{document} \\begin{displaymath}"     
        print >> f, latex_command
        print >> f, "\\end{displaymath} \\end{document}"
        f.close()

        try:
            os.system("latex tmp.tex")
            os.system("dvipng -D 200 -T tight tmp.dvi")
            shutil.copy("tmp1.png", imag_name)
        except:
            print "Problem with latex. Are latex and dvipnh installed?"
            return ""

    return  "<img src=\"" + latexdir + "/" + imag_name + "\" >"



##############################################################################
#
# preprocess
#
#   Do some text preprocessing of Q/A strings and handle special tags.
#
##############################################################################

def preprocess(old_string):
    
    # Escape literal < (unmatched tag) and new line from string.
    
    hanging = []
    open = 0
    pending = 0

    for i in range(len(old_string)):
        if old_string[i] == '<':
            if open != 0:
                hanging.append(pending)
                pending = i
                continue
            open += 1
            pending = i
        elif old_string[i] == '>':
            if open > 0:
                open -= 1

    if open != 0:
        hanging.append(pending)

    new_string = ""
    for i in range(len(old_string)):
        if old_string[i] == '\n':
            new_string += "<br>"
        elif i in hanging:
            new_string += "&lt;"
        else:
            new_string += old_string[i]

    # Fill out relative paths for img tags.

    i = new_string.lower().find("img src")
    
    while i != -1:
        
        start = new_string.find("\"", i)
        end   = new_string.find("\"", start+1)

        old_path = new_string[start+1:end]

        new_string = new_string[:start+1] + \
                     expand_path(old_path) + \
                     new_string[end:]

        i = new_string.lower().find("img src", end+1)

    # Process latex tags.

    start = new_string.lower().find("<latex>")
    
    while start != -1:
        
        end = new_string.find("</latex>", start+1)

        if end == -1:
            break

        latex_command = new_string[start+7:end]

        new_string = new_string[:start] + \
                     process_latex(latex_command) + \
                     new_string[end+8:]

        start = new_string.lower().find("<latex>", end+1)    
        
    return new_string



##############################################################################
#
# FileFormat
#
# Each file format that Mnemosyne supports is identified by a name (a string).
# Additionally, a file format needs a file name filter (in a string), a
# function to import data from a file of the respective type, and a function
# to export data in the respective format.
#
# The file format name will appear in the import and export dialogues.
# Therefore, they shall be easy to understand by a user, e.g. "Text
# with tab-separated Q/A".
#
# The file name filter has to be given in Qt format, e. g. "XML Files (*.xml
# *XML)". It will be used in the file selection dialogues.
#
# TODO-dh: Think about creating a directory, where each .py file is read at
#     startup.  With such a mechanism, adding additional file formats would
#     not even demand any code change in Mnemosyne's core.
#
##############################################################################

file_formats = []

class FileFormat:

    def __init__(self, name, filter="",
                 import_function=False, export_function=False):

        self.name = name
        self.filter = filter
        self.import_function = import_function
        self.export_function = export_function



##############################################################################
#
# register_file_format
#
##############################################################################

def register_file_format(name, filter="",
                         import_function=False, export_function=False):

    global file_formats
    
    file_formats.append(FileFormat(name, filter,
                                   import_function, export_function))
    
    file_formats.sort(lambda x,y: cmp(x.name, y.name))



##############################################################################
#
# get_importable_file_formats
#
##############################################################################

def get_importable_file_formats():
     return [f for f in file_formats if f.import_function]



##############################################################################
#
# get_exportable_file_formats
#
##############################################################################

def get_exportable_file_formats():
     return [f for f in file_formats if f.export_function]



##############################################################################
#
# get_file_format_from_name
#
##############################################################################

def get_file_format_from_name(name):

    for fformat in file_formats:
        if name == fformat.name:
            return fformat

    raise NameError("Illegal file format name.")



##############################################################################
#
# import_file
#
##############################################################################

def import_file(filename, fformat_name, default_cat_name,
                reset_learning_data=False):

    global category_by_name, categories, load_failed, revision_queue

    # If no database is active, create one.

    if not time_of_start:
        new_database(config["path"])

    # Create default category if necessary.

    if default_cat_name not in category_by_name.keys():
        default_cat = Category(default_cat_name)
        categories.append(default_cat)
        category_by_name[default_cat_name] = default_cat
    else:
        default_cat = category_by_name[default_cat_name]

    # Call import function according to file format name

    fformat = get_file_format_from_name(fformat_name)
    imported_items = fformat.import_function(filename, default_cat,
                                             reset_learning_data)
    if imported_items == False:
        return False # Failure.

    # Add new items.
    
    for item in imported_items:
                    
        # Don't add if the item is already in the database.

        for i in get_items():
            if i.q == item.q and i.a == item.a:
                break
        else:
            items.append(item)
            
            if item.is_due_for_retention_rep():
                revision_queue[0:0] = [item]
                
            interval = item.next_rep - time_of_start.days_since()
            logger.info("Imported item %s %d %d %d %d %d",
                        item.id, item.grade, item.ret_reps,
                        item.last_rep, item.next_rep, interval)

    # Clean up.

    if default_cat.in_use() == False:
        del category_by_name[default_cat.name]
        categories.remove(default_cat)

    load_failed = False

    return True # Success.



##############################################################################
#
# export_file
#
##############################################################################

def export_file(filename, fformat_name,
                cat_names_to_export, reset_learning_data):
    
    # Call export function according to file format name.

    fformat = get_file_format_from_name(fformat_name)
    fformat.export_function(filename, cat_names_to_export, reset_learning_data)

    return True



##############################################################################
#
# XML_Importer
#
##############################################################################

from xml.sax import saxutils, make_parser
from xml.sax.handler import feature_namespaces

class XML_Importer(saxutils.DefaultHandler):
    
    def __init__(self, default_cat=None, reset_learning_data=False):
        self.reading, self.text = {}, {}
        
        self.reading["cat"] = False
        self.reading["Q"]   = False
        self.reading["A"]   = False

        self.default_cat = default_cat
        self.reset_learning_data = reset_learning_data

        self.imported_items = []

    def to_bool(self, string):
        if string == '0':
            return False
        else:
            return True
    
    def startElement(self, name, attrs):
        global import_time_of_start
        
        if name == "mnemosyne":
            if attrs.get("time_of_start"):
                import_time_of_start \
                  = StartTime(long(attrs.get("time_of_start")))
            else:
                import_time_of_start = time_of_start
                
        elif name == "item":
            self.item = Item()
            
            self.item.id = 0
            if attrs.get("id"):
                self.item.id = attrs.get("id")

            self.item.grade = 0
            if attrs.get("gr"):
                self.item.grade = int(attrs.get("gr"))

            self.item.easiness = average_easiness()
            if attrs.get("e"):
                self.item.easiness = float(attrs.get("e"))

            self.item.acq_reps = 0
            if attrs.get("ac_rp"):
                self.item.acq_reps = int(attrs.get("ac_rp"))

            self.item.ret_reps = 0
            if attrs.get("rt_rp"):
                self.item.ret_reps = int(attrs.get("rt_rp"))
                
            self.item.lapses = 0
            if attrs.get("lps"):
                self.item.lapses = int(attrs.get("lps"))
                
            self.item.acq_reps_since_lapse = 0
            if attrs.get("ac_rp_l"):
                self.item.acq_reps_since_lapse = int(attrs.get("ac_rp_l"))

            self.item.ret_reps_since_lapse = 0
            if attrs.get("rt_rp_l"):
                self.item.ret_reps_since_lapse = int(attrs.get("rt_rp_l"))
                
            self.item.last_rep = 0
            if attrs.get("l_rp"):
                self.item.last_rep = int(attrs.get("l_rp"))
                
            self.item.next_rep = 0
            if attrs.get("n_rp"):
                self.item.next_rep = int(float(attrs.get("n_rp")))
                
        elif name == "category":
            self.active = self.to_bool(attrs.get("active"))
        else:
            self.reading[name] = True
            self.text[name] = ""

    def characters(self, ch):
        for name in self.reading.keys():
            if self.reading[name] == True:
                self.text[name] += ch

    def endElement(self, name):

        def decode_cdata(s):
            return saxutils.unescape(s)

        global categories, category_by_name
    
        self.reading[name] = False

        # An item ends with 'A'.
       
        if name == "A":

            self.item.q = decode_cdata(self.text["Q"])
            self.item.a = decode_cdata(self.text["A"])

            if "cat" in self.text.keys():
                cat_name = decode_cdata(self.text["cat"])
                if not cat_name in category_by_name.keys():
                    new_cat = Category(cat_name)
                    categories.append(new_cat)
                    category_by_name[cat_name] = new_cat
                self.item.cat = category_by_name[cat_name]
            else:
                self.item.cat = self.default_cat

            if self.item.id == 0:
                self.item.new_id()
                
            if self.reset_learning_data == True:
                self.item.reset_learning_data()
                self.item.easiness = average_easiness()

            self.imported_items.append(self.item)

        # A category ends with 'name'.

        elif name == "name":
            
            name = self.text["name"]
            
            if name not in category_by_name.keys():
                cat = Category(name, self.active)
                categories.append(cat)
                category_by_name[name] = cat



##############################################################################
#
# memaid_XML_Importer
#
##############################################################################

class memaid_XML_Importer(saxutils.DefaultHandler):
    
    def __init__(self, default_cat=None, reset_learning_data=False):
        self.reading, self.text = {}, {}
        
        self.reading["cat"] = False
        self.reading["Q"]   = False
        self.reading["A"]   = False

        self.default_cat = default_cat
        self.reset_learning_data = reset_learning_data

        self.imported_items = []

    def to_bool(self, string):
        if string == '0':
            return False
        else:
            return True
    
    def startElement(self, name, attrs):
        global import_time_of_start
        
        if name == "memaid":
            if attrs.get("time_of_start"):
                import_time_of_start \
                  = StartTime(long(attrs.get("time_of_start")))
            else:
                import_time_of_start = time_of_start
                
        elif name == "item":
            self.item = Item()

            self.item.id        = long(attrs.get("id"))
            self.item.grade     =  int(attrs.get("gr"))
            self.item.next_rep  =  int(attrs.get("tm_t_rpt"))
            self.item.ret_reps  =  int(attrs.get("rp"))
            interval            =  int(attrs.get("ivl"))
            self.item.last_rep  = self.item.next_rep - interval
            self.item.easiness  = average_easiness()

        elif name == "category":
            self.active = self.to_bool(attrs.get("scheduled"))
        else:
            self.reading[name] = True
            self.text[name] = ""

    def characters(self, ch):
        for name in self.reading.keys():
            if self.reading[name] == True:
                self.text[name] += ch

    def endElement(self, name):

        global categories, category_by_name
    
        self.reading[name] = False

        # An item ends with 'A'.
       
        if name == "A":

            self.item.q = self.text["Q"]
            self.item.a = self.text["A"]

            if "cat" in self.text.keys():
                cat_name = self.text["cat"]
                if not cat_name in category_by_name.keys():
                    new_cat = Category(cat_name)
                    categories.append(new_cat)
                    category_by_name[cat_name] = new_cat
                self.item.cat = category_by_name[cat_name]
            else:
                self.item.cat = self.default_cat

            if self.item.id == 0:
                self.item.new_id()

            if self.reset_learning_data == True:
                self.item.reset_learning_data()
                self.item.easiness = average_easiness()

            self.imported_items.append(self.item)

        # A category ends with 'name'.

        elif name == "name":
            
            name = self.text["name"]
            
            if name not in category_by_name.keys():
                cat = Category(name, self.active)
                categories.append(cat)
                category_by_name[name] = cat

          

##############################################################################
#
# import_XML
#
#   Note that we do not register separate file formats for Mnemosyne and
#   Memaid XML. We're able to figure out the difference on our own and do not
#   need to put this burden on the user.
#
##############################################################################

def import_XML(filename, default_cat, reset_learning_data=False):
    
    global items

    # Determine if we import a Mnemosyne or a Memaid file.

    handler = None

    f = None
    try:
        f = file(filename)
    except:
        try:
            f = file(unicode(filename).encode("latin"))
        except:
            print "Unable to open file."
            return False
    
    f.readline()
        
    if "mnemosyne" in f.readline():
        handler = XML_Importer(default_cat, reset_learning_data)
    else:
        handler = memaid_XML_Importer(default_cat, reset_learning_data)
        
    f.close()

    # Parse XML file.

    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    parser.setContentHandler(handler)

    try:
        parser.parse(file(filename))
    except Exception, e:
        print "Error parsing XML:\n"
        traceback.print_exc()
        return False

    # Calculate offset with current start date.
    
    cur_start_date =        time_of_start.time
    imp_start_date = import_time_of_start.time
    
    offset = long(round((cur_start_date - imp_start_date) / 60. / 60. / 24.))
        
    # Adjust timings.

    if reset_learning_data == False:
        if cur_start_date <= imp_start_date :
            for item in handler.imported_items:
                item.last_rep += abs(offset)
                item.next_rep += abs(offset)
        else:
            time_of_start.time = imp_start_date
            for item in items:
                item.last_rep += abs(offset)
                item.next_rep += abs(offset)

    return handler.imported_items



##############################################################################
#
# write_item_XML
#
##############################################################################

def write_item_XML(e, outfile, reset_learning_data=False):

    def encode_cdata(s):
        return "<![CDATA[" + saxutils.escape(s.encode("utf-8")) + "]]>"

    if reset_learning_data == False:
        print >> outfile, "<item id=\""+str(e.id) + "\"" \
                         + " gr=\""+str(e.grade) + "\"" \
                         + " e=\""+ "%.3f" % e.easiness + "\"" \
                         + " ac_rp=\""+str(e.acq_reps) + "\"" \
                         + " rt_rp=\""+str(e.ret_reps) + "\""  \
                         + " lps=\""+str(e.lapses) + "\"" \
                         + " ac_rp_l=\""+str(e.acq_reps_since_lapse) + "\"" \
                         + " rt_rp_l=\""+str(e.ret_reps_since_lapse) + "\"" \
                         + " l_rp=\""+str(e.last_rep) + "\"" \
                         + " n_rp=\""+str(e.next_rep) + "\">"
    else:
         print >> outfile, "<item>"
         
    print >> outfile, " <cat>" + encode_cdata(e.cat.name) + "</cat>"
    print >> outfile, " <Q>" + encode_cdata(e.q) + "</Q>"
    print >> outfile, " <A>" + encode_cdata(e.a) + "</A>"
    print >> outfile, "</item>"



##############################################################################
#
# bool_to_digit
#
##############################################################################

def bool_to_digit(b):
    
    if b == True:
        return "1"
    else:
        return "0"



##############################################################################
#
# write_category_XML
#
##############################################################################

def write_category_XML(category, outfile, reset_learning_data):

    if reset_learning_data == True:
        active = True
    else:
        active = category.active
    
    print >> outfile, "<category active=\"" \
          + bool_to_digit(active) + "\">"
    print >> outfile, " <name><![CDATA["+category.name.encode("utf-8") \
          +"]]></name>"
    print >> outfile, "</category>"

    

##############################################################################
#
# export_XML
#
##############################################################################

def export_XML(filename, cat_names_to_export, reset_learning_data):
    
    outfile = file(filename,'w')

    print >> outfile, """<?xml version="1.0" encoding="UTF-8"?>"""

    print >> outfile, "<mnemosyne core_version=\"1\"",

    if reset_learning_data == False:
        print >> outfile, "time_of_start=\"" + \
              str(long(time_of_start.time))+"\"",

    print >> outfile, ">"
    
    for cat in categories:
        if cat.name in cat_names_to_export:
            write_category_XML(cat, outfile, reset_learning_data)

    for e in items:
        if e.cat.name in cat_names_to_export:
            write_item_XML(e, outfile, reset_learning_data)

    print >> outfile, """</mnemosyne>"""

    outfile.close()


register_file_format("XML",
                     filter="XML file (*.xml *.XML)",
                     import_function=import_XML,
                     export_function=export_XML)



##############################################################################
#
# import_txt
#
#   Question and answers on a single line, separated by tab.
#
##############################################################################

def import_txt(filename, default_cat, reset_learning_data=False):
    
    global items

    imported_items = []

    # Parse txt file.

    avg_easiness = average_easiness()

    f = None
    try:
        f = file(filename)
    except:
        try:
            f = file(filename.encode("latin"))
        except:
            print "Unable to open file."
            return False
    
    for line in f:
        
        try:
            line = unicode(line, "utf-8")
        except:
            try:
                line = unicode(line, "latin")
            except:
                print "Unrecognised encoding."
                return False

        line = line.rstrip()
        if len(line) == 0:
            continue
        
        item = Item()

        try:
            item.q, item.a = line.split('\t')
        except Exception, e:
            print "Error parsing txt file:\n"
            traceback.print_exc()
            return False
        
        item.easiness = avg_easiness
        item.cat = default_cat
        item.new_id()
                    
        imported_items.append(item)

    return imported_items



##############################################################################
#
# export_txt
#
#   Newlines are converted to <br> to keep items on a single line.
#
##############################################################################

def export_txt(filename, cat_names_to_export, reset_learning_data=False):
    
    outfile = file(filename,'w')

    for e in items:
        if e.cat.name in cat_names_to_export:
            question = e.q.encode("utf-8")
            question = question.replace("\t", " ")
            question = question.replace("\n", "<br>")
            
            answer = e.a.encode("utf-8")
            answer = answer.replace("\t", " ")
            answer = answer.replace("\n", "<br>")
            
            print >> outfile, question + "\t" + answer

    outfile.close()
    

register_file_format("Text with tab separated Q/A",
                     filter="Text file (*.txt *.TXT)",
                     import_function=import_txt,
                     export_function=export_txt)



##############################################################################
#
# Functions for importing and exporting files in SuperMemo's text file format:
# A line starting with `Q: � holds a question, a line starting with `A: �
# holds an answer.  Several consecutive question lines form a multi line
# question, several consecutive answer lines form a multi line answer.  After
# the answer lines, learning data may follow.  This consists of a line like
# `I: REP=8 LAP=0 EF=3.200 UF=2.370 INT=429 LAST=27.01.06� and a line like
# `O: 36�.  After each item (even the last one) there must be an empty line.
#
##############################################################################

def read_line_sm7qa(f):

    line = f.readline()

    if not line:
        return False

    line = line.rstrip()

    # Supermemo uses the octet 0x03 to represent the � character.  Since this
    # does not seem to be a standard encoding, we simply replace this.
    
    line = line.replace("\x03", "�")

    try:
        line = unicode(line, "latin")
    except:
        try:
            line = unicode(line, "utf-8")
        except:
            print "Unrecognised encoding."
            return False

    return line



def import_sm7qa(filename, default_cat, reset_learning_data=False):

    global items

    # Parse txt file.

    avg_easiness = average_easiness()

    f = None
    try:
        f = file(filename)
    except:
        try:
            f = file(filename.encode("latin"))
        except:
            print "Unable to open file."
            return False

    imported_items = []
    state = "ITEM-START"
    error = False

    while not error and state != "END-OF-FILE":

        line = read_line_sm7qa(f)

        # Perform the actions of the current state and calculate the next state.

        if state == "ITEM-START":
            
            # Expecting a new item to start, or the end of the input file.
            
            if line == False:
                next_state = "END-OF-FILE"
            elif line == "":
                next_state = "ITEM-START"
            elif line.startswith("Q:"):
                question = line[2:].strip()
                repetitions = 0
                lapses = 0
                easiness = avg_easiness
                interval = 0
                last = 0
                next_state = "QUESTION"
            else:
                error = True
        elif state == "QUESTION":
            
            # We have already read the first question line. Further question
            # lines may follow, or the first answer line.

            if line == False:
                error = True
            elif line.startswith("Q:"):
                question = question + "\n" + line[2:].strip()
                next_state = "QUESTION"
            elif line.startswith("A:"):
                answer = line[2:].strip()
                next_state = "ANSWER"
            else:
                error = True
        elif state == "ANSWER":
            
            # We have already read the first answer line. Further answer
            # lines may follow, or the lines with the learning data.
            # Otherwise, the item has to end with either an empty line or with
            # the end of the input file.
            
            if line == False:
                next_state = "END-OF-FILE"
            elif line == "":
                next_state = "ITEM-START"
            elif line.startswith("A:"):
                answer = answer + "\n" + line[2:].strip()
                next_state = "ANSWER"
            elif line.startswith("I:"):
                attributes = line[2:].split()
                if len(attributes) != 6:
                    error = True
                else:
                    if ( attributes[0].startswith("REP=")
                            and attributes[1].startswith("LAP=")
                            and attributes[2].startswith("EF=")
                            and attributes[4].startswith("INT=")
                            and attributes[5].startswith("LAST=") ):
                        repetitions = int(attributes[0][4:])
                        lapses = int(attributes[1][4:])
                        easiness = float(attributes[2][3:])
                        interval = int(attributes[4][4:])
                        if attributes[5] == "LAST=0":
                            last = 0
                        else:
                            last = time.strptime(attributes[5][5:], "%d.%m.%y")
                    else:
                        error = True
                next_state = "LEARNING-DATA"
            else:
                error = True
        elif state == "LEARNING-DATA":
            
            # We have already read the first line of the learning data. The
            # second line with the learning data has to follow.
            
            if line == False:
                error = True
            elif line.startswith("O:"): # This line is ignored.
                next_state = "ITEM-END"
            else:
                error = True
        elif state == "ITEM-END":
            
            # We have already read all learning data. The item has to end
            # with either an empty line or with the end of the input file.
            
            if line == False:
                next_state = "END-OF-FILE"
            elif line == "":
                next_state = "ITEM-START"
            else:
                error = True

        # Perform the transition actions that are common for a set of
        # transitions.

        if ( (state == "ANSWER" and next_state == "END-OF-FILE")
                or (state == "ANSWER" and next_state == "ITEM-START")
                or (state == "ITEM-END" and next_state == "END-OF-FILE")
                or (state == "ITEM-END" and next_state == "ITEM-START") ):
            item = Item()

            if not reset_learning_data:
                
                # Calculate the dates for the last and next repetitions.
                
                if last == 0:
                    last_in_seconds = 0
                else:
                    last_in_seconds = StartTime(time.mktime(last)).time \
                                      - time_of_start.time
                last_in_days = last_in_seconds / 60. / 60. / 24.
                item.last_rep = long(max(0, last_in_days ))
                item.next_rep = long(max(0, last_in_days + interval ))

                # A grade information is not given directly in the file format.
                
                if item.next_rep > 0:
                    
                    # SuperMemo has scheduled the item for tomorrow or later. We
                    # set the grade to 4 to make Mnemosyne comply to this.
                    
                    item.grade = 4
                    
                elif repetitions == 0:
                    
                    # The item is new, there are no repetitions yet.
                    
                    item.grade = 0
                    
                elif repetitions == 1 and lapses > 0:
                    
                    # The learner had a lapse with the last repetition.
                    
                    item.grade = 0
                    
                else:
                    
                    # There were either no lapses yet, or some successful
                    # repetitions since.
                    
                    item.grade = 4
                    
                item.easiness = easiness

                # The following information is not reconstructed from SuperMemo:
                #
                # item.acq_reps, item.ret_reps, item.lapses,
                # item.acq_reps_since_lapse, item.ret_reps_since_lapse

                # The following information from SuperMemo is not used: UF, O_value

            item.q = saxutils.escape(question)
            item.a = saxutils.escape(answer)
            item.cat = default_cat

            item.new_id()

            imported_items.append(item)

        # Go to the next state.

        state = next_state

    if error:
        return False
    else:
        return imported_items


register_file_format("SuperMemo7 Text in Q:/A: format",
                     filter="SuperMemo7 text file (*.txt *.TXT)",
                     import_function=import_sm7qa,
                     export_function=False)




##############################################################################
#
# add_new_item
#
##############################################################################

def add_new_item(grade, question, answer, cat_name):

    global items, categories, category_by_name, load_failed

    if cat_name not in category_by_name.keys():
        cat = Category(cat_name)
        categories.append(cat)
        category_by_name[cat_name] = cat
    else:
        cat = category_by_name[cat_name]
    
    item = Item()
    
    item.q     = question
    item.a     = answer
    item.cat   = cat
    item.grade = grade

    item.easiness = average_easiness()
    
    item.new_id()

    new_interval = 0

    if grade == 2 or grade == 3:
        new_interval = random.randint(1,2)
    if grade == 4:
        new_interval = random.randint(2,3)
    if grade == 5:
        new_interval = random.randint(3,6)        
 
    item.next_rep = time_of_start.days_since() + new_interval
    
    items.append(item)    

    logger.info("New item %s %d %d", item.id, item.grade, new_interval)

    load_failed = False
    
    return item



##############################################################################
#
# delete_item
#
##############################################################################

def delete_item(e):

    old_cat = e.cat
    
    items.remove(e)
    rebuild_revision_queue()
    
    if old_cat.in_use() == False:
        del category_by_name[old_cat.name]
        categories.remove(old_cat)

    logger.info("Deleted item %s", e.id)



##############################################################################
#
# rebuild_revision_queue
#
##############################################################################

def rebuild_revision_queue(learn_ahead = False):
            
    global revision_queue
    
    revision_queue = []

    if len(items) == 0:
        return

    # Always add items that are due for revision.

    revision_queue = [i for i in items if i.is_due_for_retention_rep()]
    random.shuffle(revision_queue)

    # If the queue is empty, then add items which are not yet memorised.
    # Take only a limited number of grade 0 items from the unlearned items,
    # to avoid too long intervals between repetitions.
    
    if len(revision_queue) == 0:
        
        not_memorised = [i for i in items if i.is_due_for_acquisition_rep()]

        grade_0 = [i for i in not_memorised if i.grade == 0]
        grade_1 = [i for i in not_memorised if i.grade == 1]

        limit = get_config("grade_0_items_at_once")

        grade_0_selected = []

        for i in grade_0:

            for j in grade_0_selected:
                if items_are_inverses(i, j):
                    break
            else:
                grade_0_selected.append(i)

            if len(grade_0_selected) == limit:
                break

        random.shuffle(grade_0_selected)
        revision_queue[0:0] = grade_0_selected

        random.shuffle(grade_1)
        revision_queue[0:0] = grade_1
        
        random.shuffle(grade_0_selected)
        revision_queue[0:0] = grade_0_selected

    # If the queue is still empty, then simply return. The user can signal
    # that he wants to learn ahead by calling rebuild_revision_queue with
    # 'learn_ahead' set to True. Don't shuffle this queue, as it's more
    # useful to review the earliest scheduled items first.

    if len(revision_queue) == 0:
        
        if learn_ahead == False:
            return
        else:
            revision_queue = [i for i in items \
                              if i.qualifies_for_learn_ahead()]

            revision_queue.sort(key=Item.sort_key)



##############################################################################
#
# in_revision_queue
#
##############################################################################

def in_revision_queue(item):
    return item in revision_queue



##############################################################################
#
# remove_from_revision_queue
#
#   Remove a single instance of an item from the queue. Necessary when
#   the queue needs to be rebuilt, and there is still a question pending.
#
##############################################################################

def remove_from_revision_queue(item):
    
    global revision_queue
    
    for i in revision_queue:
        if i.id == item.id:
            revision_queue.remove(i)
            return



##############################################################################
#
# start_thinking
#
##############################################################################

def start_thinking():

    global thinking_time, time_of_last_question

    thinking_time = 0
    time_of_last_question = time.time()



##############################################################################
#
# pause_thinking
#
##############################################################################

def pause_thinking():

    global thinking_time

    if time_of_last_question != 0:
        thinking_time += time.time() - time_of_last_question



##############################################################################
#
# unpause_thinking
#
##############################################################################

def unpause_thinking():

    global time_of_last_question
    
    if time_of_last_question != 0:
        time_of_last_question = time.time()



##############################################################################
#
# stop_thinking
#
##############################################################################

def stop_thinking():

    global thinking_time, time_of_last_question
    
    thinking_time += time.time() - time_of_last_question
    time_of_last_question = 0



##############################################################################
#
# get_new_question
#
##############################################################################

def get_new_question(learn_ahead = False):
            
    # Populate list if it is empty.
        
    if len(revision_queue) == 0:
        rebuild_revision_queue(learn_ahead)
        if len(revision_queue) == 0:
            return None

    # Pick the first question and remove it from the queue.

    item = revision_queue[0]
    revision_queue.remove(item)

    return item



##############################################################################
#
# process_answer
#
##############################################################################

def process_answer(item, new_grade):

    global revision_queue, items

    scheduled_interval = item.next_rep              - item.last_rep
    actual_interval    = time_of_start.days_since() - item.last_rep

    # In the acquisition phase and staying there.
    
    if item.grade in [0,1] and new_grade in [0,1]:

        item.acq_reps += 1
        item.acq_reps_since_lapse += 1
        
        new_interval = 0

    # In the acquisition phase and moving to the retention phase.

    if item.grade in [0,1] and new_grade in [2,3,4,5]:

         item.acq_reps += 1
         item.acq_reps_since_lapse += 1

         new_interval = 1

         # Make sure the second copy of a grade 0 item doesn't show up again.

         if item.grade == 0:
             for i in revision_queue:
                 if i.id == item.id:
                     revision_queue.remove(i)
                     break

         # If this is the very first time we grade this item, (e.g. after
         # importing it) allow for slightly longer scheduled intervals,
         # as we might know this item from before (similar to add_new_item). 

         if item.acq_reps == 1 and item.ret_reps == 0 and new_grade > 2:
             new_interval = new_grade

    # In the retention phase and dropping back to the acquisition phase.

    if item.grade in [2,3,4,5] and new_grade in [0,1]:

         item.ret_reps += 1
         item.lapses += 1
         item.acq_reps_since_lapse = 0
         item.ret_reps_since_lapse = 0

         new_interval = 0

         # Move this item to the front of the list, to have precedence over
         # items which are still being learned for the first time.

         items.remove(item)
         items.insert(0,item)

    # In the retention phase and staying there.

    if item.grade in [2,3,4,5] and new_grade in [2,3,4,5]:

        item.ret_reps += 1
        item.ret_reps_since_lapse += 1

        if actual_interval >= scheduled_interval:
            if new_grade == 3:
                item.easiness -= 0.14
            if new_grade == 5:
                item.easiness += 0.10
            if item.easiness < 1.3:
                item.easiness = 1.3
            
        new_interval = 0
        
        if item.ret_reps_since_lapse == 1:
            new_interval = 6
        else:
            if new_grade == 3:
                if actual_interval <= scheduled_interval:
                    new_interval = actual_interval * item.easiness
                else:
                    new_interval = scheduled_interval
                    
            if new_grade == 4:
                new_interval = actual_interval * item.easiness
                
            if new_grade == 5:
                if actual_interval < scheduled_interval:
                    new_interval = scheduled_interval # Avoid spacing.
                else:
                    new_interval = actual_interval * item.easiness

        # Shouldn't happen, but build in a safeguard.

        if new_interval == 0:
            logger.info("Internal error: new interval was zero.")
            new_interval = scheduled_interval

        new_interval = int(new_interval)

    # Add some randomness to interval.

    if new_interval == 0:
        noise = 0
    elif new_interval == 1:
        noise = random.randint(0,1)
    elif new_interval <= 10:
        noise = random.randint(-1,1)
    elif new_interval <= 60:
        noise = random.randint(-3,3)
    else:
        a = .05 * new_interval
        noise = int(random.uniform(-a,a))

    # Update grade and interval.
    
    item.grade    = new_grade
    item.last_rep = time_of_start.days_since()
    item.next_rep = time_of_start.days_since() + new_interval + noise

    # Don't schedule inverse or identical questions on the same day.

    for j in items:
        if (j.q == item.q and j.a == item.a) or items_are_inverses(item, j):
            if j != item and j.next_rep == item.next_rep and item.grade >= 2:
                item.next_rep += 1
                noise += 1
        
    logger.info("R %s %d %1.2f | %d %d %d %d %d | %d %d | %d %d | %1.1f",
                item.id, item.grade, item.easiness,
                item.acq_reps, item.ret_reps, item.lapses,
                item.acq_reps_since_lapse, item.ret_reps_since_lapse,
                scheduled_interval, actual_interval,
                new_interval, noise, thinking_time)
    


##############################################################################
#
# finalise
#
##############################################################################

def finalise():

    if upload_thread:
        print "Waiting for uploader thread to stop..."
        upload_thread.join()
        print "done!"
    
    logger.info("Program stopped")

    basedir = os.path.join(os.path.expanduser("~"), ".mnemosyne")
    os.remove(os.path.join(basedir,"MNEMOSYNE_LOCK"))
    
