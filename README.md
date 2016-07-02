# aws-python

this tool is used for analyzing the kind of indirect branches in a binary executable.

execute like below:

    $ python ./aws.py -b /path/to/some/program


=========

The tool iterate instrucions in .text section in binary.

When meeting a indiret branch, dicide kind through debug info.

So the analyzed binary must have debug info and source files must be reserved.

=========

## internals

Disassembe using capstone.

Parse elf(get .text section) using pyelftools.

Get debug info(get source file and line associated with instruction) using lldb python bindings.

Parse AST using clang python bindings.

When meeting a indiret branch, get source line by lldb. iterate cursors in this line by clang(it seems that the debug info has no column info and there may be multi cursors in a line).

The kind of indirect branches is: virtual call, virtual destructor, call back, switch.

If parsing cursors is fault, then parsing tokens.

Some kind enum the prefix of which is "MAY" is obtained by parsing tokens.

But the implementation of parsing token is incomplete.
