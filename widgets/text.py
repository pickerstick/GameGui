"""The Text widget."""
from ..bases import Widget
from .._utils import blank_of_size,getdeffont
from ..cache import cdc
from collections import deque
LEFT = object()#unique
CENTER = object()
RIGHT = object()
class StyleChange:
    """Style change.
Avaliable kinds: StyleChange.AA    antialiasing change
                 StyleChange.LSP   line spacing change
                 StyleChange.COLOR color change"""
    AA = object()
    LSP = object()
    COLOR = object()
    def __init__(self,where,kind,new):
        self.where = where
        self.k = kind
        self.n = new
    def __lt__(self,other):#for sorting
        return self.where<other.where
    def __le__(self,other):
        return self.where<=other.where
    def __gt__(self,other):
        return not (self<=other)
    def __ge__(self,other):
        return not (self<other)
aac = StyleChange.AA
lspc = StyleChange.LSP
clrc = StyleChange.COLOR
atable = {
}
def render(it,t,sch,begini):
    sch = deque((i for i in sch if (begini <= i.where <= begini+len(t))))
    font = it.font
    segs = []
    token = ""
    for i,ch in enumerate(t,begini):
        if sch and sch[0].where == i:
            segs.append((token,sch.popleft()))
            token = ""
        token += ch
    if token:
        segs.append((token,None))
    sfc = []
    tw = 0
    mh = 0
    for seg,info in segs:
        sf = font.render(seg,it.aa,it.color)
        r = sf.get_rect()
        tw += r.width
        mh = max(mh,r.height)
        sfc.append((sf,r.width))
        if info:
            k = info.k
            if k is aac:
                it.aa = info.n
            elif k is lspc:
                it.lsp = info.n
            elif k is clrc:
                it.color = info.n
            else:
                raise ValueError(f"Unsupported text render style change type!")
    final = blank_of_size(tw,mh)
    i = 0
    cw = 0
    for s,w in sfc:
        final.blit(s,(cw,0))
        cw += w
    return final
class Dummy:
    def __init__(self,other):
        self.__thingy = other
    def __getattr__(self,attr):
        return getattr(self.__thingy,attr)
class Text(Widget):
    """A text label.
text specifies initial text,
w,h specifies dimensions,
color specifies the text color(foreground),
font specifies the font to use,
antialiased specifies if antialiasing should be enabled,
align specifies the align style(LEFT,CENTER,RIGHT), and
linespacing specifies the space between lines."""
    @staticmethod
    def unfocusable():
        return True
    def __init__(self,text="",w=500,h=500,
                 color=(255,255,255),font=None,antialiased=True,
                 align=LEFT,linespacing=1,stylechanges=()):
        if font is None:
            font = getdeffont()
        self.content = text
        self.font = font
        self.color = color
        self.aa = antialiased
        self.align = align
        self.width = w
        self.height = h
        self.cursor = -1
        self.lsp = linespacing
        self.sch = list(stylechanges)
        self.TH = self.HTH = 0
    def settext(self,text):
        self.content = text
    def get_surface(fles):
        self = Dummy(fles)#Won't change color, font etc. forever
        lines = []
        ht = 0
        i = 0
        cursor = None
        cotl = self.cursor
        whereisthecursor = 0
        ssch = tuple(sorted(self.sch))
        charh = -1
        for lnc,line in enumerate(self.content.split("\n")):
            small = i<self.cursor
            if i==self.cursor:
                whereisthecursor = lnc
                cursor = (0,ht)
            ln = render(self,line,ssch,i)
            i += len(line)+1
            if (cursor is None) and small and i>self.cursor:
                whereisthecursor = lnc
                leftie = 0
                for j in range(cotl):
                    leftie += cdc.get(self.font,line[j],self.aa).width
                cursor = (leftie,ht)
                charh = ln.get_rect().height
            cotl -= len(line)+1
            lines.append((ln,ht))
            ht += ln.get_rect().height+self.lsp
        lh = ln.get_rect().height
        if charh==-1:
            charh = cdc.get(self.font,"|",self.aa).height
        if ssch and (ssch[-1].k is clrc):
            self.color = ssch[-1].n
        if ht:
            ht -= self.lsp
        if (cursor is None) and self.cursor!=-1:
            cursor = (ln.get_rect().width,ht-charh)
            whereisthecursor = lnc
        sf = self.blank()
        fles.TH = ht#modify the 'real self'
        fles.HTH = ht//2
        xdiff = 0
        for i,(lnsf,y) in enumerate(lines):
            if self.align is LEFT:
                x = 0
            elif self.align is CENTER:
                rect = lnsf.get_rect()
                rect.centerx = self.width//2
                x = rect.left
            elif self.align is RIGHT:
                rect = lnsf.get_rect()
                rect.right = self.width
                x = rect.left
            else:
                raise ValueError(f"Invalid align:{self.align}")
            if cursor is not None and whereisthecursor == i:
                xdiff = x
            sf.blit(lnsf,(x,y))
        if cursor is not None:
            sf.fill(self.color,(cursor[0]+xdiff,cursor[1],2,charh))
        return sf
    def get_extra(self):
        return {"TH":self.TH,"HTH":self.HTH}
