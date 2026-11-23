"""Mock-ups of the right-half nice!view showing the active Miryoku layer.
Pixel-exact at the screen's 68 x 160 (portrait) resolution, 1-bit."""
import os
import matplotlib
from PIL import Image, ImageDraw, ImageFont

FD = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data/fonts/ttf')
F8 = ImageFont.truetype(os.path.join(FD, 'DejaVuSansMono-Bold.ttf'), 9)    # stands in for unscii_8
F16 = ImageFont.truetype(os.path.join(FD, 'DejaVuSans-Bold.ttf'), 15)      # stands in for montserrat_16
W, H = 68, 160

# ---- 7x7 pixel icons ('#' = ink) ------------------------------------------------------------
ICONS = {k: v.strip('\n').split('\n') for k, v in {
'left': """
...#...
..##...
.######
#######
.######
..##...
...#...""",
'right': """
...#...
...##..
######.
#######
######.
...##..
...#...""",
'up': """
...#...
..###..
.#####.
#######
..###..
..###..
..###..""",
'down': """
..###..
..###..
..###..
#######
.#####.
..###..
...#...""",
'home': """
#......
#..#...
#.##...
######.
#.##...
#..#...
#......""",
'end': """
......#
...#..#
...##.#
.######
...##.#
...#..#
......#""",
'pgup': """
#######
...#...
..###..
.#####.
...#...
...#...
...#...""",
'pgdn': """
...#...
...#...
...#...
.#####.
..###..
...#...
#######""",
'undo': """
..#....
.##....
#######
.##...#
..#...#
......#
..####.""",
'redo': """
....#..
....##.
#######
#...##.
#...#..
#......
.####..""",
'cut': """
#.....#
.#...#.
..#.#..
...#...
.##.##.
#..#..#
.##.##.""",
'copy': """
####...
#..#...
#.####.
#.#..#.
###..#.
..#..#.
..####.""",
'paste': """
.#.#.#.
#######
#.....#
#.###.#
#.....#
#.###.#
#######""",
'enter': """
......#
......#
..#...#
.##...#
#######
.##....
..#....""",
'bksp': """
..#####
.#....#
#.#.#.#
#..#..#
#.#.#.#
.#....#
..#####""",
'del': """
#####..
#....#.
#.#.#.#
#..#..#
#.#.#.#
#....#.
#####..""",
'mouse_l': """
###.###
###.#..
###.#..
#######
#.....#
#.....#
.#####.""",
'mouse_r': """
###.###
..#.###
..#.###
#######
#.....#
#.....#
.#####.""",
'mouse_m': """
###.###
#.###.#
#.###.#
#######
#.....#
#.....#
.#####.""",
'scr_l': """
..#..#.
.##.##.
#######
.##.##.
..#..#.
.......
.......""",
'scr_r': """
.#..#..
.##.##.
#######
.##.##.
.#..#..
.......
.......""",
'scr_u': """
...#...
..###..
.#####.
...#...
..###..
.#####.
...#...""",
'scr_d': """
...#...
.#####.
..###..
...#...
.#####.
..###..
...#...""",
'star': """
.......
.#.#.#.
..###..
.#####.
..###..
.#.#.#.
.......""",
'prev': """
#..#..#
#.##.##
#######
#.##.##
#..#..#
.......
.......""",
'next': """
#..#..#
##.##.#
#######
##.##.#
#..#..#
.......
.......""",
'volup': """
...#...
..##.#.
####..#
####.##
####..#
..##.#.
...#...""",
'voldn': """
...#...
..##...
####...
####.##
####...
..##...
...#...""",
'mute': """
...#...
..##...
####.#.
####..#
####.#.
..##...
...#...""",
'play': """
#..#.#.
##.#.#.
####.#.
#####..
####.#.
##.#.#.
#..#.#.""",
'stop': """
.......
.#####.
.#####.
.#####.
.#####.
.#####.
.......""",
'sun': """
#..#..#
.#.#.#.
..###..
###.###
..###..
.#.#.#.
#..#..#""",
'bolt': """
....##.
...##..
..##...
.######
...##..
..##...
.##....""",
'bt': """
...#...
...##..
.#.#.#.
..###..
.#.#.#.
...##..
...#...""",
'usb': """
...#...
..###..
...#.#.
.#.#.#.
.#.##..
..##...
...#...""",
'capsw': """
..#....
.#.#...
#...#..
#####..
#...#.#
#...#.#
......#""",
}.items()}


