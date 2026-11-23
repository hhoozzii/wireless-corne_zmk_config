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


def key(d, x, y, label, kind='key', w=12, h=12):
    """kind: key (outline), mod (filled, inverted label), none (dotted, empty)."""
    if kind == 'none':
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


def screen(layer, held, grid, kinds, thumbs, hint):
    im = blank(); d = ImageDraw.Draw(im)
    # --- top block (0..67): battery + link kept, layer badge replaces "corne"
    d.rectangle((2, 3, 30, 13), outline=0); d.rectangle((31, 6, 32, 10), fill=0); d.rectangle((4, 5, 22, 11), fill=0)
    text(d, 0, 2, 66, '      ' + ' ')  # spacing placeholder
    icon(d, 56, 4, 'bt')                 # link symbol (stands in for LV_SYMBOL_WIFI)
    text(d, 0, 22, W, 'linked')
    if held:
        d.rectangle((0, 38, W - 1, 63), fill=0); text(d, 0, 42, W, layer, font=F16, ink=1)
    else:
        d.rectangle((0, 38, W - 1, 63), outline=0); text(d, 0, 42, W, layer, font=F16, ink=0)
    # --- middle block (68..135): 5x3 grid at 14 px pitch + 3 thumbs
    y0 = 70
    for r in range(3):
        for c in range(5):
            key(d, c * 14, y0 + r * 14, grid[r][c], kinds[r][c])
    for i, (lab, kd) in enumerate(thumbs):
        key(d, i * 16 + (0 if hint.startswith('L') else 20), y0 + 45 + i, lab, kd, w=14, h=14)
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
    ('MEDIA', True,
     [['@sun', '~FX', '~HUE', '~SAT', '~BRI'], ['@bolt', '@prev', '@voldn', '@volup', '@next'],
      ['@usb', '~B0', '~B1', '~B2', '~B3']],
     [[K] * 5] * 3, [('@stop', K), ('@play', K), ('@mute', K)], 'HOLD ESC'),
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
BUTTON = ('BUTTON', True, [CLIP, [None, '~SH', '~CT', '~AL', '~GU'], CLIP], [[K] * 5, [N, M, M, M, M], [K] * 5],
          [('@mouse_r', K), ('@mouse_l', K), ('@mouse_m', K)], 'HOLD Z OR /')
# Miryoku layer ids: 0 Base 1 Extra 2 Tap 3 Button 4 Nav 5 Mouse 6 Media 7 Num 8 Sym 9 Fun
BY_ID = [_by['BASE'], EXTRA, TAP, BUTTON, _by['NAV'], _by['MOUSE'], _by['MEDIA'], _by['NUM'], _by['SYM'], _by['FUN']]

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
