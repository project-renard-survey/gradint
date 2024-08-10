# This file is part of the source code of Gradint
# (c) Silas S. Brown.
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# This is the start of system.py - imports library modules, gets directory and extension separators, works out where temporary files go, etc.

macsound = (sys.platform.find("mac")>=0 or sys.platform.find("darwin")>=0)
cygwin = (sys.platform.find("cygwin")>=0)
mingw32 = sys.platform.find("mingw32")>=0
if not macsound and not cygwin and sys.platform.find("win")>=0: import winsound
else: winsound=None
riscos_sound = sys.platform.lower().find("riscos")>=0
try: import olpc # One Laptop Per Child module
except: olpc = 0

try: import appuifw # Symbian S60's GUI module
except: appuifw = 0
if appuifw:
    appuifw.app.body = appuifw.Text()
    appuifw.app.body.add(u""+program_name.replace("(c)","\n(c)")+"\n\nLoading, please wait...\n(Do NOT press OK or Cancel yet!)\n")
    import audio
    appuifw.app.title = u""+appTitle
    appuifw.app.screen='large' # lose Python banner
    import e32,time
    # S60 threads are awkward - callbacks run in a different thread and there's no way to interrupt main().  This is not as responsive as I'd like but it should do:
    def e32sleep(s):
        t=time.time()+s
        while time.time()<t:
            check_for_interrupts()
            e32.ao_sleep(min(1,t-time.time()))
    time.sleep = e32sleep
    def s60_interrupt():
        doLabel("Trying to interrupt main thread, please wait...")
        global need_to_interrupt
        need_to_interrupt = 1
    def s60_briefInt():
        global emergency_lessonHold_to
        if emergency_lessonHold_to:
            emergency_lessonHold_to = 0
            doLabel("Resuming...")
        else:
            emergency_lessonHold_to = time.time() + briefInterruptLength
            doLabel("Preparing to interrupt lesson... (select it again to resume)")
    appuifw.app.menu=[(u"Brief interrupt",s60_briefInt),(u"Cancel lesson",s60_interrupt)]
    appuifw.app.exit_key_handler = s60_interrupt

winCEsound = msvcrt = WMstandard = None
if winsound:
    try: import msvcrt
    except: msvcrt = None # missing
    if hasattr(os,"name") and os.name=="ce": # oops, this "Windows" is Windows CE
        winsound = None ; winCEsound = 1
        import ctypes # if that fails (pre-2.5, pre-Windows Mobile 2003) then we can't do much
        import ctypes.wintypes as wintypes
        class ShellExecuteInfo(ctypes.Structure): _fields_ = [("cbSize",wintypes.DWORD),("fMask",wintypes.ULONG),("hwnd",wintypes.HWND),("Verb",ctypes.c_wchar_p),("File",ctypes.c_wchar_p),("Parameters",ctypes.c_wchar_p),("Directory",ctypes.c_wchar_p),("nShow",ctypes.c_int),("hInstApp",wintypes.HINSTANCE),("IDList",ctypes.c_void_p),("Class",ctypes.c_wchar_p),("hkeyClass",wintypes.HKEY),("dwHotKey",wintypes.DWORD),("hIconOrMonitor",wintypes.HANDLE),("hProcess",wintypes.HANDLE)]
        try: ctypes.cdll.commdlg
        except: WMstandard = True

if macsound and __name__=="__main__": os.system("clear >&2") # so warnings etc start with a clear terminal (>&2 just in case using stdout for something else)
if riscos_sound: sys.stderr.write("Loading Gradint...\n") # in case it takes a while

try: import androidhelper as android
except:
  try: import android
  except: android = 0
if android:
    try: android = android.Android()
    except:
        print ("\n"*50+" *** Your SL4A server has crashed ***\n  Please restart SL4A\n  (or restart your phone)\n  and try running Gradint again.\n\n\n")
        raise SystemExit

wsp = '\t\n\x0b\x0c\r ' ; bwsp=B(wsp) # whitespace characters - ALWAYS use .strip(wsp) not .strip(), because someone added \xa0 (iso8859-1 no-break space) to string.whitespace on WinCE Python, and that can break processing of un-decoded UTF8 strings, e.g. a Chinese phrase ending "\xe5\x86\xa0"!  (and assign to string.whitespace does not work around this.)
# As .split() can't take alternative characters (and re-writing in Python is probably slow), just be careful with using it on un-decoded utf-8 stuff.  (split(None,1) is ok if 1st word won't end in an affected character)

