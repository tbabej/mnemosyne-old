<?php   include 'include/header.php';
        $lastmod = date ("M d, Y @ h:ia", getlastmod());
?>

<div id="content">

<h1>Changelog</h1>
<pre>

MNEMOSYNE 1.0 : 20071227

(Note that for Windows users we recommend uninstalling the previous 
version before doing an upgrade.)

-Mnemosyne can now be run from a USB drive. Copy the Mnemosyne directory
 from C:\Program Files to your USB drive, and then copy the .mnemosyne 
 directory from inside your home directory to inside the Mnemosyne directory
 on the USB drive. Alternatively, you can start mnemosyne with the -d option
 to specify where .mnemosyne directory is located, e.g. 
   F:\Mnemosyne\mnemosyne.exe -d F:\.mnemosyne
	
 To run the Linux version from a USB key, untar the source file
 mnemosyne-X.X.tgz (with X.X the version number) to the USB key. Copy your 
 .mnemosyne directory to the USB key as well. Change to the directory where 
 the USB key is mounted and type

 PYTHONPATH=mnemosyne-X.X python mnemosyne-X.X/mnemosyne/pyqt_ui/mnemosyne -d .

 (This assumes that the system you are working on has Python installed, as 
 well as all the libraries Mnemosyne requires.)
-new logo, thanks to a contributor whose name sadly got lost in the 
 demise of the open-collab site.
-new icons, based on the Crystal iconset.
-added tip of the day wizard.
-implemented a basic plugin system. The directory .mnemosyne/plugins
 can contain Python scripts which will be executed at run time and
 which can be used to customise Mnemosyne or add new features.
-when importing from tab separated txt files, the presence of 3 columns
 on a line gives results in the import of 3-sided cards (written form / 
 pronunciation / translation).
-choosing 'reset learning data' on export now preserves the relationship
 between cards (for e.g. inverses and three-sided cards).
-automatically back up the database to XML on exit. The last five backups 
 are kept in .mnemosyne/backup.
-support for multiple sound tags per field (requested by compiu).
-removed a few rarely used options from the configuration dialog and
 placed them in .mnemosyne/config.py, a new file which can be used to
 set these and other rarely used options.
-increase the maximum value of 'increase size of non-latin characters'
 to 200 (requested by Mike Charlton).
-make 'increase size of non-latin characters' more robust (Nils Kriha).
 Previously, not all values of this setting would result in a visible
 change.
-don't count inactive cards in the grade distribution in the statistics
 window (reported by Joonatan Kaartinen).
-add support for translations. (German translation provided by Martin Mueller,
 Spanish by Daniel Alvarez Wise and Juan Alonsa, Dutch by Edwin de Jong) 
 The translation will be chosen automatically based on your system's 
 localisation, but can be overridden by editing the 'locale' variable in 
 .mnemosyne/config.py. 
-improved tooltips.
-added desktop file, so that Mnemosyne shows up in the application menu
 under Linux.
-more verbose error messages when an import failed, showing the line that
 failed to parse.
-log uploading now works if a proxy is needed to access the web.
-added support for Unicode filenames.
-recreate user id from history folder in case the config file was 
 accidentally deleted.
-don't exit when final save failed (requested by lebowski_404).
-added more supported sound and picture formats.
-don't stumble over (invalid) unicode in latex commands (reported by Tomek
 Guzialek).
-fixed 'Save as' option.

	
MNEMOSYNE 0.9.10 : 2007-10-28

-added 3-sided cards, to make dealing with vocabulary in foreign scripts 
 easier. Right clicking the text field in 'add cards' gives you to option
 to switch to 3-sided card input, which replaces the question and answer
 fields by 3 fields: written form, pronunciation, translation. After 
 selecting an initial grade, 2 cards will be added:

  Q: written form
  A: pronunciation
     translation

 and

  Q: translation
  A: written form
     pronunciation  

-when creating multiple cards from the same data (either through add vice
 versa or the 3-sided input), the relationship between these cards is now
 stored. In a future version, this will make it possible that editing one 
 card of the set automatically updates the other ones.