TINY = {'0': '###,#.#,#.#,#.#,###', '1': '.#.,##.,.#.,.#.,###', '2': '###,..#,###,#..,###',
         '3': '###,..#,.##,..#,###', '4': '#.#,#.#,###,..#,..#', '5': '###,#..,###,..#,###',
         '6': '###,#..,###,#.#,###', '7': '###,..#,.#.,.#.,.#.', '8': '###,#.#,###,#.#,###',
         '9': '###,#.#,###,..#,###', 'P': '###,#.#,###,#..,#..', 'S': '###,#..,###,..#,###',
         'C': '###,#..,#..,#..,###', 'R': '##.,#.#,##.,#.#,#.#', 'L': '#..,#..,#..,#..,###',
         'B': '##.,#.#,##.,#.#,##.', 'K': '#.#,#.#,##.,#.#,#.#', 'N': '#.#,###,###,###,#.#',
         'U': '#.#,#.#,#.#,#.#,###', 'M': '#.#,###,###,#.#,#.#', 'Y': '#.#,#.#,.#.,.#.,.#.',
         'A': '.#.,#.#,###,#.#,#.#', 'V': '#.#,#.#,#.#,#.#,.#.', 'F': '###,#..,##.,#..,#..',
         'I': '###,.#.,.#.,.#.,###', 'T': '###,.#.,.#.,.#.,.#.', 'E': '###,#..,##.,#..,###',
         'G': '###,#..,#.#,#.#,###', 'H': '#.#,#.#,###,#.#,#.#', 'O': '###,#.#,#.#,#.#,###',
         'X': '#.#,#.#,.#.,#.#,#.#', 'D': '##.,#.#,#.#,#.#,##.', ' ': '...,...,...,...,...'}
TINY.update({'Z': '###,..#,.#.,#..,###', '/': '..#,..#,.#.,#..,#..', 'W': '#.#,#.#,###,###,#.#'})


def blank():
    return Image.new('1', (W, H), 1)       # 1 = background (white), 0 = ink


def icon(d, x, y, name, ink=0):
    for r, row in enumerate(ICONS[name]):
        for c, ch in enumerate(row):
            if ch == '#':
                d.point((x + c, y + r), fill=ink)


def text(d, x, y, w, s, font=F8, ink=0):
    tw = d.textlength(s, font=font)
    d.text((x + (w - tw) / 2, y), s, font=font, fill=ink)


def tiny(d, x, y, w, s, ink=0):
    """3x5 digits/letters for 2-3 character labels (F-keys, layer hints)."""
    G = TINY
    tw = len(s) * 4 - 1
    x0 = x + (w - tw) // 2
    for i, ch in enumerate(s):
        for r, row in enumerate(G[ch].split(',')):
            for c, px in enumerate(row):
                if px == '#':
                    d.point((x0 + i * 4 + c, y + r), fill=ink)


SHOW_UNUSED = False   # False: keys that do nothing on a layer are left blank (free for a later piano layer)