warnings_printed = [] ; app = False # False is a hack for "maybe later"
warnings_toprint = []
def show_warning(w):
    if w+"\n" in warnings_printed: return
    if not app and not app==False and not appuifw and not android:
        if winCEsound and len(w)>100: w=w[:100]+"..." # otherwise can hang winCEsound's console (e.g. a long "assuming that" message from justSynthesize)
        sys.stderr.write(w+"\n")
    warnings_printed.append(w+"\n")
    if app==False: warnings_toprint.append(w) # may need to output them if app/appuifw/android turns out not to be created

def show_info(i,always_stderr=False):
    # == sys.stderr.write(i) with no \n and no error if closed (+ redirect to app or appuifw if exists)
    if (app or appuifw or android) and not always_stderr: return doLabel(i)
    if not riscos_sound and not always_stderr and hasattr(sys.stderr,"isatty") and not sys.stderr.isatty(): return # be quiet if o/p is being captured by cron etc (but isatty() might always return false on RISC OS
    if winCEsound and len(i)>101: i=i[:100]+"..."+i[-1] # otherwise can hang winCEsound's console
    if type(i)==type(u""): i=i.encode('utf-8')
    try: writeB(sys.stderr,i)
    except IOError: pass

# (TODO: GUI_translations, if not set in advanced.txt, won't work properly on pre-2.3 - it'll take them as Latin-1)
# (TODO: and if it *IS* set in advanced.txt, will 2.2's exec() correctly exec a unicode string?)

# Check if we're on big-endian architecture (relevant to sox etc)
try: import struct
except: struct=0
if struct and B(struct.pack("h",1)[0])==B('\x00'): big_endian = 1
else: big_endian = 0

# RISC OS has a different extension separator because "." is used as a directory separator (from the original 1982 BBC Micro DFS with 1-character directories)
if hasattr(os,'extsep'): extsep = os.extsep
elif riscos_sound: extsep = "/"
else: extsep = "."
dotwav = extsep+"wav" ; dotmp3 = extsep+"mp3" ; dottxt = extsep+"txt"
# and Python for S60 2.2 appends os.sep to getcwd() and crashes if you add another, so check:
cwd_addSep = os.sep
if os.getcwd()[-1]==os.sep: cwd_addSep = ""

def list2dict(l):
  d = {}
  for i in l: d[i]=True
  return d
try: list2set = set
except NameError: list2set = list2dict
def checkIn(k,obj):
    try: return k in obj # dict or set
    except:
        try: return obj.has_key(k) # Python 2.1 (may raise TypeError, AttributeError etc if try to use the "in" operator as above, but has_key rm'd from Python3)
        except: return obj.find(k) > -1 # Python 2.1 strings
try: object
except:
    class object: pass # Python 2.1

# settings.txt and advanced.txt
# (done here before the variables start to be used in
# defaults, top-level, etc)
# but check we're in the right directory (needed if launched
# via Mac OS Finder)
try:
    import os.path
    fileExists = os.path.isfile
    fileExists_stat = os.path.exists
    isDirectory = os.path.isdir
except: # os.path not included in the libraries - use this slower version:
    def fileExists(f):
        try:
            open(f)
            return 1
        except: return 0
    def fileExists_stat(f):
        try:
            os.stat(f)
            return 1
        except: return 0
    def isDirectory(directory):
        # or a symlink to a directory.  Do it this way to be safe:
        oldDir = os.getcwd()
        try:
            os.chdir(directory)
            ret = 1
        except: ret = 0 # was except OSError but some Python ports have been known to throw other things
        os.chdir(oldDir)
        return ret

use_unicode_filenames = winCEsound # needed to stop synth-cache being ??? (but do NOT use this on winsound, it's too unreliable)
if use_unicode_filenames:
    # pretend we still work in utf-8 for listdir etc (TODO this is not complete, but SampleEvent and PlayerInput will translate to Unicode also)
    oldOsListdir = os.listdir
    def listdir(d): return map(lambda x:x.encode('utf-8'),oldOsListdir(unicode(d,"utf-8")))
    os.listdir = listdir
    oldOsRename = os.rename
    def rename(o,n): return oldOsRename(unicode(o,"utf-8"),unicode(n,"utf-8"))
    os.rename = rename
    oldIsdir = isDirectory
    def isDirectory(d): return oldIsdir(unicode(d,"utf-8"))
    oldFileExistsStat = fileExists_stat
    def fileExists_stat(f): return oldFileExistsStat(unicode(f,"utf-8"))

