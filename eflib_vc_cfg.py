import re


def pfxRange(a, pfx, start=0):
    """Return the index range of the first continuous range of list items
    starting with a prefix, or (0,0) if none found."""
    beg = None
    end = None
    for i, s in enumerate(a[start:]):
        if beg is None:
            if s.startswith(pfx):
                beg = i
        else:
            if not s.startswith(pfx):
                end = i
                break
    if beg is None:
        return (0, 0)
    if end is None:
        end = len(a)
    return (beg, end)
    


class Project:

    def __init__(self):
        self.header = None
        self.configs = None
        self.target = None

        self.name = ''
        self.targType = ''


    def read(self, f):
        """Read project from an open file."""
        
        a = [s.rstrip('\n') for s in f.readlines()]
    
        self.header = []
        while a and not a[0].startswith('!IF'):
            self.header += [a.pop(0)]

        self.configs = []
        while a and not a[0].startswith('# Begin Target'):
            self.configs += [a.pop(0)]
        self._splitCfgs()

        self.target = a

        # get some project attributes from header
        self.name = re.search(r'Name="(.*?)"', self.header[0]).group(1)
        for s in self.header:
            if s.startswith('# TARGTYPE '):
                self.targType = re.search(r'"(.*?)"', s).group(1)
                break


    def write(self, f):
        """Write project to san open file."""

        writeLn = lambda s: f.write(s + '\n')
        
        for s in self.header:
            writeLn(s)

        for i, cfg in enumerate(self.configs):
            s = '!%sIF  "$(CFG)" == "%s"' % (('ELSE' if i else ''), cfg[0])
            writeLn(s)
            for s in cfg[1]:
                writeLn(s)
        writeLn('!ENDIF ')
        writeLn('')
    
        for s in self.target:
            writeLn(s)


    def _splitCfgs(self):
        """Split the whole cfg IF block to a list of (name, lines)."""
        res = []
        cfgCaseRx = re.compile(r'^!(?:ELSE)?IF  "\$\(CFG\)" == "(.+)"$')
        for s in self.configs:
            if s == '!ENDIF ':
                break
            m = cfgCaseRx.match(s)
            if m:
                res.append([m.group(1), []])
                continue
            res[-1][1] += [s]
        self.configs = res


    def getCfgType(self, type):
        cfgTypeRx = re.compile(r'^' + re.escape(self.name) + r' - Win32 (.*)$')
        for name, lines in self.configs:
            if cfgTypeRx.match(name).group(1) == type:
                return name, lines
        raise IndexError('Could not find cfg: ' + type)


    def setTargetNames(self, a):
        nameLinePfx = '# Name '
        beg, end = pfxRange(self.target, nameLinePfx)
        self.target[beg:end] = [nameLinePfx + '"' + s + '"' for s in a]

        # also set in header msg
        # (VS6 will crash if these are invalid)
        i = self.header.index('!MESSAGE Possible choices for configuration are:')
        i += 2  # skip the above + 1 blank
        beg, end = pfxRange(self.header, '!MESSAGE "')
        self.header[beg:end] = [
            '!MESSAGE "%s" (based on "%s")' % (s, self.targType) for s in a]


    def setDefaultCfg(self, cfgName):
        for i, s in enumerate(self.header):
            if s.startswith('CFG='):
                self.header[i] = 'CFG=' + cfgName


def modifyCfg(cfg, libPfx, debug, codepage, multithread, dynCRuntime):
    if not multithread and dynCRuntime:
        raise Exception('modifyCfg -> not multithread and dynCRuntime')
    
    name, lines = cfg[0], cfg[1][:]

    id = ''
    id += 'Dbg' if debug else 'Rel'
    id += ' ' + codepage.upper()
    id += ' MT' if multithread else ' ST'
    id += ' dCRT' if dynCRuntime else ' sCRT'

    name = name.replace('Debug' if debug else 'Release', id)

    propOutDir = '# PROP Output_Dir '
    propIntDir = '# PROP Intermediate_Dir '
    cppOpt = '# ADD CPP '
    libOpt = '# ADD LIB32 '

##    outDir = '..\\bin\\'
##    outDir += 'dbg' if debug else 'rel'
##    outDir += '_uc' if unicode else ''
##    outDir += '_mt' if multithread else ''

    intDir = 'obj\\' + id.lower().replace(' ', '_')
    outDir = intDir

    outLib = '..\\bin\\' + libPfx + '_'
    outLib += id.lower().replace(' ', '_')
    outLib += '.lib'

    mbcsDef = '/D "_MBCS"'
    defs = []
    defs += ['_UNICODE', 'UNICODE'] if codepage == 'u' else ['_MBCS'] if codepage == 'm' else []
    defs += ['_MT'] if multithread else []
    defs += ['_DLL'] if dynCRuntime else []
    defs = [('/D "%s"' % s) for s in defs]
    defs = ' '.join(defs)

    libSwitch = ' /M'
    libSwitch += 'D' if dynCRuntime else 'T' if multithread else 'L'
    libSwitch += 'd' if debug else ''

    for i, s in enumerate(lines):
        if s.startswith(propOutDir):
            lines[i] = propOutDir + '"' + outDir + '"'
        elif s.startswith(propIntDir):
            lines[i] = propIntDir + '"' + intDir + '"'
        elif  s.startswith(cppOpt):
            lines[i] = s.replace(mbcsDef, defs)
            logoSwitch = '/nologo'
            pos = lines[i].index(logoSwitch) + len(logoSwitch)
            lines[i] = strInsert(lines[i], pos, libSwitch)
        elif  s.startswith(libOpt):
            lines[i] = libOpt + '/nologo /out:"%s"' % outLib

    return [name, lines]


def strInsert(s, i, ins):
    return s[:i] + ins + s[i:]


def modifyProject(dspFile, libPfx):
    prj = Project()
    with file(dspFile + '.ORG') as f:
        prj.read(f)

    cfgs = []
    templateCfgs = {False:prj.getCfgType('Release'),
                    True:prj.getCfgType('Debug')}
    bools = (False, True)
    cps = ('a', 'm', 'u')
    for dynCRuntime in bools:
        for multithread in bools:
            for codepage in cps:
                for debug in bools:
                    # dyn C-RTL must be multithreaded
                    if dynCRuntime and not multithread:
                        continue
                    cfgs.append(modifyCfg(templateCfgs[debug], libPfx,
                                          debug, codepage, multithread,
                                          dynCRuntime))
    prj.configs = cfgs
    prj.setTargetNames([c[0] for c in cfgs])
    prj.setDefaultCfg(cfgs[0][0])

    with file(dspFile, 'w') as f:
        prj.write(f)
        

#modifyProject(r'D:\Projects\libs\eflib\vs6\std\std.dsp', 'efstd')
modifyProject(r'D:\Projects\libs\eflib\vs6\win\win.dsp', 'efwin')

##Rel | U | St LibC
##Dbg | A | St DynC
##    | M | Mt DynC
##
##efstd_Rel_U_MT_DynC
