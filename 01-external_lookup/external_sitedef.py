#!/usr/bin/env python
# coding : utf-8


import sys
import csv
import ConfigParser
import re


DEFAULTSECT = "DEFAULT"
MAX_INTERPOLATION_DEPTH = 10


# The _read method has been rewritten to handle option starting with a space in the INI file
class LazyConfigParser(ConfigParser.ConfigParser):
    
    disable_multiline = True

    def _read(self, fp, fpname):
        """Parse a sectioned setup file.

        The sections in setup file contains a title line at the top,
        indicated by a name in square brackets (`[]'), plus key/value
        options lines, indicated by `name: value' format lines.
        Continuations are represented by an embedded newline then
        leading whitespace.  Blank lines, lines beginning with a '#',
        and just about everything else are ignored.
        """
        cursect = None                        # None, or a dictionary
        optname = None
        lineno = 0
        e = None                              # None, or an exception
        while True:
            line = fp.readline()
            if not line:
                break
            lineno = lineno + 1
            # comment or blank line?
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                # no leading whitespace
                continue
            # continuation line?
            if not self.disable_multiline and line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    cursect[optname].append(value)
            # a section header or option header?
            else:
                # is it a section header?
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == DEFAULTSECT:
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        cursect['__name__'] = sectname
                        self._sections[sectname] = cursect
                    # So sections can't start with a continuation line
                    optname = None
                # no section header in the file?
                elif cursect is None:
                    raise MissingSectionHeaderError(fpname, lineno, line)
                # an option line?
                else:
                    mo = self._optcre.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        optname = self.optionxform(optname.rstrip())
                        # This check is fine because the OPTCRE cannot
                        # match if it would set optval to None
                        if optval is not None:
                            if vi in ('=', ':') and ';' in optval:
                                # ';' is a comment delimiter only if it follows
                                # a spacing character
                                pos = optval.find(';')
                                if pos != -1 and optval[pos-1].isspace():
                                    optval = optval[:pos]
                            optval = optval.strip()
                            # allow empty values
                            if optval == '""':
                                optval = ''
                            cursect[optname] = [optval]
                        else:
                            # valueless option handling
                            cursect[optname] = optval
                    else:
                        # a non-fatal parsing error occurred.  set up the
                        # exception but keep going. the exception will be
                        # raised at the end of the file and will contain a
                        # list of all bogus lines
                        if not e:
                            e = ParsingError(fpname)
                        e.append(lineno, repr(line))
        # if any parsing errors occurred, raise an exception
        if e:
            raise e

        # join the multi-line values collected while reading
        all_sections = [self._defaults]
        all_sections.extend(self._sections.values())
        for options in all_sections:
            for name, val in options.items():
                if isinstance(val, list):
                    options[name] = '\n'.join(val)

    OPTCRE = re.compile(
        r'\s*(?P<option>[^:=\s][^:=]*)'          # very permissive!
        r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
                                              # followed by separator
                                              # (either : or =), followed
                                              # by any # space/tab
        r'(?P<value>.*)$'                     # everything up to eol
        )


def main():
    if len(sys.argv) != 5:
        print 'Usage: python external_lookup.py [pagename field] [status field] [object field] [metaclass field]'
        sys.exit(1)

    pagenamefield = sys.argv[1]
    statusfield = sys.argv[2]
    objectfield = sys.argv[3]
    metaclassfield = sys.argv[4]

    # Load the INI file
    sitedef = LazyConfigParser()
    sitedef.read('./SiteDef.ini')

    infile = sys.stdin
    outfile = sys.stdout

    r = csv.DictReader(infile)
    header = r.fieldnames

    w = csv.DictWriter(outfile, fieldnames=header)
    w.writeheader()

    for result in r:
        page = result[pagenamefield]
        print result
        if page:
            if sitedef.has_section(page):
		if sitedef.has_option(page, 'available'):
                    result[statusfield] = sitedef.get(page, 'available')
		if sitedef.has_option(page, 'object'):
                    result[objectfield] = sitedef.get(page, 'object').decode('iso8859_15')
		if sitedef.has_option(page, 'metaclass'):
                    result[metaclassfield] = sitedef.get(page, 'metaclass').decode('iso8859_15')
                w.writerow(result)


if __name__ == "__main__":
    main()
