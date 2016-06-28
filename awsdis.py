import capstone, os

disassembler = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
disassembler.detail = True
disassembler.syntax = capstone.CS_OPT_SYNTAX_ATT

class AwsDis(object):
  @staticmethod
  def get_inst(content, start_addr):
    try:
      inst = disassembler.disasm(content, start_addr).next()
      return (inst, inst.size)    
    except StopIteration:
      return (None, 0)
      
  @staticmethod
  def is_indirect_branch(inst):
    if (inst.group(capstone.CS_GRP_CALL) or inst.group(capstone.CS_GRP_IRET) or inst.group(capstone.CS_GRP_RET) or inst.group(capstone.CS_GRP_JUMP)) and (inst.op_count(capstone.CS_OP_REG) or inst.op_count(capstone.CS_OP_MEM)):
      return True
    else:
      return False