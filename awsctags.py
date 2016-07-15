import ctags, re, pdb
from ctags import CTags, TagEntry

tag_path = '/mnt/sdb/test/ctags_test/nginx_tag_file'

tag_file = CTags(tag_path)

def skip_white_space(file_name, line):
  fp = open(file_name, 'r')
  i = 0
  for i in range(1, line):
    fp.readline()
  line_content = fp.readline().lstrip()
  fp.close()
  return line_content

def is_virtual(name):
  entry = TagEntry()
  if(tag_file.find(entry, name, ctags.TAG_FULLMATCH|ctags.TAG_OBSERVECASE)):
    if (entry['kind'] == 'prototype' or entry['kind'] == 'function') and entry['lineNumber'] != 0:
      line_content = skip_white_space(entry['file'], entry['lineNumber'])
      if line_content.find("virtual") is 0:
        return True
  while tag_file.findNext(entry):
    if (entry['kind'] == 'prototype' or entry['kind'] == 'function') and entry['lineNumber'] != 0:
      line_content = skip_white_space(entry['file'], entry['lineNumber'])
      if line_content.find("virtual") is 0:
        return True
  return False
  
def is_funcptr(name):
  entry = TagEntry()
  if(tag_file.find(entry, name, ctags.TAG_FULLMATCH|ctags.TAG_OBSERVECASE)):
    if (entry['kind'] == 'member') and entry['lineNumber'] != 0:
      line_content = entry['pattern'] # skip_white_space(entry['file'], entry['lineNumber'])
      if is_funcptr_type(re.split("/\^| *", line_content)[2]):
        return True
  while tag_file.findNext(entry):
    if (entry['kind'] == 'member') and entry['lineNumber'] != 0:
      line_content = entry['pattern'] # skip_white_space(entry['file'], entry['lineNumber'])
      if is_funcptr_type(re.split("/\^| *", line_content)[2]):
        return True
  return False
  
def is_funcptr_type(name):
  entry = TagEntry()
  if(tag_file.find(entry, name, ctags.TAG_FULLMATCH|ctags.TAG_OBSERVECASE)):
    if (entry['kind'] == 'typedef') and entry['lineNumber'] != 0:
      line_content = entry['pattern']
      line_list = re.split("/\^| *", line_content)
      if len(line_list)>=4:
        for i in range(0, len(line_list[3])-2):
          if line_list[3][i] == '*':
            continue
          elif line_list[3][i] == '(' and line_list[3][i+1] == '*':
            return True
          else:
            break
  while tag_file.findNext(entry):
    if (entry['kind'] == 'typedef') and entry['lineNumber'] != 0:
      line_content = entry['pattern']
      line_list = re.split("/\^| *", line_content)
      if len(line_list)>=4:
        for i in range(0, len(line_list[3])-2):
          if line_list[3][i] == '*':
            continue
          elif line_list[3][i] == '(' and line_list[3][i+1] == '*':
            return True
          else:
            break
  return False