def u8strip(d):
    global last_u8strip_found_BOM ; last_u8strip_found_BOM = 0
    d = B(d)
    if d.startswith(LB('\xef\xbb\xbf')):
        last_u8strip_found_BOM = 1
        return d[3:] # ignore Notepad's UTF-8 BOM's
    else: return d
def bwspstrip(s):
    try: return s.strip(bwsp)
    except: return s.strip() # Python 2.1
def wspstrip(s):
    try: return s.strip(wsp)
    except: return s.strip() # Python 2.1
GUI_translations_old = GUI_translations
configFiles = map(lambda x:x+dottxt,["advanced","settings"]) # MUST have settings last so can have per-user override of scriptVariants
if not hasattr(sys,"argv"): sys.argv=" " # some Symbian versions
starting_directory = os.getcwd()
if not fileExists(configFiles[0]):
  if macsound and checkIn("_",os.environ):
    s=os.environ["_"] ; s=s[:s.rfind(os.sep)]
    os.chdir(s)
    if not fileExists(configFiles[0]):
        # try up 1 more level (in case gradint.py has been hidden in start-gradint.app directory on Mac OS)
        s=s[:s.rfind(os.sep)]
        os.chdir(s)
  if not fileExists(configFiles[0]) and sys.argv and (os.sep in sys.argv[0] or (os.sep=='\\' and '/' in sys.argv[0])):
    # try the sys.argv[0] directory, in case THAT works
    if os.sep=="\\" and '/' in sys.argv[0] and fileExists(sys.argv[0].replace('/','\\')): sys.argv[0]=sys.argv[0].replace('/','\\') # hack for some Windows Python builds accepting slash in command line but reporting os.sep as backslash
    os.chdir(starting_directory)
    os.chdir(sys.argv[0][:sys.argv[0].rfind(os.sep)])
  if not fileExists(configFiles[0]): # argv[0] might be a symlink
    os.chdir(starting_directory)
    try: rp = os.path.realpath(sys.argv[0])
    except: rp = 0 # e.g. no os.path, or no os.path.realpath
    if rp: os.chdir(rp[:rp.rfind(os.sep)])
  if not fileExists(configFiles[0]):
    # Finally, try the module pathname, in case some other Python program has imported us without changing directory.  Apparently we need to get this from an exception.
    try: raise 0
    except:
      tbObj = sys.exc_info()[2]
      while tbObj and hasattr(tbObj,"tb_next") and tbObj.tb_next: tbObj=tbObj.tb_next
      if tbObj and hasattr(tbObj,"tb_frame") and hasattr(tbObj.tb_frame,"f_code") and hasattr(tbObj.tb_frame.f_code,"co_filename") and os.sep in tbObj.tb_frame.f_code.co_filename:
        os.chdir(starting_directory)
        try: os.chdir(tbObj.tb_frame.f_code.co_filename[:tbObj.tb_frame.f_code.co_filename.rfind(os.sep)])
        except: pass

# directory should be OK by now
if sys.platform.find("ymbian")>-1: sys.path.insert(0,os.getcwd()+os.sep+"lib")
import time,sched,random,math,pprint,codecs

def exc_info(inGradint=True):
    import sys # in case it's been gc'd
    w = str(sys.exc_info()[0])
    if "'" in w: w=w[w.index("'")+1:w.rindex("'")]
    if '.' in w: w=w[w.index(".")+1:]
    if sys.exc_info()[1]: w += (": "+str(sys.exc_info()[1]))
    tbObj = sys.exc_info()[2]
    while tbObj and hasattr(tbObj,"tb_next") and tbObj.tb_next: tbObj=tbObj.tb_next
    if tbObj and hasattr(tbObj,"tb_lineno"): w += (" at line "+str(tbObj.tb_lineno))
    if inGradint:
        if tbObj and hasattr(tbObj,"tb_frame") and hasattr(tbObj.tb_frame,"f_code") and hasattr(tbObj.tb_frame.f_code,"co_filename") and not tbObj.tb_frame.f_code.co_filename.find("gradint"+extsep+"py")>=0: w += (" in "+tbObj.tb_frame.f_code.co_filename)
        else: w += (" in "+program_name[:program_name.index("(c)")])
        w += " on Python "+sys.version.split()[0]+"\n"
    del tbObj
    return w