-added feature to insert an image or a sound tag by using a file selector. 
 Accessed through popup-menu or keyboard shortcuts.
-remember more settings across invocations: file formats and directories,
 reset learning data, column width and sorting order, ...
-rationalised keyboard shortcuts and menus. Added list of keyboard shortcuts
 to the website.
-polished file dialogs.
-when possible, paths in the config file are now saved relative to the 
 .mnemosyne directory rather than as absolute paths. This makes it easier
 to copy the .mnemosyne directory back and forth between a Linux and a
 Windows machine.
-respect duplicate handling configuration options when importing (reported 
 by lebowski_404).
-latex output and error messages are now written to the file 
 .mnemosyne/latex/latex_out.txt rather than to the screen, so that they
 are not lost for Windows users.
-fixed bug when showing the statistics for an empty database (reported by 
 Gintautas Miliauskas).


MNEMOSYNE 0.9.9 : 2007-08-16

-added 'Show statistics' menu option, showing the schedule for the
 next week, the distribution of the items over the grades and the number 
 of items for each category.
-added simple per-item statistics in pop-up menu in 'edit items'.
-performance improvements.
-new latex tags, based on code by Christopher Gilbreth and bug reports by 
 Jamned:
   -&lt$>...&lt/$>         : for inline equations
   -&lt$$>...&lt/$$>       : for centered equations on a separate line
   -&ltlatex>...&lt/latex> : for latex code not in a certain environment
 This means that the functionality of the old &ltlatex>...&lt/latex> tags is
 now taken over by &lt$>...&lt/$>. However, there is no need to update your 
 items, as you can rely on the following new feature: 
-don't abort on small latex errors which the latex interpreter can fix
 itself (like missing $) (requested by S. Scharrer).
-the preamble and postamble used when processing the latex tags can now
 be customised by editing the files 'preamble' and 'postamble' in 
 &lthome dir>/.mnemosyne/latex.
-the command invoking dvipng to create images from latex can now be 
 customised by editing the file 'dvipng' in &lthome dir>/.mnemosyne/latex
-remember category and vice-versa settings across invocations when adding 
 items.
-add maximise button to add and edit items under Windows (thanks to
 pizzasource and S. Scharrer).
-respect setting 'number of grade 0 items to learn at once' to zero 
 (reported by pizzasource).
-fix word wrap when using left alignment (reported by TomC).
-don't abort when sound initialisation fails.


MNEMOSYNE 0.9.8.1: 2007-04-23

-fix scheduling bug when importing new grade 0 items (reported by Jim 
Slattery).
-remove incorrect statement with respect to grade 2 behaviour from the 
manual. In 0.9.8, the code was changed to be consistent with the old 
manual. This has been reverted, so that grade 2 behaviour is again more 
like 0.9.7.


MNEMOSYNE 0.9.8: 2007-04-13

-added sound support through tags like &ltsound src="a.wav">. The path to
 the sound file is either absolute or relative to the location of your 
 .mem file. To play the sound again, press the 'R' key in the main window. 
 Supported file formats are wav, ogg and mp3. On Linux, this requires
 properly installing pygame and its dependencies like SDL.
-add option to increase size of non-latin characters relative to latin
 characters (together with N. Kriha).
-disable 'edit item' as long as the answer is not shown, to prevent 
 accidentally revealing it (patch by D. Herrmann).
-fix handling of &lt inside latex tags (reported by jgurling, patch by N. 
 Kriha).
-warn when exiting an 'Add items' which contains an item which has not
 been added (requested by Airconditioning).
-fix UTF-8 handling in the Supermemo7 file format (reported by Loco)
-fix corner cases in scheduling algorithm (patch by Querido).
-make button ordering more consistent in add items (reported by N. Kriha).
-fixed handling of multiple latex tags (reported by M. Boespflug).
-don't hang on latex errors (reported by M. Boespflug).
-make tab-separated import resistant to the presence of multiple tabs 
 (reported by J. Forrez).
