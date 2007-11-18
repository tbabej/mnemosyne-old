import os, sys, shutil

from distutils.core import setup, Extension

if sys.platform == "win32":
    import py2exe

import mnemosyne.version

#############################################################################

class InnoScript:
    def __init__(self,
                 name,
                 lib_dir,
                 dist_dir,
                 windows_exe_files = [],
                 lib_files = [],
                 qm_files = [],
                 version = mnemosyne.version.version):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = name
        self.version = version
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]
        self.qm_files = [self.chop(p) for p in qm_files]

    def chop(self, pathname):
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]
    
    def create(self, pathname="dist\\mnemosyne.iss"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi

        print >> ofi, r"[Files]"
        for path in self.windows_exe_files + self.lib_files + self.qm_files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))         
        print >> ofi
        
        print >> ofi, r"[Icons]"
        for path in self.windows_exe_files:
            print >> ofi, r'Name: "{group}\%s"; Filename: "{app}\%s"' % (self.name, path),
        print >> ofi, ' ; WorkingDir: {app}'
        print >> ofi, 'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name

    def compile(self):
        try:
            import ctypes
        except ImportError:
            try:
                import win32api
            except ImportError:
                import os
                os.startfile(self.pathname)
            else:
                print "Ok, using win32api."
                win32api.ShellExecute(0, "compile",
                                                self.pathname,
                                                None,
                                                None,
                                                0)
        else:
            print "Cool, you have ctypes installed."
            res = ctypes.windll.shell32.ShellExecuteA(0, "compile",
                                                      self.pathname,
                                                      None,
                                                      None,
                                                      0)
            if res < 32:
                raise RuntimeError, "ShellExecute failed, error %d" % res


#############################################################################


if sys.platform == "win32":
    from py2exe.build_exe import py2exe
else:
    class py2exe:
        pass
    
class build_installer(py2exe):
    
    # This first builds the exe file(s), then creates a Windows installer.
    # You need InnoSetup for it.
    
    def run(self):
        
        # First, let py2exe do it's work.
        
        py2exe.run(self)

        lib_dir = self.lib_dir
        dist_dir = self.dist_dir

        # Prepare to install translations.
        
        join = os.path.join
        
        pyqt_ui_dir = join("mnemosyne", "pyqt_ui")
        locale_dir = join(pyqt_ui_dir, "locale")

        os.mkdir(join(dist_dir, "locale"))

        self.qm_files = []
        for p in os.listdir(locale_dir):
            if p.endswith(".qm"):
                 src = join(os.path.abspath(locale_dir), p)
                 dest = join(join(dist_dir, "locale"), p)
                 shutil.copy(src, dest)
                 self.qm_files.append(dest)     
        
        # Create the Installer, using the files py2exe has created.
        
        script = InnoScript("Mnemosyne",
                            lib_dir,
                            dist_dir,
                            self.windows_exe_files,
                            self.lib_files,
                            self.qm_files,
                            version=mnemosyne.version.version)
        script.create()
        script.compile()
        
        # Note: the final setup.exe will be in an Output subdirectory.



        
#############################################################################

if sys.platform == "win32": # For py2exe.
    base_path = ""
    data_files = None
else:
    base_path = os.path.join(sys.exec_prefix, "lib", "python"+sys.version[:3],
                             "site-packages","mnemosyne")
    data_files = [('/usr/share/applications', ['mnemosyne.desktop']),
                  ('/usr/share/icons', ['pixmaps/mnemosyne.png'])]
  
pixmap_path = os.path.join(base_path, "pixmaps")
util_path   = os.path.join(base_path, "util")
doc_path    = os.path.join(base_path, "docs")

setup (name = "mnemosyne",
       version = mnemosyne.version.version,
       author = "Peter Bienstman",
       author_email = "Peter.Bienstman@UGent.be",
       packages = ["mnemosyne", "mnemosyne.pyqt_ui","mnemosyne.core"],
       package_data = {"mnemosyne.pyqt_ui": ['locale/*.qm']},
       data_files = data_files,
       scripts = ['mnemosyne/pyqt_ui/mnemosyne'],
       windows = [{'script':'mnemosyne/pyqt_ui/mnemosyne',
                   "icon_resources":[(1,"pixmaps/mnemosyne.ico")]}],
       #console = [{'script':'mnemosyne/pyqt_ui/mnemosyne',
       #            "icon_resources":[(1,"mnemosyne/pixmaps/mnemosyne.ico")]}],
       cmdclass = {"py2exe": build_installer}
       )
