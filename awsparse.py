import sys, os
sys.path.append('/home/user/Documents/llvm-3.4/tools/clang/bindings/python/')
import clang.cindex

clang_index = clang.cindex.Index.create()
clang_args = ['-cc1', '-triple', 'x86_64-unknown-linux-gnu', '-emit-obj', '-mrelax-all', '-disable-free', '-mrelocation-model', 'static', '-mdisable-fp-elim', '-fmath-errno', '-masm-verbose', '-mconstructor-aliases', '-munwind-tables', '-fuse-init-array', '-target-cpu', 'x86-64', '-target-linker-version', '2.24', '-g', '-resource-dir', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/x86_64-linux-gnu', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/c++/4.8/backward', '-internal-isystem', '/usr/lib/gcc/x86_64-linux-gnu/4.8/../../../../include/x86_64-linux-gnu/c++/4.8', '-internal-isystem', '/usr/local/include', '-internal-isystem', '/home/user/Documents/llvm-3.4-build/Debug+Asserts/bin/../lib/clang/3.4/include', '-internal-externc-isystem', '/usr/include/x86_64-linux-gnu', '-internal-externc-isystem', '/include', '-internal-externc-isystem', '/usr/include', '-fdeprecated-macro', '-fdebug-compilation-dir', '/home/user/Documents/test/indirect_branch', '-ferror-limit', '19', '-fmessage-length', '97', '-mstackrealign', '-fobjc-runtime=gcc', '-fcxx-exceptions', '-fexceptions', '-fdiagnostics-show-option', '-vectorize-slp']

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
  def print_tokens(file_name, line, column):
    assert(file_name!=None)
    compile_unit = get_compile_unit(file_name)

    cursor = get_cursor(compile_unit, line, column)
    print_cursor_children(cursor, 1)
    
    for token in cursor.get_tokens():
      print "   %s - %s" % (token.spelling, token.kind)