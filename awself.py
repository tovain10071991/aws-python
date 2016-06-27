import elftools.elf.sections, elftools.elf.elffile

class AwsElf(object):

  def __init__(self, executable):
    fp = open(executable, 'rb')
    self.elf_file = elftools.elf.elffile.ELFFile(fp)
    
    class Section(object):
      def __init__(self, elf_file, sec_name):
        self.sec = elf_file.get_section_by_name(sec_name)
        self.start_off = self.sec['sh_offset']
        self.size = self.sec['sh_size']
        self.start_addr = self.sec['sh_addr']
        self.content = self.sec.data()
      
    self.text_sec = Section(self.elf_file, ".text")