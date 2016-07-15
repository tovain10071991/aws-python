import argparse, os, pdb
from awsdbg import *
from awself import *
from awsparse import *
from awsdis import *

# global initialize

parser = argparse.ArgumentParser(description='analysis indirect branch with source')
parser.add_argument("-b", "--binary", default = '/bin/ls')
args = parser.parse_args()

executable = args.binary

dbg_helper = AwsDbg(executable)
elf_helper = AwsElf(executable)
parse_helper = AwsParse()
dis_helper = AwsDis()

total = 5250

if __name__ == '__main__':
  num = 0
  offset = elf_helper.text_sec.start_off
  address = elf_helper.text_sec.start_addr
  while(1):
    content = elf_helper.text_sec.get_content(offset)
    if content is None:
      break
    # pdb.set_trace()
    inst, inst_size = dis_helper.get_inst(content, address)
    if inst is None:
      break
    if(dis_helper.is_indirect_branch(inst)):
      num = num + 1
      output = "the num of parsing: %d total: %d\n" % (num, total)
      sys.stderr.write(output)
      output = "0x%x %s %s\n" % (inst.address, inst.mnemonic, inst.op_str)
      sys.stderr.write(output)
      # sys.stderr.flush()
      file_name, line, column = dbg_helper.get_location(inst.address)
      # pdb.set_trace()
      if file_name is not None:
        if parse_helper.parse_indirect_branch(file_name, line, column) is False:
          sys.stderr.write('indirect branch kind: IndirectBrKind.UNKNOWN\n')
          print "indirect branch kind: IndirectBrKind.UNKNOWN"
          print("0x%x %s %s" %(inst.address, inst.mnemonic, inst.op_str))
          dbg_helper.print_source_code(inst.address)
          print "%s: %d, %d" % (file_name, line, column)
          parse_helper.print_cursors(file_name, line, column)
    offset = offset + inst_size
    address = address + inst_size
  sys.stderr.write("done!\n")