def read(fname): return open(fname,"rb").read()
def write(fname,data): open(fname,"wb").write(data)
def readSettings(f):
   try: fdat = u8strip(read(f)).replace(B("\r"),B("\n"))
   except: return show_warning("Warning: Could not load "+f)
   try: fdat = unicode(fdat,"utf-8")
   except: return show_warning("Problem decoding utf-8 in "+f)
   try: exec(fdat,globals())
   except: show_warning("Error in "+f+" ("+exc_info(False)+")")
synth_priorities = "eSpeak MacOS SAPI Ekho" # old advanced.txt had this instead of prefer_espeak; we can still support it
dir1 = list2set(dir()+["dir1","f","last_u8strip_found_BOM","__warningregistry__"])
for f in configFiles: readSettings(f)
for d in dir():
  if not checkIn(d,dir1) and eval(d) and not type(eval(d))==type(lambda *args:0): # (ignore unrecognised options that evaluate false - these might be an OLD unused option with a newer gradint rather than vice versa; also ignore functions as these could be used in command-line parameters)
    show_warning("Warning: Unrecognised option in config files: "+d)
del dir1
GUI_translations_old.update(GUI_translations) ; GUI_translations = GUI_translations_old # in case more have been added since advanced.txt last update

def cond(a,b,c):
    if a: return b
    else: return c

unix = not (winsound or mingw32 or riscos_sound or appuifw or android or winCEsound)
if unix: os.environ["PATH"] = os.environ.get("PATH","/usr/local/bin:/usr/bin:/bin")+cond(macsound,":"+os.getcwd()+"/start-gradint.app:",":")+os.getcwd() # for qtplay and sox, which may be in current directory or may be in start-gradint.app if it's been installed that way, and for lame etc.  Note we're specifying a default PATH because very occasionally it's not set at all when using 'ssh system command' (some versions of DropBear?)

# Any options in the environment?
env=os.environ.get("Gradint_Extra_Options","")
while env.endswith(";"): env=env[:-1]
while env.startswith(";"): env=env[1:]
if env: exec(env)
# and anything on the command line?
if len(sys.argv)>1:
    runInBackground=0 # NOT useTK=0 because there might not be a console on Win/GUI or Mac
    progressFileBackup=logFile=None
    exec(" ".join(sys.argv[1:]))

# Paranoid file management option.  Can't go any earlier than this because must parse advanced.txt first.
if paranoid_file_management:
  # For ftpfs etc.  Retry on errno 13 (permission denied), and turn append into a copy.  Otherwise occasionally get vocab.txt truncated.
  _old_open = open
  def tryIO(func):
    for tries in list(range(10))+["last"]:
        try: return func()
        except IOError:
            err = sys.exc_info()[1]
            if tries=="last" or not err.errno in [5,13,None]: raise
            time.sleep(0.5)
  def read(file): return tryIO(lambda x=file:_old_open(x,"rb").read())
  def _write(fn,data):
    tryIO(lambda x=fn,y=data:_old_open(x,"wb").write(y))
    time.sleep(0.5)
    if not filelen(fn)==len(data):
      # might be a version of curlftpfs that can't shorten files - try delete and restart (although this can erase permissions info)
      os.remove(fn)
      tryIO(lambda x=fn,y=data:_old_open(x,"wb").write(y))
      if not filelen(fn)==len(data): raise IOError("wrong length")
    if not read(fn)==data: raise IOError("verification failure on "+repr(fn))
  def write(fn,data): return tryIO(lambda x=fn,y=data:_write(x,y))
  def open(file,mode="r",forAppend=0):
    if "a" in mode:
        try: dat = open(file,"rb").read()
        except IOError:
            err = sys.exc_info()[1]
            if err.errno==2: dat = "" # no such file or directory
            else: raise
        if len(dat) < filelen(file): raise IOError("short read")
        try: os.rename(file,file+"~") # just in case!
        except: pass
        o=open(file,"wb",1)
        o.write(dat)
        return o
    r=tryIO(lambda x=file,m=mode:_old_open(x,m))
    if "w" in mode and not forAppend and filelen(file): # it's not truncating (see _write above)
        r.close()
        os.unlink(file)
        r=tryIO(lambda x=file,m=mode:_old_open(x,m))
    return r

if seedless: random.seed(0)

# Different extension separators again
if not extsep==".":
    # only do the below if defaults haven't been changed
    if progressFile=="progress.txt": progressFile=progressFile.replace(".",extsep)
    if vocabFile=="vocab.txt": vocabFile=vocabFile.replace(".",extsep)
    if progressFileBackup=="progress.bak": progressFileBackup=progressFileBackup.replace(".",extsep)
    if pickledProgressFile=="progress.bin": pickledProgressFile=pickledProgressFile.replace(".",extsep)
    if logFile=="log.txt": logFile=logFile.replace(".",extsep)
    if userNameFile=="username.txt": userNameFile=userNameFile.replace(".",extsep)
