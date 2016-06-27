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

if __name__ == '__main__':
  for inst in dis_helper.iterate_indiret_branch(elf_helper.text_sec.content, elf_helper.text_sec.start_addr):
    print("0x%x %s %s" %(inst.address, inst.mnemonic, inst.op_str))
    dbg_helper.print_source_code(inst.address)
    file_name, line, column = dbg_helper.get_location(inst.address)
    if file_name is None:
      continue
    parse_helper.print_cursors(file_name, line, column)
    parse_helper.parse_indirect_branch(file_name, line, column)