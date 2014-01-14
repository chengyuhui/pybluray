__author__ = 'Harry'
import pprint
pp = pprint.PrettyPrinter(indent=2)
from bitstring import BitStream

def to_scenarist(time):
    hour = time / (60*60*45000)
    time -= 60*60*45000*hour
    minute = time / (60*45000)
    time -= minute*60*45000
    second = time / 45000
    rest = time - second * 45000
    return [hour,minute,second,round(rest/45000.0*1000*23.976/1000)]

def parse_clip(bs):
    clip = {
        'clip_id':bs.read('bytes:5'),
        'codec_id':bs.read('bytes:4'),
        'stc_id':bs.read('uint:8')
    }

    if clip['codec_id'] != 'M2TS':
        raise ValueError('Incorrect CodecIdentifier (%s)'%clip['codec_id'])
    return clip

def parse_header(bs):
    [sig1,sig2]=bs.readlist('hex:32, hex:32')

    if sig1 != '4d504c53' or (sig2 != '30323030' and sig2 != '30313030'):
        raise ValueError('MPLS failed signature match: expected MPLS0100 or MPLS0200')

    return bs.readlist('uintbe:32,uintbe:32,uintbe:32')

def parse_uo(bs):
    uo = {}
    uo['menu_call'],\
    uo['title_search'],\
    uo['chapter_search'],\
    uo['time_search'],\
    uo['skip_to_next_point'],\
    uo['skip_to_prev_point'],\
    uo['play_firstplay'],\
    uo['stop'],\
    uo['pause_on'],\
    uo['pause_off'],\
    uo['still'],\
    uo['forward'],\
    uo['backward'],\
    uo['resume'],\
    uo['move_up'],\
    uo['move_down'],\
    uo['move_left'],\
    uo['move_right'],\
    uo['select'],\
    uo['activate'],\
    uo['select_and_activate'],\
    uo['primary_audio_change'],\
    uo['angle_change'],\
    uo['popup_on'],\
    uo['popup_off'],\
    uo['pg_enable_disable'],\
    uo['pg_change'],\
    uo['secondary_video_enable_disable'],\
    uo['secondary_video_change'],\
    uo['secondary_audio_enable_disable'],\
    uo['secondary_audio_change'],\
    uo['pip_pg_change'] = bs.readlist('bool,'*21 + 'bool,pad:1,' + 'bool,'*9 + 'pad:1,bool')

    return uo


def parse_appinfo(bs):
    if bs.pos & 0x07:
        raise ValueError('MPLS parse_appinfo: alignment error')
    pos = bs.pos >> 3
    app_len = bs.read('uintbe:32')

    app_info = {}
    bs.read('pad:8')
    app_info['playback_type'] = bs.read('uint:8')
    if app_info['playback_type'] == 2 or app_info['playback_type'] == 3:
        app_info['playback_count'] = bs.read('uint:16')
    else:
        bs.read('pad:16')

    app_info['uo_mask'] = parse_uo(bs.read('bits:64'))
    app_info['random_access_flag'],app_info['audio_mix_flag'],app_info['lossless_bypass_flag'] \
        = bs.readlist('bool,bool,bool')
    bs.pos = pos+app_len
    return app_info

def parse_stream(bs):
    if bs.pos & 0x07:
        raise ValueError('MPLS parse_stream: Stream alignment error')
    stream_len = bs.read('uint:8')
    pos = bs.bytepos
    s = {
        'stream_type':bs.read('uint:8')
    }

    _ref = s['stream_type']

    if _ref == 1:
        s['pid'] = bs.read('hex:16')
    elif _ref == 2 or _ref == 4:
        s['subpath_id'],s['subclip_id'],s['pid'] = bs.readlist('hex:8,hex:8,hex:16')
    elif _ref == 3:
        s['subpath_id'],s['pid'] = bs.readlist('hex:8,hex:16')
    else:
        raise ValueError('unrecognized stream type %02x'%_ref)

    bs.bytepos = stream_len + pos
    stream_len2 = bs.read('uint:8')
    pos2 = bs.bytepos

    s['coding_type'] = bs.read('uint:8')
    _ref = s['coding_type']
    if _ref in [0x01,0x02,0xea,0x1b]:
        s['format'],s['rate'] = bs.readlist('uint:4,uint:4')
    elif _ref in [0x03,0x04,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0xa1,0xa2]:
        s['format'],s['rate'],s['lang'] = bs.readlist('uint:4,uint:4,bytes:3')
    elif _ref == 0x90 or _ref == 0x91:
        s['lang'] = bs.read('bytes:3')
    elif _ref == 0x92:
        s['char_code'],s['lang'] = bs.readlist('uint:8,bytes:3')
    else:
        raise ValueError('unrecognized coding type %02x'%_ref)

    bs.bytepos = stream_len2 + pos2
    return s