# End of extension-separator stuff

# Check for a script changing progressFile but forgetting to change pickledProgressFile to match
oldDir=None
for p in [progressFile,progressFileBackup,pickledProgressFile]:
    if not p: continue
    if os.sep in p: p=(p[:p.rfind(os.sep)+1],p[p.rfind(os.sep)+1:])
    else: p=("",p)
    if extsep in p[1]: p=(p[0],p[1][:p[1].rfind(extsep)]) # here rather than earlier to cover cases where extsep is in a directory name but not in the filename
    if oldDir==None: oldDir=p
    elif not oldDir==p:
        sys.stderr.write("ERROR: progressFile, progressFileBackup and pickledProgressFile, if not None, must have same directory and major part of filename.  Gradint will not run otherwise.  This coherence check was added in case some script sets progressFile to something special but forgets to set the others.\n")
        sys.exit(1)

# Check for RISC OS pre-1970 clock problem (actually quite likely if testing on the rpcemu emulator without setting the clock)
if riscos_sound and hex(int(time.time())).find("0xFFFFFFFF")>=0 and not outputFile:
    sys.stderr.write("ERROR: time.time() is not usable - gradint cannot run interactively.\n")
    sys.stderr.write("This error can be caused by the RISC OS clock being at 1900 (the Unix time functions start at 1970).\nClose this task window, set the clock and try again.\n")
    sys.exit()

# Check for WinCE low memory (unless we're a library module in which case it's probably ok - reader etc)
# NB on some systems this has been known to false alarm (can't allocate 15M even when there's 70M+ of program memory ??) so set a flag and ask Y/N later when got Tk
if winCEsound and __name__=="__main__":
  m1=m2=m3=0
  try:
    m1=chr(0)*5000000
    m2=chr(0)*5000000
    m3=chr(0)*5000000
    del m1,m2,m3
  except MemoryError:
    del m1,m2,m3
    ceLowMemory=1

# Check for Mac OS Tk problem
Tk_might_display_wrong_hanzi = wrong_hanzi_message = "" ; forceRadio=0
if macsound:
  try: os.remove("_tkinter.so") # it might be an old patched version for the wrong OS version
  except: pass
  def tkpatch(): # (called only on specific older versions of Mac OS X) patch Mac OS Tk to the included v8.6 (as v8.4 on OS10.5 has hanzi problem and v8.5 on 10.6 has fontsize problems etc)
    f="/System/Library/Frameworks/Python.framework/Versions/"+sys.version[:3]+"/lib/python"+sys.version[:3]+"/lib-dynload/_tkinter.so"
    if fileExists(f): # we might be able to patch this one up
     if not isDirectory("Frameworks") and fileExists("Frameworks.tbz"): os.system("tar -jxvf Frameworks.tbz && rm Frameworks.tbz && chmod -R +w Frameworks")
     if isDirectory("Frameworks"):
      if not fileExists("_tkinter.so"): open("_tkinter.so","w").write(read(f).replace("/System/Library/Frameworks/T","/tmp/gradint-Tk-Frameworks/T").replace("/Versions/8.4/","/Versions/8.6/").replace("/Versions/8.5/","/Versions/8.6/"))
      os.system('ln -fs "$(pwd)/Frameworks" /tmp/gradint-Tk-Frameworks') # must be same length as /System/Library/Frameworks
      sys.path.insert(0,os.getcwd()) ; import _tkinter ; del sys.path[0]
      _tkinter.TK_VERSION = _tkinter.TCL_VERSION = "8.6"
      return True
  if not os.environ.get("VERSIONER_PYTHON_PREFER_32_BIT","no")=="no": # needed at least on 10.6 (so if run from cmd line w/out this setting, don't try this patch)
    if sys.version.startswith("2.3.5"): Tk_might_display_wrong_hanzi="10.4"
    elif sys.version[:5] == "2.5.1": # 10.5
      if not tkpatch(): Tk_might_display_wrong_hanzi="10.5"
    elif sys.version[:5] == "2.6.1": tkpatch() # 10.6 (still has Tk8.5, hanzi ok but other problems)
    elif sys.version[:5] == "2.7.5": tkpatch() # 10.9 (problems with "big print" button if don't do this)
  if Tk_might_display_wrong_hanzi: wrong_hanzi_message = "NB: In Mac OS "+Tk_might_display_wrong_hanzi+", Chinese\ncan display wrongly here." # so they don't panic when it does