def key(d, x, y, label, kind='key', w=12, h=12):
    """kind: key (outline), mod (filled, inverted label), none (dotted, empty)."""
    if kind == 'none':
        if not SHOW_UNUSED:
            return
        for i in range(0, w, 2):
            d.point((x + i, y)); d.point((x + i, y + h - 1))
        for j in range(0, h, 2):
            d.point((x, y + j)); d.point((x + w - 1, y + j))
        return
    ink = 0
    if kind == 'mod':
        d.rectangle((x, y, x + w - 1, y + h - 1), fill=0); ink = 1
    else:
        d.rectangle((x, y, x + w - 1, y + h - 1), outline=0)
    if label is None:
        return
    if label.startswith('@') and len(label) > 1:
        icon(d, x + (w - 7) // 2, y + (h - 7) // 2, label[1:], ink)
    elif label.startswith('~') and len(label) > 1:
        tiny(d, x, y + (h - 5) // 2, w, label[1:], ink)
    else:
        text(d, x, y + 1, w, label, ink=ink)


def screen(layer, held, grid, kinds, thumbs, hint, side='right', out=('BLE', 1, 'CONNECTED')):
    im = blank(); d = ImageDraw.Draw(im)
    # --- top block (0..67): battery + link kept, layer badge replaces "corne"
    d.rectangle((2, 3, 30, 13), outline=0); d.rectangle((31, 6, 32, 10), fill=0); d.rectangle((4, 5, 22, 11), fill=0)
    text(d, 0, 2, 66, '      ' + ' ')  # spacing placeholder
    if side == 'right':
        icon(d, 56, 4, 'bt')             # link symbol (stands in for LV_SYMBOL_WIFI)
        text(d, 0, 22, W, 'linked')
    else:
        icon(d, 56, 4, 'usb' if out[0] == 'USB' else 'bt')
        text(d, 0, 20, W, 'USB' if out[0] == 'USB' else f'BLE {out[1]}')
        tiny(d, 0, 31, W, out[2])
    if held:
        d.rectangle((0, 38, W - 1, 63), fill=0); text(d, 0, 42, W, layer, font=F16, ink=1)
    else:
        d.rectangle((0, 38, W - 1, 63), outline=0); text(d, 0, 42, W, layer, font=F16, ink=0)
    # --- middle block (68..135): 5x3 grid at 14 px pitch + 3 thumbs
    y0 = 70
    for r in range(3):
        for c in range(5):
            key(d, c * 14, y0 + r * 14, grid[r][c], kinds[r][c])
    for i, (lab, kd) in enumerate(thumbs):   # inner thumb (big, angled on a Corne) sits lowest
        if side == 'left':
            key(d, 20 + i * 16, y0 + 45 + i, lab, kd, w=14, h=14)
        else:
            key(d, i * 16, y0 + 47 - i, lab, kd, w=14, h=14)
    # --- bottom strip (136..159)
    tiny(d, 0, 148, W, hint)
    return im


K, M, N = 'key', 'mod', 'none'
R_MODS = [N, M, M, M, M]
CLIP = ['@redo', '@paste', '@copy', '@cut', '@undo']
LAYERS = [
    ('BASE', False,
     [['Y', 'U', 'I', 'O', 'P'], ['H', 'J', 'K', 'L', "'"], ['N', 'M', ',', '.', '/']],
     [[K] * 5, [K, M, M, M, M], [K] * 5],
     [('~SYM', K), ('~NUM', K), ('~FUN', K)], 'RIGHT HAND'),
    ('NAV', True,
     [CLIP, ['@capsw', '@left', '@down', '@up', '@right'], ['~INS', '@home', '@pgdn', '@pgup', '@end']],
     [[K] * 5] * 3, [('@enter', K), ('@bksp', K), ('@del', K)], 'HOLD SPACE'),
    ('MOUSE', True,
     [CLIP, [None, '@left', '@down', '@up', '@right'], [None, '@scr_l', '@scr_d', '@scr_u', '@scr_r']],
     [[K] * 5, [N, K, K, K, K], [N, K, K, K, K]], [('@mouse_r', K), ('@mouse_l', K), ('@mouse_m', K)], 'HOLD TAB'),
    # RGB row and external-power toggle do nothing on this board (no LEDs, no switched power):
    # left blank as unused -> free for a later piano layer
    ('MEDIA', True,
     [['@sun', '~FX', '~HUE', '~SAT', '~BRI'], ['@bolt', '@prev', '@voldn', '@volup', '@next'],
      ['@usb', '~B0', '~B1', '~B2', '~B3']],
     [[N] * 5, [N, K, K, K, K], [K] * 5], [('@stop', K), ('@play', K), ('@mute', K)], 'HOLD ESC'),
    ('NUM', True,
     [['[', '7', '8', '9', ']'], [';', '4', '5', '6', '='], ['`', '1', '2', '3', '\\']],
     [[K] * 5] * 3, [('.', K), ('0', K), ('-', K)], 'LEFT HAND'),
    ('SYM', True,
     [['{', '&', '@star', '(', '}'], [':', '$', '%', '^', '+'], ['~', '!', '@', '#', '|']],
     [[K] * 5] * 3, [('(', K), (')', K), ('_', K)], 'LEFT HAND'),
    ('FUN', True,
     [['~12', '~7', '~8', '~9', '~PS'], ['~11', '~4', '~5', '~6', '~SL'], ['~10', '~1', '~2', '~3', '~PB']],
     [[K] * 5] * 3, [('~APP', K), ('@enter', N), ('~TAB', K)], 'LEFT HAND'),
]
# fix-ups: Fun thumbs are App / Space / Tab
LAYERS[6] = LAYERS[6][:4] + ([('~APP', K), ('~SPC', K), ('~TAB', K)],) + LAYERS[6][5:]
_by = {l[0]: l for l in LAYERS}
EXTRA = ('EXTRA', False) + _by['BASE'][2:]
TAP = ('TAP', False, _by['BASE'][2], [[K] * 5] * 3, [('@enter', K), ('@bksp', K), ('@del', K)], 'NO MODS')
BUTTON = ('BTN', True, [CLIP, [None, '~SH', '~CT', '~AL', '~GU'], CLIP], [[K] * 5, [N, M, M, M, M], [K] * 5],
          [('@mouse_r', K), ('@mouse_l', K), ('@mouse_m', K)], 'HOLD Z OR /')
# ---- own-hand tables: each screen shows its own half of the active layer ----------------------
SEL_L = ['~BL', '~TAP', '~EXT', '~BAS', None]          # bootloader, default-layer selects
SEL_R = [None, '~BAS', '~EXT', '~TAP', '~BL']
MODS_L = ['~GU', '~AL', '~CT', '~SH', None]
MODS_R = [None, '~SH', '~CT', '~AL', '~GU']
KS_L = [K, K, K, K, N]
KS_R = [N, K, K, K, K]
MK_L = [M, M, M, M, N]
MK_R = [N, M, M, M, M]
CLIP_L = ['@undo', '@cut', '@copy', '@paste', '@redo']
NO3 = [(None, N), (None, N), (None, N)]


def held_left(name, lock, hint):      # left hand while a LEFT-thumb layer is held: mods + selects
    return (name, True, [SEL_L, MODS_L, [None, '~AGR', '~' + lock, '~' + name[:3], None]],
            [KS_L, MK_L, [N, K, K, K, N]], NO3, hint)


def held_right(name, lock, hint):     # right hand while a RIGHT-thumb layer is held
    return (name, True, [SEL_R, MODS_R, [None, '~' + name[:3], '~' + lock, '~AGR', None]],
            [KS_R, MK_R, [N, K, K, K, N]], NO3, hint)


LEFT_BY_ID = [
    ('BASE', False, [list('QWERT'), list('ASDFG'), list('ZXCVB')], [[K] * 5, [M, M, M, M, K], [K] * 5],
     [('~MED', K), ('~NAV', K), ('~MOU', K)], 'LEFT HAND'),
    None, None,
    ('BTN', True, [CLIP_L, MODS_L, CLIP_L], [[K] * 5, MK_L, [K] * 5],
     [('@mouse_m', K), ('@mouse_l', K), ('@mouse_r', K)], 'HOLD Z OR /'),
    held_left('NAV', 'NUM', 'HOLD SPACE'), held_left('MOUSE', 'SYM', 'HOLD TAB'), held_left('MEDIA', 'FUN', 'HOLD ESC'),
    None, None, None,
]
LEFT_BY_ID[1] = ('EXTRA',) + LEFT_BY_ID[0][1:]
LEFT_BY_ID[2] = ('TAP', False, LEFT_BY_ID[0][2], [[K] * 5] * 3, [('~ESC', K), ('~SPC', K), ('~TAB', K)], 'NO MODS')
for i, nm, hint in [(7, 'NUM', 'HOLD BKSP'), (8, 'SYM', 'HOLD ENTER'), (9, 'FUN', 'HOLD DEL')]:
    lay = [l for l in LAYERS if l[0] == nm][0]
    LEFT_BY_ID[i] = (nm, True, lay[2], lay[3], lay[4], hint)

# Miryoku layer ids: 0 Base 1 Extra 2 Tap 3 Button 4 Nav 5 Mouse 6 Media 7 Num 8 Sym 9 Fun
BY_ID = [_by['BASE'], EXTRA, TAP, BUTTON, _by['NAV'], _by['MOUSE'], _by['MEDIA'], _by['NUM'], _by['SYM'], _by['FUN']]
RIGHT_BY_ID = list(BY_ID)            # own-hand version of the right screen
RIGHT_BY_ID[7] = held_right('NUM', 'NAV', 'HOLD BKSP')
RIGHT_BY_ID[8] = held_right('SYM', 'MOU', 'HOLD ENTER')
RIGHT_BY_ID[9] = held_right('FUN', 'MED', 'HOLD DEL')

def pairs_preview(path, S=3):
    FG, BG = (40, 44, 38), (196, 200, 186)
    lab = ImageFont.truetype(os.path.join(FD, 'DejaVuSans-Bold.ttf'), 18)
    sm = ImageFont.truetype(os.path.join(FD, 'DejaVuSans.ttf'), 13)
    order = [0, 4, 5, 6, 7, 8, 9, 3, 2, 1]
    outs = [('BLE', 1, 'CONNECTED'), ('BLE', 1, 'CONNECTED'), ('USB', 0, ''), ('BLE', 2, 'PAIRING'), ('BLE', 1, 'CONNECTED'),
            ('BLE', 1, 'CONNECTED'), ('BLE', 3, 'WAITING'), ('BLE', 1, 'CONNECTED'), ('BLE', 1, 'CONNECTED'), ('BLE', 1, 'CONNECTED')]
    pw = 2 * W * S + 10; cols = 5; gap = 26
    out = Image.new('RGB', (cols * (pw + gap) + gap, 2 * (H * S + 70) + 10), (250, 250, 248)); dd = ImageDraw.Draw(out)
    subs = {0: 'nothing held', 1: 'default layer', 2: 'default layer', 3: 'hold Z or /', 4: 'hold Space', 5: 'hold Tab',
            6: 'hold Esc', 7: 'hold Backspace', 8: 'hold Enter', 9: 'hold Delete'}
    for k, lid in enumerate(order):
        x = gap + (k % cols) * (pw + gap); y = 10 + (k // cols) * (H * S + 70)
        for j, (side, tab) in enumerate([('left', LEFT_BY_ID), ('right', RIGHT_BY_ID)]):
            n, h, g, kk, t, hint = tab[lid]
            im = screen(n, h, g, kk, t, hint, side=side, out=outs[k])
            rgb = Image.new('RGB', im.size); px = im.load(); q = rgb.load()
            for yy in range(H):
                for xx in range(W):
                    q[xx, yy] = BG if px[xx, yy] else FG
            out.paste(rgb.resize((W * S, H * S), Image.NEAREST), (x + j * (W * S + 10), y + 50))
        dd.text((x, y + 4), tab[lid][0].title(), font=lab, fill=(20, 20, 20))
        dd.text((x, y + 27), subs[lid] + '   (left | right)', font=sm, fill=(90, 90, 90))
    out.save(path)
    return out.size


if __name__ == '__main__':
    S = 4; pad = 18
    FG, BG = (40, 44, 38), (196, 200, 186)                    # memory-LCD look
    shots = [(n, screen(n, h, g, k, t, hint)) for n, h, g, k, t, hint in BY_ID]
    out = Image.new('RGB', (len(shots) * (W * S + pad) + pad, H * S + 60), (250, 250, 248))
    dd = ImageDraw.Draw(out); lab = ImageFont.truetype(os.path.join(FD, 'DejaVuSans-Bold.ttf'), 20)
    for i, (n, im) in enumerate(shots):
        rgb = Image.new('RGB', im.size); px = im.load(); q = rgb.load()
        for y in range(H):
            for x in range(W):
                q[x, y] = BG if px[x, y] else FG
        rgb = rgb.resize((W * S, H * S), Image.NEAREST)
        x = pad + i * (W * S + pad)
        out.paste(rgb, (x, 50))
        sub = {'BASE': 'nothing held', 'EXTRA': 'default (Extra)', 'TAP': 'default (Tap)', 'BUTTON': 'Z or /',
               'NAV': 'Space', 'MOUSE': 'Tab', 'MEDIA': 'Esc', 'NUM': 'Backspace', 'SYM': 'Enter',
               'FUN': 'Delete'}[n]
        dd.text((x, 8), n.title(), font=lab, fill=(20, 20, 20))
        dd.text((x, 30), 'hold: ' + sub, font=ImageFont.truetype(os.path.join(FD, 'DejaVuSans.ttf'), 14), fill=(90, 90, 90))
    out.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'docs', 'right_display_layers.png'))
    print(out.size)
