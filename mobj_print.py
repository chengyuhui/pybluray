__author__ = 'Harry'
from bitstring import pack
hdmv_insn_grp = {
    'branch':0,
    'cmp':1,
    'set':2
}

hdmv_insn_grp_branch = {
    'goto':0x00,
    'jump':0x01,
    'play':0x02
}

insn_opt_goto = ['nop','goto','break']

def mobj_parse(cmds):
    for cmd in cmds:
        insn = cmd['insn']
        str = "%s %08x,%08x"%(cmd['opcode'],cmd['dst'],cmd['src'])

        if insn['grp'] == hdmv_insn_grp['branch']:
            if insn['sub_grp'] == hdmv_insn_grp_branch['goto']:
                if insn['branch_opt']<insn_opt_goto:
                    str += "%-10s"%insn_opt_goto[insn['branch_opt']]