# Handle keeping progress file and temp directories etc if we're running from a live CD
# (and if the live CD has just been copied to the hard disk, look in the old progress file locations also)

def progressFileOK():
    try:
        open(progressFile) ; return 1
    except IOError:
        try:
            open(progressFile,"w") ; os.unlink(progressFile)
            return 1
        except: return 0
if winsound:  # will try these dirs in reverse order:
    tryList = ["C:\\TEMP\\gradint-progress.txt", "C:\\gradint-progress.txt", "C:gradint-progress.txt"]
    if checkIn("HOMEDRIVE",os.environ) and checkIn("HOMEPATH",os.environ): tryList.append(os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]+os.sep+"gradint-progress.txt")
elif checkIn("HOME",os.environ): tryList=[os.environ["HOME"]+os.sep+"gradint-progress.txt"]
elif riscos_sound: tryList=["$.gradint-progress/txt"]
else: tryList = []
foundPF = okPF = 0 ; defaultProgFile = progressFile
while not foundPF:
    if fileExists(progressFile):
        foundPF = okPF = progressFile ; break
    elif (not okPF) and progressFileOK(): okPF = progressFile   # (but carry on looking for an existing one)
    if not tryList: break # (NOT elif!)
    progressFile = tryList.pop()
if foundPF: progressFile=foundPF
elif okPF: progressFile=okPF
else: show_warning("WARNING: Could not find a writable directory for progress.txt and temporary files\nExpect problems!")
need_say_where_put_progress = (not progressFile==defaultProgFile)
if need_say_where_put_progress:
    progressFileBackup = progressFile[:-3]+"bak"
    pickledProgressFile = progressFile[:-3]+"bin"
    logFile = None # for now
tempdir_is_curdir = False
if winsound or winCEsound or mingw32 or riscos_sound or not hasattr(os,"tempnam") or android:
    tempnam_no = 0
    if os.sep in progressFile: tmpPrefix=progressFile[:progressFile.rindex(os.sep)+1]+"gradint-tempfile"
    else: tmpPrefix,tempdir_is_curdir="gradint-tempfile",True
    if winCEsound or ((winsound or mingw32) and not os.sep in tmpPrefix and not tmpPrefix.startswith("C:")):
        # put temp files in the current directory, EXCEPT if the current directory contains non-ASCII characters then check C:\TEMP and C:\ first (just in case the non-ASCII characters create problems for command lines etc; gradint *should* be able to cope but it's not possible to test in advance on *everybody's* localised system so best be on the safe side).  TODO check for quotes etc in pathnames too.
        def isAscii():
          for c in os.getcwd():
            if c<' ' or c>chr(127): return False
          return True
        tmpPrefix = None
        if winCEsound or not isAscii():
            # WinCE: If a \Ramdisk has been set up, try that first.  (Could next try storage card if on WM5+ to save hitting internal flash, but that would be counterproductive on WM2003, and anyway the space in the pathname would be awkward.)
            for t in cond(winCEsound,["\\Ramdisk\\","\\TEMP\\", "\\"],["C:\\TEMP\\", "C:\\"]):
                try:
                    open(t+"gradint-tempfile-test","w")
                    os.unlink(t+"gradint-tempfile-test")
                except: continue
                tmpPrefix,tempdir_is_curdir = t,False ; break
        if not tmpPrefix: tmpPrefix = os.getcwd()+os.sep
        tmpPrefix += "gradint-tempfile"
    def tempnam():
        global tempnam_no ; tempnam_no += 1
        return tmpPrefix+str(tempnam_no)
    os.tempnam = os.tmpnam = tempnam
elif (macsound or sys.platform.lower().find("bsd")>0) and os.environ.get("TMPDIR",""): # BSD tempnam uses P_tmpdir instead, override
    tempnam0 = os.tempnam
    os.tempnam=lambda *args:tempnam0(os.environ["TMPDIR"])

if disable_once_per_day==1:
  if once_per_day==3: sys.exit()
  else: once_per_day=0