def parse_stn(bs):
    if bs.pos & 0x07:
        raise ValueError('MPLS parse_stn: Stream alignment error')
    stn_len = bs.read('uint:16')
    pos = bs.bytepos
    bs.read('pad:16')
    stn = {}
    stn['num_video']           = bs.read('uint:8')
    stn['num_audio']           = bs.read('uint:8')
    stn['num_pg']              = bs.read('uint:8')
    stn['num_ig']              = bs.read('uint:8')
    stn['num_secondary_audio'] = bs.read('uint:8')
    stn['num_secondary_video'] = bs.read('uint:8')
    stn['num_pip_pg']          = bs.read('uint:8')

    bs.read('pad:40')

    #Primary Video Streams
    stn['video'] = []
    for i in range(0,stn['num_video']):stn['video'].append(parse_stream(bs))

    #Primary Audio Streams
    stn['audio'] = []
    for i in range(0,stn['num_audio']):stn['audio'].append(parse_stream(bs))

    #Presentation Graphic Streams
    stn['pg'] = []
    for i in range(0,stn['num_pg'] + stn['num_pip_pg']):stn['pg'].append(parse_stream(bs))

    #Interactive Graphic Streams
    stn['ig'] = []
    for i in range(0,stn['num_ig']):stn['ig'].append(parse_stream(bs))

    #Primary Audio Streams
    #stn['audio'] = []
    #for i in range(0,stn['num_audio']):stn['audio'].append(parse_stream(bs))

    return stn

def parse_playitem(bs):
    if bs.pos & 0x07:
        raise ValueError('MPLS parse_playitem: alignment error')
    pi = {}
    item_len = bs.read('uint:16')
    pos = bs.bytepos
    #Primary Clip identifer
    clip_id = bs.read('bytes:5')[0:5]
    codec_id = bs.read('bytes:4')[0:4]

    bs.read('pad:11')
    pi['is_multi_angle'] = bs.read('bool')
    pi['connection_condition'] = bs.read('uint:4')
    _ref = pi['connection_condition']
    if _ref != 0x01 and _ref != 0x05 and _ref != 0x06:
        raise ValueError("Unexpected connection condition %02x"%_ref)
    stc_id = bs.read('uint:8')
    pi['in_time'] = to_scenarist(bs.read('uintbe:32'))
    pi['out_time'] = to_scenarist(bs.read('uintbe:32'))
    pi['uo_mask'] = parse_uo(bs.read('bits:64'))
    pi['random_access_flag'],pi['still_mode'] = bs.readlist('bool,pad:7,uint:8')
    if pi['still_mode'] == 0x01:
        pi['still_time'] = bs.read('uint:16')
    else:
        bs.read('pad:16')
    pi['angle_count'] = 1
    if pi['is_multi_angle']:
        pi['angle_count'] = bs.read('uint:8')
        if pi['angle_count'] < 1 : pi['angle_count'] = 1
        bs.read('pad:6')
        pi['is_different_audio'] = bs.read('bool')
        pi['is_seamless_angle'] = bs.read('bool')

    pi['clip'] = [
        {
            'clip_id':clip_id,
            'codec_id':codec_id,
            'stc_id':stc_id
        }
    ]
    for i in range (1,pi['angle_count']):
        pi['clip'].append(parse_clip(bs))

    pi['stn'] = parse_stn(bs)
    bs.bytepos = pos + item_len
    return pi


def parse_playlist(bs):
    bs.read('pad:48')
    pl = {
        'play_item':[]
    }
    pl['list_count'],pl['sub_count'] = bs.readlist('uint:16,uint:16')
    #print parse_playitem(bs)

    for i in range(0,pl['list_count']):
        pl['play_item'].append(parse_playitem(bs))
    pp.pprint(pl['play_item'][1])


class Playlist:
    def __init__(self,file_path):
        self.file_path = file_path
        self.parsed = False

    def parse(self):
        bs = BitStream(filename=self.file_path)
        pls = {}
        pls['list_pos'],pls['mark_pos'],pls['ext_pos'] = parse_header(bs)
        bs.read('pad:160')
        pls['app_info'] = parse_appinfo(bs)
        bs.bytepos = pls['list_pos']
        parse_playlist(bs)
        print pls


