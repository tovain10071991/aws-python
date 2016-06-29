import sys, os, enum, pdb
sys.path.append('/home/user/Documents/llvm-3.4/tools/clang/bindings/python/')
import clang.cindex
from clangargs import clang_args, h_args
clang_index = clang.cindex.Index.create()
# clang_args = ['-cc1', '-triple', 'x86_64-unknown-linux-gnu', '-emit-obj', '-mrelax-all', '-disable-free', '-mrelocation-model', 'static', '-mdisable-fp-elim', '-fmath-errno', '-masm-verbose', '-mconstructor-aliases', '-munwind-tables', '-fuse-init-array', '-target-cpu', 'x86-64', '-target-linker-version', '2.24', '-g', '-resource-dir', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/x86_64-linux-gnu', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/backward', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/x86_64-linux-gnu/c++/4.8', '-internal-isystem', '/usr/local/include', '-internal-isystem', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4/include', '-internal-externc-isystem', '/usr/include/x86_64-linux-gnu', '-internal-externc-isystem', '/include', '-internal-externc-isystem', '/usr/include', '-fdeprecated-macro', '-fdebug-compilation-dir', '/home/user/Documents/test/indirect_branch', '-ferror-limit', '19', '-fmessage-length', '97', '-mstackrealign', '-fobjc-runtime=gcc', '-fcxx-exceptions', '-fexceptions', '-fdiagnostics-show-option', '-vectorize-slp']

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
      output = "parsing source file: %s ..." % source_file
      sys.stderr.write(output + '\n')
      # sys.stderr.flush()
      args = []
      if(source_file in clang_args):
        args = clang_args[source_file]
      elif(source_file[-2:] == '.h'):
        args = h_args
      else:
        output = "clang_args not found: %s ..." % source_file
        sys.stderr.write(output + '\n')
        os.abort()
      compile_unit[source_file] = clang_index.parse(source_file, args, options = clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
      sys.stderr.write('parsing done\n')
    except clang.cindex.TranslationUnitLoadError as e:
      print ("an error occurred when creating compile unit: %s" % e)
      compile_unit[source_file] = None
  return compile_unit[source_file]

def get_cursor(file_name, line, column):
  # print "%s: %d, %d" % (file_name, line, column)
  output = "getting compile unit: %s ..." % file_name
  sys.stderr.write(output + '\n')
  # sys.stderr.flush()
  compile_unit = get_compile_unit(file_name)
  sys.stderr.write('getting done\n')
  if compile_unit is None:
    return None
  src_loc = clang.cindex.SourceLocation.from_position(compile_unit, compile_unit.get_file(file_name), line, column)
  cursor = clang.cindex.Cursor.from_location(compile_unit, src_loc)
  tmp_offset = cursor.extent.end.offset
  # if(tmp_offset == 0):
    # pdb.set_trace()
    # cursor = clang.cindex.Cursor.from_location(compile_unit, src_loc)
    
  while(1):
    tmp_src_loc = clang.cindex.SourceLocation.from_offset(compile_unit, compile_unit.get_file(file_name), tmp_offset)
    tmp_cursor = clang.cindex.Cursor.from_location(compile_unit, tmp_src_loc)
    if tmp_cursor.extent.start != cursor.extent.start:
      break
    cursor = tmp_cursor
    tmp_offset = tmp_offset + 1
  assert(cursor is not None)
  return cursor

def get_cursors(file_name, line, column):
  while(1):
    column = get_next_column(file_name, line, column)
    if column is None:
      break
    cursor = get_cursor(file_name, line, column)
    if cursor is None:
      break
    yield cursor
    if line != cursor.extent.end.line:
      break
    column = cursor.extent.end.column

def print_cursor_children(cursor, level):
  for i in range(0, level):
    print " ",
  ref_spelling = None
  ref_kind = None
  if cursor.referenced is not None:
    ref_spelling = cursor.referenced.spelling
    ref_kind = cursor.referenced.kind
  print "%s - %s - %s - ref: %s - %s" % (cursor.spelling, cursor.displayname, cursor.kind, ref_spelling, ref_kind)
  for child in cursor.get_children():
    print_cursor_children(child, level+1)

def parse_indirect_branch(cursor):
  IndirectBrKind = enum.Enum('IndirectBrKind', 'SWITCH VIRCALL CALLBACK VIRDESTRUCT UNKNOWN')
  # pdb.set_trace()
  if cursor.kind is clang.cindex.CursorKind.RETURN_STMT or cursor.kind is clang.cindex.CursorKind.DECL_STMT or cursor.kind is clang.cindex.CursorKind.VAR_DECL or cursor.kind is clang.cindex.CursorKind.UNARY_OPERATOR or cursor.kind is clang.cindex.CursorKind.COMPOUND_STMT or cursor.kind is clang.cindex.CursorKind.UNEXPOSED_EXPR or cursor.kind is clang.cindex.CursorKind.IF_STMT:
    ret = False
    for child in cursor.get_children():
      if parse_indirect_branch(child) is True:
        ret = True
    return ret
  elif cursor.kind is clang.cindex.CursorKind.SWITCH_STMT:
    # print "indirect branch kind: %s" % IndirectBrKind.SWITCH
    return True
  elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced is not None and (cursor.referenced.kind is clang.cindex.CursorKind.VAR_DECL or cursor.referenced.kind is clang.cindex.CursorKind.FIELD_DECL):
    output = "indirect branch kind: %s" % IndirectBrKind.CALLBACK
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced is not None and cursor.referenced.kind is clang.cindex.CursorKind.CXX_METHOD:
    output = "indirect branch kind: %s" % IndirectBrKind.VIRCALL
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CXX_DELETE_EXPR:
    output = "indirect branch kind: %s" % IndirectBrKind.VIRDESTRUCT
    sys.stderr.write(output + '\n')
    return True
  else:
    output = "indirect branch kind: %s" % IndirectBrKind.UNKNOWN
    sys.stderr.write(output + '\n')
    print "indirect branch kind: %s" % IndirectBrKind.UNKNOWN
    return False

class AwsParse(object):
  @staticmethod
  def print_cursors(file_name, line, column):
    assert(file_name!=None)
    for cursor in get_cursors(file_name, line, column):
      print_cursor_children(cursor, 1)
      
  @staticmethod
  def parse_indirect_branch(file_name, line, column):
    assert(file_name!=None)
    ret = False
    for cursor in get_cursors(file_name, line, column):
      output = "%s - %s - %s ..." % (cursor.spelling, cursor.displayname, cursor.kind)
      sys.stderr.write(output + '\n')
      # sys.stderr.flush()
      if parse_indirect_branch(cursor) is True:
        ret = True
    return ret