if once_per_day&2 and not hasattr(sys,"_gradint_innerImport"): # run every day
    currentDay = None
    # markerFile logic to avoid 2+ background copies (can't rely on taskkill beyond WinXP)
    myID = str(time.time())
    try: myID += str(os.getpid())
    except: pass
    markerFile="background"+dottxt
    open(markerFile,"w").write(myID)
    def reador0(f):
        try: return read(f)
        except: return 0
    while reador0(markerFile)==myID:
     if not currentDay == time.localtime()[:3]: # first run of day
      currentDay = time.localtime()[:3]
      if __name__=="__main__": # can do it by importing gradint
        sys._gradint_innerImport = 1
        try: reload(gradint)
        except NameError: import gradint
        gradint.orig_onceperday = once_per_day
        try: gradint.main()
        except SystemExit: pass
      elif winsound and fileExists("gradint-wrapper.exe"): # in this setup we can do it by recursively calling gradint-wrapper.exe
        s=" ".join(sys.argv[1:])
        if s: s += ";"
        s += "once_per_day="+str(once_per_day-2)+";orig_onceperday="+str(once_per_day)
        s="gradint-wrapper.exe "+s
        if fileExists_stat("tcl"): os.popen(s).read() # (looks like we're a GUI setup; start /wait will probably pop up an undesirable console if we're not already in one)
        else: os.system("start /wait "+s) # (NB with "start", can't have quotes around 1st part of the program, as XP 'start' will treat it as a title, but if add another title before it then Win9x will fail)
      else:
        show_warning("Not doing once_per_day&2 logic because not running as main program")
        # (DO need to be able to re-init the module - they might change advanced.txt etc)
        break
      if len(sys.argv)>1: sys.argv.append(";")
      sys.argv.append("disable_once_per_day=0") # don't let a disable_once_per_day=2 in argv result in repeated questioning
     time.sleep(3600) # delay 1 hour at a time (in case hibernated)
if once_per_day&1 and fileExists(progressFile) and time.localtime(os.stat(progressFile).st_mtime)[:3]==time.localtime()[:3]: sys.exit() # already run today
try: orig_onceperday
except: orig_onceperday=0

if winsound:
    # check for users putting support files/folders in the desktop shortcuts folder and thinking it's the gradint folder
    # We can't do much about detecting users on non-English Windows who have heeded the warning about moving the "Desktop" folder to the real desktop but then mistook this for the gradint folder when adding flite (but hopefully they'll be using ptts/espeak anyway, and yali has an installer)
    if checkIn("HOMEDRIVE",os.environ) and checkIn("HOMEPATH",os.environ): dr=os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"]
    else: dr="C:\\Program Files" # as setup.bat (location for gradint on Win95 etc)
    if checkIn("USERPROFILE",os.environ): dr=os.environ["USERPROFILE"]
    if not dr[-1]=="\\": dr += "\\"
    try: dirList = os.listdir(dr+"Desktop\\gradint\\") # trailing \ important, otherwise it can include gradint.zip etc on Desktop
    except: dirList = []
    for d in dirList:
        if not d.endswith(".bat"): show_warning("WARNING: The file or folder '%s'\nwas found in the desktop shortcuts folder,\nwhich is NOT the gradint folder.\nThe gradint folder is: %s\nIf you meant '%s' to be used by gradint,\nplease move it to %s\n" % (d,os.getcwd(),d,os.getcwd()))
elif macsound:
    # Handle Mac upgrades.  Windows upgrades are done by setup.bat, but on the Mac if the Finder unpacks a second gradint.tbz we will be in "Gradint 2.app" (which is why there's a "Gradint 2" script in Contents/MacOS).
    if os.getcwd().endswith("/Gradint 2.app") and fileExists_stat("../Gradint.app"):
       for toKeep in "vocab.txt settings.txt advanced.txt".split():
          if fileExists_stat(toKeep) and fileExists_stat("../Gradint.app/"+toKeep): os.remove(toKeep)
       os.system('cp -fpr * ../Gradint.app/')
       open("deleteme","w")
       os.system('open ../Gradint.app')
       sys.exit(0)
    elif fileExists_stat("../Gradint 2.app/deleteme"):
       try: import thread
       except ImportError: import _thread as thread
       thread.start_new_thread(lambda *x:(time.sleep(2),os.system('rm -rf "../Gradint 2.app"')),())

