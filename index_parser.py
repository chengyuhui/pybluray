__author__ = 'Harry'
import json
from bitstring import BitStream


def parse_header(bs):
    [sig1,sig2]=bs.readlist('hex:32, hex:32')

    if sig1 != '494e4458' or (sig2 != '30323030' and sig2 != '30313030'):
        raise ValueError('index.bdmv failed signature match: expected INDX0100 or INDX0200')

    return bs.readlist('uintbe:32, uintbe:32')

def parse_app_info(bs):
    bs.bytepos = 40

    info_len = bs.read('uintbe:32')

    if info_len != 34:
        print "index.bdmv app_info length is %d, expected 34 !" % info_len

    app_info = {}
    [app_info['initial_output_mode_preference'],
     app_info['content_exist_flag'],
     app_info['video_format'],
     app_info['frame_rate'],
     app_info['user_data']
    ] = bs.readlist('pad:1,bool,bool,pad:5,uintbe:32,uintbe:32,bytes:32')

    return app_info


def parse_hdmv_obj(bs):
    hdmv = {
        'pos':bs.pos
    }
    [hdmv['playback_type'],hdmv['id_ref']] = bs.readlist('uint:2,pad:14,uint:16,pad:32')
    return hdmv


def parse_bdj_obj(bs):
    bdj = {
        'pos':bs.pos
    }
    [bdj['playback_type'],bdj['name']] = bs.readlist('uint:2,pad:14,bytes:5,pad:8')
    return bdj


def parse_playback_obj(bs):
    obj = {}
    [obj['object_type']] = bs.readlist('uint:2,pad:30')

    if obj['object_type'] == 1 :
        obj['hdmv'] = parse_hdmv_obj(bs)
    else:
        obj['bdj'] = parse_bdj_obj(bs)

    return obj


def parse_index(bs):
    #index_len = bs.read('uintbe:32')
    index = {
        'first_play':parse_playback_obj(bs),
        'top_menu':parse_playback_obj(bs),
        'num_titles':bs.read('uint:16'),
        'titles':[]
    }

    for i in range(0,index['num_titles']):
        index['titles'].append({
            'pos':bs.pos,
            'object_type':bs.read('uint:2'),
            'access_type':bs.read('uint:2')
        })
        bs.read('pad:28')
        print index['titles'][i]['object_type']
        if index['titles'][i]['object_type'] == 1:
            index['titles'][i]['hdmv'] = parse_hdmv_obj(bs)
        else:
            index['titles'][i]['bdj'] = parse_bdj_obj(bs)


    return index



class Index:
    def __init__(self, file_path):
        self.file_path = file_path
        self.app_info = {}
        self.indexes = {}
        self.parsed = False

    def parse(self):
        bs = BitStream(filename=self.file_path)
        [index_start, extension_data_start] = parse_header(bs)
        self.app_info = parse_app_info(bs)

        bs.bytepos = index_start
        self.indexes = parse_index(bs)
        self.parsed = True

    def get_app_info(self):
        if not self.parsed:
            raise Exception('Not parsed!')
        return self.app_info

    def __getattr__(self, item):
        if not self.parsed:
            raise Exception('Not parsed!')
        if item == 'app_info':
            return self.app_info
        elif item == 'indexes':
            return self.indexes
        else:
            raise AttributeError("Attribute %s not found!"%item)





