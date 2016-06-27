import sys, os, enum, pdb
sys.path.append('/home/user/Documents/llvm-3.4/tools/clang/bindings/python/')
import clang.cindex

clang_index = clang.cindex.Index.create()
clang_args = ['-cc1', '-triple', 'x86_64-unknown-linux-gnu', '-emit-obj', '-mrelax-all', '-disable-free', '-mrelocation-model', 'static', '-mdisable-fp-elim', '-fmath-errno', '-masm-verbose', '-mconstructor-aliases', '-munwind-tables', '-fuse-init-array', '-target-cpu', 'x86-64', '-target-linker-version', '2.24', '-g', '-resource-dir', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/x86_64-linux-gnu', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/backward', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/x86_64-linux-gnu/c++/4.8', '-internal-isystem', '/usr/local/include', '-internal-isystem', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4/include', '-internal-externc-isystem', '/usr/include/x86_64-linux-gnu', '-internal-externc-isystem', '/include', '-internal-externc-isystem', '/usr/include', '-fdeprecated-macro', '-fdebug-compilation-dir', '/home/user/Documents/test/indirect_branch', '-ferror-limit', '19', '-fmessage-length', '97', '-mstackrealign', '-fobjc-runtime=gcc', '-fcxx-exceptions', '-fexceptions', '-fdiagnostics-show-option', '-vectorize-slp']

def skip_white_space(line_content):
  column = 1
  while(1):
    ch = line_content[column]
    if(ch.isspace() is False):
      break
  column = column + 1      
  return column

def truncate_end_space(line_content):
  i = len(line_content) - 1
  while(line_content[i].isspace()):
    i = i - 1
  return line_content[0:i+1]

def get_next_column(file_name, line, column):
  column = column + 1
  fp = open(file_name, 'r')
  i = 0
  for i in range(1, line):
    fp.readline()
  line_content = fp.readline()
  line_content = truncate_end_space(line_content)
  if(column > len(line_content)):
    return None
  
  while(1):
    ch = line_content[column-1]
    if(ch.isspace() is False):
      break
  column = column + 1      
  return column

compile_unit = {}

def get_compile_unit(source_file):
  global compile_unit
  if not source_file in compile_unit:
    try:
      compile_unit[source_file] = clang_index.parse(source_file, clang_args)
    except clang.cindex.TranslationUnitLoadError as e:
      print ("an error occurred when creating compile unit: %s" % e)
      os.abort()
  return compile_unit[source_file]

def get_cursor(compile_unit, line, column):
  src_loc = clang.cindex.SourceLocation.from_position(compile_unit, compile_unit.get_file(compile_unit.spelling), line, column)
  cursor = clang.cindex.Cursor.from_location(compile_unit, src_loc)
  tmp_offset = cursor.extent.end.offset
  while(1):
    tmp_src_loc = clang.cindex.SourceLocation.from_offset(compile_unit, compile_unit.get_file(compile_unit.spelling), tmp_offset)
    tmp_cursor = clang.cindex.Cursor.from_location(compile_unit, tmp_src_loc)
    if tmp_cursor.extent.start != cursor.extent.start:
      break
    cursor = tmp_cursor
    tmp_offset = tmp_offset + 1
  return cursor

def get_cursors(compile_unit, line, column):
  while(1):
    column = get_next_column(compile_unit.spelling, line, column)
    if column is None:
      break;
    cursor = get_cursor(compile_unit, line, column)
    yield cursor
    if line != cursor.extent.end.line:
      break
    column = cursor.extent.end.column

def print_cursor_children(cursor, level):
  for i in range(0, level):
    print " ",
  def_spelling = None
  def_kind = None
  if cursor.get_definition() is not None:
    def_spelling = cursor.get_definition().spelling
    def_kind = cursor.get_definition().kind
  print "%s - %s - %s - def: %s - %s" % (cursor.spelling, cursor.displayname, cursor.kind, def_spelling, def_kind)
  for child in cursor.get_children():
    print_cursor_children(child, level+1)

class AwsParse(object):
  @staticmethod
  def print_cursors(file_name, line, column):
    assert(file_name!=None)
    compile_unit = get_compile_unit(file_name)

    for cursor in get_cursors(compile_unit, line, column):
      print_cursor_children(cursor, 1)
      
  @staticmethod
  def parse_indirect_branch(file_name, line, column):
  
    IndirectBrKind = enum.Enum('IndirectBrKind', 'SWITCH VIRCALL CALLBACK VIRDESTRUCT UNKNOWN')
  
    assert(file_name!=None)
    compile_unit = get_compile_unit(file_name)
    for cursor in get_cursors(compile_unit, line, column):
      print "indirect branch kind: ",
      if cursor.kind is clang.cindex.CursorKind.SWITCH_STMT:
        print IndirectBrKind.SWITCH
      elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced.kind is clang.cindex.CursorKind.VAR_DECL:
        print IndirectBrKind.CALLBACK
      elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced.kind is clang.cindex.CursorKind.CXX_METHOD:
        print IndirectBrKind.VIRCALL
      elif cursor.kind is clang.cindex.CursorKind.CXX_DELETE_EXPR:
        print IndirectBrKind.VIRDESTRUCT
      else:
        print IndirectBrKind.UNKNOWN