def got_program(prog):
    if winsound:
        if fileExists(prog+".exe"): return prog+".exe"
    elif riscos_sound:
        if prog[:1]=="*": # module
            os.system("help "+prog[1:]+" { > _tstCmd_ }")
            got = open("_tstCmd_").read().find(prog[1:].upper())>-1
            os.unlink("_tstCmd_") ; return got
        return checkIn("Alias$"+prog,os.environ) # works in Python 3.8 but not 2.7 (Alias$ vars hidden)
    elif unix:
        try:
            try: from shutil import which as find_executable # PEP 632
            except: from distutils.spawn import find_executable
            if (":"+os.environ.get("PATH","")).find(":.")>-1:
                prog = find_executable(prog)
            else: # at least some distutils assume that "." is in the PATH even when it isn't, so do it ourselves without checking "."
                oldCwd = os.getcwd()
                pList = os.environ.get("PATH","").split(':')
                if pList:
                  done=0
                  for p in pList:
                    try: os.chdir(p)
                    except: continue
                    done=1 ; break
                  if done:
                    prog = find_executable(prog)
                    os.chdir(oldCwd)
        except ImportError:
            # fall back to running 'which' in a shell (probably slower if got_program is called repeatedly)
            prog = wspstrip(os.popen("which "+prog+" 2>/dev/null").read())
            if not fileExists_stat(prog): prog=None # some Unix 'which' output an error to stdout instead of stderr, so check the result exists
        return prog

def win2cygwin(path): # convert Windows path to Cygwin path
    if path[1]==":": return "/cygdrive/"+path[0].lower()+path[2:].replace("\\","/")
    else: return path.replace("\\","/") # TODO what if it STARTS with a \ ?
if winsound or mingw32: programFiles = os.environ.get("ProgramFiles","C:\\Program Files")
elif cygwin: programFiles = win2cygwin(os.environ.get("PROGRAMFILES","C:\\Program Files"))

def mysleep(secs):
    # In some Python distributions, time.sleep() will sleep about 1.01% too long.
    # That's not normally a problem for lessons (the scheduler compensates afterwards), but it can be a problem if using gradint for reminders - 1% extra on a 9-hour delay could make a reminder 5 minutes late (this happens on an NSLU2 running Debian Etch for example)
    # Let's work around it by reducing long delays slightly (sched will call sleep again if necessary)
    if secs>60: secs *= 0.95
    if emulated_interruptMain or winCEsound:
        t=time.time()+secs
        while time.time()<t:
            if emulated_interruptMain: check_for_interrupts()
            if winCEsound: ctypes.cdll.coredll.SystemIdleTimerReset()
            time.sleep(max(0,min(1,t-time.time())))
    else: time.sleep(secs)

emulated_interruptMain = (appuifw or winCEsound) # for now (will add 1 if we import thread and find it doesn't have an interrupt_main)
# (OK so the "emulated_interruptMain or winCEsound" will be redundant above, but keep it anyway in case we ever get a real interrupt_main on WinCE)

need_to_interrupt = 0
def check_for_interrupts(): # used on platforms where thread.interrupt_main won't work
    global need_to_interrupt
    if need_to_interrupt:
        need_to_interrupt = 0
        raise KeyboardInterrupt

# If forking, need to do so BEFORE importing any Tk module (we can't even verify Tk exists 1st)
if outputFile or justSynthesize or appuifw or not (winsound or winCEsound or mingw32 or macsound or riscos_sound or cygwin or checkIn("DISPLAY",os.environ)): useTK = 0
if useTK and runInBackground and not (winsound or mingw32) and hasattr(os,"fork") and not checkIn("gradint_no_fork",os.environ):
    if os.fork(): sys.exit()
    os.setsid()
    if os.fork(): sys.exit()
    devnull = os.open("/dev/null", os.O_RDWR)
    for fd in range(3): os.dup2(devnull,fd)
else: runInBackground = 0

try: import readline # enable readline editing of raw_input()
except: readline=0

try: import cPickle as pickle
except:
  try: import pickle
  except: pickle = None
try: import re
except: re = None
try:
    import gc
    gc.disable() # slight speedup (assume gradint won't create reference loops)
except: pass

# make sure unusual locale settings don't make .lower() change utf-8 bytes by mistake:
try:
  import locale
  locale.setlocale(locale.LC_ALL, 'C')
except: pass
if not LB('\xc4').lower()==LB('\xc4'): # buggy setlocale (e.g. S60) can create portability issues with progress files
  lTrans=B("").join([chr(c) for c in range(ord('A'))]+[chr(c) for c in range(ord('a'),ord('z')+1)]+[chr(c) for c in range(ord('Z')+1,256)])
  def lower(s): return s.translate(lTrans) # (may crash if Unicode)
else:
  def lower(s): return s.lower()

# -------------------------------------------------------