-fixed hang when end quotes are not present inside a tag.
-fixed regression where the active flag of categories was not respected on
 import (reported by A. Rachmatullah).
-respect left align option in 'preview items' (reported by E. Grannan).
-making saving more robust while Windows is shutting down (fix by Tom).
-various small interface cleanups and fixes.


MNEMOSYNE 0.9.7: 2006-10-27

-multiple items can now be selected in the 'edit items' dialog in order
 to delete them, change their categories, or add their vice versas.
-added option to import text files where question and answer are each on
 their own line.
-again respect window size set by user.
-make delete button work in 'edit items' dialog (reported by J. Forrez).
-worked around oddity (extra first character in text file) when importing 
 Word unicode text files.
-various small interface cleanups and fixes.
-updated documentation on the website.


MNEMOSYNE 0.9.6: 2006-10-07

-added LaTeX support for formulas, e.g. &ltlatex>x^2+y^2=z^2&lt/latex>. For 
 this you need latex and dvipng installed. Windows users can download 
 MiKTeX. (thanks to input from Henrik Skov Midtiby and J. David Lee.)
-added possibility to preview an item. Useful if you work with tags.
-added import from SuperMemo7 text files (code thanks to Dirk Herrmann).
-either space, enter or return can be used to show the answer. The default
 answer grade is set to 4, which once again can be chosen by either space,
 enter or return (patch by Dirk Herrmann).
-importing of txt files in utf8 unicode encoding now works (patch by Ian 
 MacLean).
-exporting to txt files now uses utf8 encoding.
-the total number of items in the status bar now only takes into account
 items in active categories (patch by Mike Charlton).
-prevent infinite recursion when searching for an item that was recently 
 deleted.
-the titlebar now displays unicode filenames correctly.
-after the window expands to accomodate a large item, it will shrink 
 back again.
-fixed incorrect button text when switching databases.
-new grade 0/1 items will now be scheduled after existing grade 0/1 items.


MNEMOSYNE 0.9.5: 2006-08-03

*** IMPORTANT UPGRADE NOTICE ***

This version uses a different database format. Before upgrading, export your
old data as xml. After upgrade, create a new database and import the old data
from the xml file.

-databases can now be moved back and forth between Windows and Unix.
-added 'Reset learning data on export' option. This makes it easier to 
 create a file to share with other people.
-the database is now saved each time a new item is added.
-fixed a bug where exporting to txt always exported all categories
 (reported by Dariusz Laska).
-items which you forget will no longer be pushed out of the revision queue
 by items which you still need to learn.


MNEMOSYNE 0.9.4: 2006-06-04

- category names are now sorted alphabetically.
- relative path names now work for multiple img tags in the same string.
  (patch by J. David Lee).
- removed leftover debug code which could cause problems with Unicode 
  items.

MNEMOSYNE 0.9.3: 2006-05-25

- relative paths can now be used in img tags, i.e. &ltimg src="foo/bar.png">
  instead of &ltimg src="/home/johndoe/.mnemosyne/foo/bar.png">. Paths are
  relative to the location of the *.mem file.
- added ability to export to a txt file (only the questions and the 
  answers are exported).
- added locking mechanism which warns you if you start a second
  instance of the program, which could lead to data loss.
- fixed obscure button labelling bug (patch by J. David Lee).

MNEMOSYNE 0.9.2: 2006-03-25

*** IMPORTANT UPGRADE NOTICE ***

This version uses a different database format. Before upgrading, export your 
old data as xml. After upgrade, create a new database and import the old data
from the xml file.
	
- only a limited number of grade 0 items is moved to the learning queue
  at a single time. This is 5 by default, but can be set through the
  configuration screen
- added ability to import from tab separated text files (as exported e.g.
  by Excel)

MNEMOSYNE 0.9.1: 2006-02-09

- fixed bug where an item would get asked twice after editing
- fixed bug when using the popup menu on an empty spot

MNEMOSYNE 0.9: 2006-02-08

- first release of the new core.

</pre>

<?php
        include 'include/footer.php';
?>
