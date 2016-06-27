import sys
sys.path.append('/home/user/Documents/llvm-3.4-build/Debug+Asserts/lib/python2.7/site-packages/')
import lldb

class AwsDbg(object):
  def __init__(self, executable):
    lldb.SBDebugger.Initialize()
    self.debugger = lldb.SBDebugger.Create()
    self.debugger.SetAsync(False)
    
    self.target = self.debugger.CreateTargetWithFileAndArch(executable, lldb.LLDB_ARCH_DEFAULT)
    assert(self.target.IsValid())
    main_bp = self.target.BreakpointCreateByName('main', self.target.GetExecutable().GetFilename())
    assert(main_bp.IsValid())
    error = lldb.SBError()
    self.target.Launch(lldb.SBLaunchInfo(None), error)
    assert(error.Success())
  
  def __del__(self):
    lldb.SBDebugger.Destroy(self.debugger)
  
  def get_source_code(self, address):
    load_addr = lldb.SBAddress(address, self.target)
    line_entry = load_addr.GetLineEntry()
    if(line_entry.GetFileSpec().IsValid()):
      stream = lldb.SBStream()
      src_mgr = self.debugger.GetSourceManager()
      src_mgr.DisplaySourceLinesWithLineNumbers(line_entry.GetFileSpec(), line_entry.GetLine(), 2, 2, '=>', stream)
      print('%s' % stream.GetData())
    else:
      print("   have no debug info")