#!/usr/bin/env python

from collections import OrderedDict
import logging
import os
import sys
import time
from StringIO import StringIO

from hipchat.hiplogging import HipChatHandler


class SMParser(object):

    TOKENS = (
        'TITLE', 'SUBTITLE', 'ARTIST',
        'TITLETRANSLIT', 'SUBTITLETRANSLIT',
        'ARTISTTRANSLIT', 'CREDIT', 'BANNER',
        'BACKGROUND', 'LYRICSPATH', 'CDTITLE',
        'MUSIC', 'OFFSET', 'SAMPLESTART',
        'SAMPLELENGTH', 'SELECTABLE', 'DISPLAYBPM',
        'BPMS', 'STOPS', 'BGCHANGES',
    )

    BOM_CHAR = '\xef\xbb\xbf'

    SECTION_HEADER = '//--'

    STYLES = ('dance-single', 'dance-double')
    DIFFICULTIES = ('Easy', 'Medium', 'Hard')
    FOOT_RATINGS = range(1, 11)
    STEP_TYPES = '0123'

    def __init__(self, simfile):
        self.charts = {}
        self._simfile = simfile
        self._parse_header_tokens()
        self._parse_sections()

    def _parse_header_tokens(self):
        for line in StringIO(self._simfile):
            try:
                token, value = (line.strip()
                                .replace(self.BOM_CHAR, '')
                                .split(':')[:2])
            except ValueError:
                continue
            if token[1:] in self.TOKENS:
                setattr(self, token[1:], value.strip(';'))
            if token[1:] == 'BPMS':
                self.BPMS = OrderedDict([measure.split('=') for measure
                                         in self.BPMS.split(',')])
            elif line.startswith(self.SECTION_HEADER):
                break

    def _parse_sections(self):

        def _dos_to_unix(s):
            return s.replace('\r', '')

        parsing = False
        parsing_measure = False
        measure_counter = 1

        for line in StringIO(self._simfile):
            line = _dos_to_unix(line.strip())

            if not parsing and not line.startswith(self.SECTION_HEADER):
                continue

            elif line.startswith(self.SECTION_HEADER):
                # parse section header
                parsing = True
                style = 'Double' if 'double' in line else 'Single'
                self.charts[style] = self.charts.setdefault(style, {})

            elif parsing and ':' in line:
                # Parse #INFO section
                value = line.split(':')[0]
                if value in self.DIFFICULTIES:
                    difficulty = value
                    self.charts[style][difficulty] = {}
                elif value in self.FOOT_RATINGS:
                    self.charts[style][difficulty]['foot rating'] = value
                elif ',' in value:
                    self.charts[style][difficulty]['?'] = value

            elif all((c in self.STEP_TYPES for c in line)) and line != '':
                # parse individual measures
                if parsing_measure:
                    measure['steps'].append(line)
                else:
                    measure = {'measure': measure_counter, 'steps': [line]}
                    parsing_measure = True
                self.charts[style][difficulty]['chart'] = self.charts[style][
                    difficulty].setdefault('chart', [])

            elif line.startswith(',') and parsing_measure:
                # stop parsing measure
                self.charts[style][difficulty]['chart'].append(measure)
                parsing_measure = False
                measure_counter += 1

            elif line.startswith(';') and parsing:
                # stop parsing section
                parsing, parsing_measure = False, False
                measure_counter = 1


class Logger(object):

    def __init__(self, hipchat_creds_file='~/.hipchat.yml'):
        self.hipchat_creds_file = hipchat_creds_file

    def _set_up_hipchat(self):
        """
        simple YAML-like parsing of :hipchat_creds_file. returns
        a HipChat logging handler.
        """
        with open(os.path.expanduser(self.hipchat_creds_file)) as fh:
            tokens = ('api_key', 'room', 'url')
            for line in fh:
                try:
                    k = line.split(':')[0]
                    v = ':'.join(line.split(':')[1:]).strip()
                except ValueError, IndexError:
                    continue

                if k in tokens:
                    exec('{0} = "{1}"'.format(k, v))

            try:
                api_key, room, url
            except NameError:
                raise ValueError("Need to set a value for :api_key, :room, "
                                 "and :url in {0}".format(
                                     self.hipchat_creds_file))

        return HipChatHandler(api_key, room, url)

    @property
    def logger(self):
        logger = logging.getLogger()
        loglevel = logging.INFO
        logger.setLevel(loglevel)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)

        logger.addHandler(ch)
        logger.addHandler(self._set_up_hipchat())

        return logger


class Simulator(object):

    def __init__(self, simfile, logger):
        self.sm = simfile
        self.logger = logger

    def step_to_arrow(self, step):
        graphical_arrow = ''
        for i, arrow in enumerate(step):
            if int(arrow) > 0:
                if i == 0 or i == 4:
                    graphical_arrow += "(ddrleft)"
                if i == 1 or i == 5:
                    graphical_arrow += "(ddrdown)"
                if i == 2 or i == 6:
                    graphical_arrow += "(ddr)"
                if i == 3 or i == 7:
                    graphical_arrow += "(ddrright)"
            else:
                graphical_arrow += '_' * 4

        return graphical_arrow

    def loop(
            self, style, difficulty, beat_multiplier=1,
            speed_mod=1, correct_spacing=False):
        # just support a single BPM for now.
        bpm = self.sm.BPMS.values()[0]

        beats_per_second = float(bpm) / 60
        beats_per_measure = 4
        seconds_per_measure = beats_per_measure / beats_per_second
        chart = self.sm.charts[style][difficulty]['chart']

        # arrows can't subdivide lines, so the width between
        # arrows must be variable based on the measure with the
        # highest step count: e.g. an eighth note looks like:
        #
        # ['0000', '0001', '0000', '0000',
        #  '0000', '0010', '0000'. '0000']
        #
        # so with that as the measure with the highest step
        # count, the spacing would look like:
        # ____
        # ___*
        # ____
        # ____
        # ____
        # __*_
        # ____
        # ____
        #
        # this gets pretty gnarly for heavy charts, so it is
        # disabled by default with :correct_spacing == False.
        measure_length_multiplier = len(max(
            chart, key=lambda k: len(k['steps']))['steps'])

        self.logger.info("A-a-are a-a-a-are you ready!?")
        for measure in chart:
            time_divisor = seconds_per_measure / len(measure['steps'])
            for step in measure['steps']:
                if step in ('0000', '00000000'):
                    for mod in xrange(0, speed_mod *
                                         (measure_length_multiplier
                                          if correct_spacing else 1)):
                        self.logger.info('____' * len(step))
                else:
                    arrows = self.step_to_arrow(step)
                    self.logger.info(arrows)
                time.sleep(time_divisor * beat_multiplier)

USAGE = """
Usage: {0} :simfile :style :difficulty :speed_mod :song_speed_multiplier

:simfile:               Max300.sm
:style:                 Single|Double
:difficulty:            Easy|Medium|Hard
:speed_mod:             x1|x2|x3|...
:song_speed_multiplier: 1|2|3|...
""".format(sys.argv[0])

def main():
    try:
        (simfile, style, difficulty, speed_mod,
         song_speed_multiplier) = sys.argv[1:]

        simfile = open(simfile).read()
        speed_mod = int(speed_mod.strip('x'))
        song_speed_multiplier = int(song_speed_multiplier)

    except (IndexError, IOError, ValueError):
        print >> sys.stderr, USAGE
        return 1

    simulator = Simulator(SMParser(simfile), Logger().logger)

    simulator.loop(style, difficulty, song_speed_multiplier, speed_mod)

if __name__ == "__main__":
    sys.exit(main())
