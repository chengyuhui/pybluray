__author__ = 'Harry'
from bitstring import BitStream
import json

def parse_header(bs):
    [sig1,sig2]=bs.readlist('hex:32, hex:32')

    if sig1 != '4d4f424a' or (sig2 != '30323030' and sig2 != '30313030'):
        raise ValueError('MovieObject.bdmv failed signature match: expected MOBJ0100 or MOBJ0200')

    return bs.read('uintbe:32')

def parse_cmd(bs):
    opcode = bs.read('hex:32')
    bs.bytepos -= 4
    cmd = {
        'opcode':opcode,
        'insn':{
            'op_cnt':bs.read('uint:3'),
            'grp':bs.read('uint:2'),
            'sub_grp':bs.read('uint:3'),
            'imm_op1':bs.read('bool'),
            'imm_op2':bs.read('bool'),
            'branch_opt':bs.readlist('pad:2,uint:4')[0],
            'cmp_opt':bs.readlist('pad:4,uint:4')[0],
            'set_opt':bs.readlist('pad:3,uint:5')[0]
        },
        'dst':bs.read('uintbe:32'),
        'src':bs.read('uintbe:32')
    }
    return cmd

def parse_object(bs):
    obj = {
        'resume_intention_flag':bs.read('bool'),
        'menu_call_mask':bs.read('bool'),
        'title_search_mask':bs.read('bool')
    }

    [num_cmds] = bs.readlist('pad:13,uintbe:16')
    cmds = []
    for i in range(0,num_cmds):
        cmds.append(parse_cmd(bs))
    obj['cmds'] = cmds
    return obj

class MovieObject:
    def __init__(self,file_path):
        self.file_path = file_path
        self.parsed = False
        self.objects = []

    def parse(self):
        bs = BitStream(filename=self.file_path)
        parse_header(bs)
        bs.bytepos = 40
        data_len = bs.read('uintbe:32')
        if (bs.len - bs.pos)/8 < data_len:
            raise ValueError('MovieObject:invalid data_len %d'%data_len)

        objects = []
        [num_objects] = bs.readlist('pad:32,uintbe:16')

        for i in range(0,num_objects):
            objects.append(parse_object(bs))
        self.parsed = True
        self.objects = objects

    def __getattr__(self, item):
        if not self.parsed:
            raise Exception('Not parsed!')
        if item == 'objects':
            return self.objects
        else:
            raise AttributeError("Attribute %s not found!"%item)




