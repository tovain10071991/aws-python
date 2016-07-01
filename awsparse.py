import sys, os, enum, pdb, collections
sys.path.append('/home/user/Documents/llvm-3.4/tools/clang/bindings/python/')
import clang.cindex
from clangargs import clang_args, h_args
clang_index = clang.cindex.Index.create()
import awsctags

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

def get_end_column(file_name, line):
  fp = open(file_name, 'r')
  i = 0
  for i in range(1, line):
    fp.readline()
  line_content = fp.readline()
  line_content = truncate_end_space(line_content)
  column = len(line_content)
  fp.close()
  return column

compile_unit = {}
recent_unit = collections.deque()
ast_cache_dir = '/mnt/sdb/test/analysis_indirect_branch_compare_with_source/ast/'

def convert_to_ast(file_name):
  list = file_name.split('/')
  ast_file = ast_cache_dir + 'ast'
  for ele in list:
    ast_file = ast_file + '-' + ele
  return ast_file

def get_compile_unit(source_file):
  global compile_unit
  if not source_file in compile_unit:
    output = "the size of compile_unit set: %d\n" % len(compile_unit)
    sys.stderr.write(output)
    if(len(recent_unit)==15):
      unrecent = recent_unit.popleft()
      output = "delete compile_unit: %s\n" % unrecent
      sys.stderr.write(output)
      del compile_unit[unrecent]
    output = "read ast file: %s ..." % source_file
    sys.stderr.write(output + '\n')
    ast_file = convert_to_ast(source_file)
    if(os.access(ast_file, os.F_OK)):
      try:
        compile_unit[source_file] = clang_index.read(ast_file)
        sys.stderr.write('reading done\n')
        recent_unit.append(source_file)
        return compile_unit[source_file]
      except:
        output = "an error occurred when reading ast and try parsing: %s\n" % e
        sys.stderr.write(output)
    sys.stderr.write("reading ast failed and try parsing\n")
    try:
      output = "parsing source file: %s ..." % source_file
      sys.stderr.write(output + '\n')
      # sys.stderr.flush()
      args = []
      if(source_file in clang_args):
        args = clang_args[source_file]
      elif(source_file[-2:] == '.h'):
        args = h_args
      elif(source_file[-4:] == '.inc'):
        return None
      else:
        output = "clang_args not found: %s ..." % source_file
        sys.stderr.write(output + '\n')
        os.abort()
      compile_unit[source_file] = clang_index.parse(source_file, args, options =   clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
      sys.stderr.write('parsing done\n')
      assert(not os.access(ast_file, os.F_OK))
      compile_unit[source_file].save(ast_file)
    except clang.cindex.TranslationUnitLoadError as e:
      output = "an error occurred when creating compile unit: %s\n" % e
      sys.stderr.write(output)      
      compile_unit[source_file] = None
  else:
    recent_unit.remove(source_file)
  recent_unit.append(source_file)
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
  print "%s - %s - %s - %d, %d ~ %d, %d - ref: %s - %s" % (cursor.spelling, cursor.displayname, cursor.kind, cursor.extent.start.line, cursor.extent.start.column, cursor.extent.end.line, cursor.extent.end.column, ref_spelling, ref_kind)
  for child in cursor.get_children():
    print_cursor_children(child, level+1)

IndirectBrKind = enum.Enum('IndirectBrKind', 'SWITCH VIRCALL CALLBACK VIRDESTRUCT UNKNOWN UNSUPPORTTED MAYVIRCALL MAYVIRDESTRUCT')

def parse_indirect_branch(cursor):
  # pdb.set_trace()
  if cursor.kind is clang.cindex.CursorKind.RETURN_STMT or cursor.kind is clang.cindex.CursorKind.DECL_STMT or cursor.kind is clang.cindex.CursorKind.VAR_DECL or cursor.kind is clang.cindex.CursorKind.UNARY_OPERATOR or cursor.kind is clang.cindex.CursorKind.COMPOUND_STMT or cursor.kind is clang.cindex.CursorKind.UNEXPOSED_EXPR or cursor.kind is clang.cindex.CursorKind.IF_STMT or cursor.kind is clang.cindex.CursorKind.BINARY_OPERATOR or cursor.kind is clang.cindex.CursorKind.CONDITIONAL_OPERATOR or cursor.kind is clang.cindex.CursorKind.PAREN_EXPR or cursor.kind is clang.cindex.CursorKind.CASE_STMT or cursor.kind is clang.cindex.CursorKind.CXX_REINTERPRET_CAST_EXPR or cursor.kind is clang.cindex.CursorKind.MEMBER_REF_EXPR:
    ret = False
    for child in cursor.get_children():
      if parse_indirect_branch(child) is True:
        ret = True
    return ret
  elif cursor.kind is clang.cindex.CursorKind.SWITCH_STMT:
    output = "indirect branch kind: %s" % IndirectBrKind.SWITCH
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced is not None and (cursor.referenced.kind is clang.cindex.CursorKind.VAR_DECL or cursor.referenced.kind is clang.cindex.CursorKind.FIELD_DECL or cursor.referenced.kind is clang.cindex.CursorKind.PARM_DECL):
    output = "indirect branch kind: %s" % IndirectBrKind.CALLBACK
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR and cursor.referenced is not None and cursor.referenced.kind is clang.cindex.CursorKind.CXX_METHOD:
    output = "indirect branch kind: %s" % IndirectBrKind.VIRCALL
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CALL_EXPR:
    ret = False
    for child in cursor.get_children():
      if parse_indirect_branch(child) is True:
        ret = True
    return ret
  elif cursor.kind is clang.cindex.CursorKind.CXX_DELETE_EXPR:
    output = "indirect branch kind: %s" % IndirectBrKind.VIRDESTRUCT
    sys.stderr.write(output + '\n')
    return True
  elif cursor.kind is clang.cindex.CursorKind.CXX_METHOD:
    ret = False
    for child in cursor.get_children():
      if child.kind is clang.cindex.CursorKind.COMPOUND_STMT:
        for child2 in child.get_children():
          if child2.kind is clang.cindex.CursorKind.RETURN_STMT:
            for child3 in child2.get_children():
              if parse_indirect_branch(child3) is True:
                ret = True
    return ret
  elif cursor.kind is clang.cindex.CursorKind.NO_DECL_FOUND or cursor.kind is clang.cindex.CursorKind.MACRO_INSTANTIATION or cursor.kind is clang.cindex.CursorKind.CLASS_DECL:
    output = "indirect branch kind: %s" % IndirectBrKind.UNSUPPORTTED
    sys.stderr.write(output + '\n')
    return True
  else:
    # output = "indirect branch kind: %s" % IndirectBrKind.UNKNOWN
    # sys.stderr.write(output + '\n')
    # print "indirect branch kind: %s" % IndirectBrKind.UNKNOWN
    return False

def parse_indirect_branch_by_tokens(file_name, line, column):
  output = "getting compile unit: %s ..." % file_name
  sys.stderr.write(output + '\n')
  compile_unit = get_compile_unit(file_name)
  if compile_unit is None:
    return False
  sys.stderr.write('getting done\n')
  src_start = clang.cindex.SourceLocation.from_position(compile_unit, compile_unit.get_file(file_name), line, column)
  src_end = clang.cindex.SourceLocation.from_position(compile_unit, compile_unit.get_file(file_name), line, get_end_column(file_name, line))
  src_ext = clang.cindex.SourceRange.from_locations(src_start, src_end)
  tokens = compile_unit.get_tokens(extent = src_ext)
  for token in tokens:
    if token.spelling == 'switch':
      output = "indirect branch kind: %s" % IndirectBrKind.SWITCH
      sys.stderr.write(output + '\n')
      return True
    # elif token.spelling == 'return':
      # pass
    elif token.spelling == 'delete':
      output = "indirect branch kind: %s" % IndirectBrKind.MAYVIRDESTRUCT
      sys.stderr.write(output + '\n')
      return True
    elif token.kind is clang.cindex.TokenKind.IDENTIFIER:
      if awsctags.is_virtual(token.spelling) is True:
        output = "indirect branch kind: %s" % IndirectBrKind.MAYVIRCALL
        sys.stderr.write(output + '\n')
        return True
    # elif token.spelling == '->':
      # try:
        # token = tokens.next()
        # if token.kind is clang.cindex.TokenKind.IDENTIFIER:
          # token = tokens.next()
          # if token.spelling == '(':
            # output = "indirect branch kind: %s" % IndirectBrKind.MAYVIRCALL
            # sys.stderr.write(output + '\n')
            # return True
      # except StopIteration:
        # pass
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
      if ret is False:
        print "the result of parsing cursor is IndirectBrKind.UNKNOWN\n\t%s: %d, %d - %d, %d" % (file_name, cursor.extent.start.line, cursor.extent.start.column, cursor.extent.end.line, cursor.extent.end.column)
    if ret is False:
      ret = parse_indirect_branch_by_tokens(file_name, line, column)
      if ret is False:
        print "the result of parsing tokens is IndirectBrKind.UNKNOWN\n\t%s: %d, %d" % (file_name, line, column)
    return ret