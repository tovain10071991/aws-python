import capstone

disassembler = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
disassembler.detail = True
disassembler.syntax = capstone.CS_OPT_SYNTAX_ATT

class AwsDis(object):
  @staticmethod
  def iterate_indiret_branch(content, start_addr):
    for inst in disassembler.disasm(content, start_addr):
      if (inst.group(capstone.CS_GRP_CALL) or inst.group(capstone.CS_GRP_IRET) or inst.group(capstone.CS_GRP_RET) or inst.group(capstone.CS_GRP_JUMP)) and (inst.op_count(capstone.CS_OP_REG) or inst.op_count(capstone.CS_OP_MEM)):
        yield inst