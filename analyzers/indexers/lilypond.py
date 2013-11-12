#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/indexers/lilypond.py
# Purpose:                LilyPondIndxexer
#
# Copyright (C) 2013 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""
.. codeauthor:: Christopher Antila <crantila@fedoraproject.org>

The :class:`LilyPondIndexer` uses the :mod:`OutputLilyPond` module to produces the LilyPond file
that should produce a score of the input.
"""

import pandas
from music21 import stream, note, duration
from OutputLilyPond import OutputLilyPond
from OutputLilyPond.LilyPondSettings import LilyPondSettings
from vis.analyzers import indexer


def annotation_func(obj):
    """
    Used by :class:`AnnotationIndexer` to make a "markup" command for LilyPond scores.

    Parameters
    ==========
    :param obj: A single-element :class:`Series` with the string to wrap in a "markup" command.
    :type obj: :class:`pandas.Series` of ``unicode``

    Returns
    =======
    :returns: The thing in a markup.
    :rtype: ``unicode``
    """
    return u''.join([u'_\markup{ "', unicode(obj[0]), u'" }'])


def annotate_the_note(obj):
    """
    Used by :class:`AnnotateTheNoteIndexer` to make a :class:`~music21.note.Note` object with the
    annotation passed in. Take note (hahaha): the ``lily_invisible`` property is, by default,
    set to ``True``!

    Parameters
    ==========
    :param obj: A single-element :class:`Series` with the string to put as the ``lily_markup``
        property of a new :class:`Note`
    :type obj: :class:`pandas.Series` of ``unicode``

    Returns
    =======
    :returns: The new Note!
    :rtype: :class:`music21.note.Note`
    """
    post = note.Note()
    post.lily_invisible = True
    post.lily_markup = obj[0]
    return post


class LilyPondIndexer(indexer.Indexer):
    """
    Use the :mod:`OutputLilyPond` module to produce the LilyPond file that should produce a score
    of the input.

    .. note:: The class currently only works for the first :class:`IndexedPiece` given.
    """

    required_score_type = stream.Score
    """
    You must provide a :class:`music21.stream.Score` to this Indexer.
    """

    possible_settings = [u'run_lilypond', u'output_pathname', u'annotation part']
    """
    Possible settings for the :class:`LilyPondIndexer` include:

    :keyword u'run_lilypond': Whether to run LilyPond; if ``False`` or omitted, simply produce the \
        input file LilyPond requires.
    :type u'run_lilypond': boolean

    :keyword u'output_pathname': Pathname for the resulting LilyPond output file. If \
        ``u'run_lilypond'`` is ``True``, you must include this setting. If u'run_lilypond' is \
        ``False`` and you do not provide ``u'output_pathname'`` then the output file is returned \
        by :meth:`run` as a ``unicode``.
    :type u'output_pathname': ``basestring``

    :keyword u'annotation_part': A :class:`Part` with annotation instructions for
        :mod:`OutputLilyPond`. This :class:`Part` will be appended as last in the :class:`Score`.
    :type u'annotation_part': :class:`music21.stream.Part`
    """

    default_settings = {u'run_lilypond': False, u'output_pathname': None, u'annotation_part': None}
    """
    Default settings.
    """

    # error message for when settings say to run LilyPond, but we have no pathname
    error_no_pathname = u'LilyPondIndexer cannot run LilyPond without saving output to a file.'

    def __init__(self, score, settings=None):
        """
        Parameters
        ==========
        :param score: The :class:`Score` object to output to LilyPond.
        :type score: singleton list of :class:`music21.stream.Score`

        :param settings: All required settings.
        :type settings: ``dict`` or :dict:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if ``score`` is the wrong type.
        :raises: :exc:`RuntimeError` if ``score`` is not a list of the same types.
        :raises: :exc:`RuntimeError` if required settings are not present in ``settings``.
        :raises: :exc:`RuntimeError` if ``u'run_lilypond'`` is ``True`` but ``u'output_pathname'`` \
            is unspecified.
        """
        settings = {} if settings is None else settings
        self._settings = {}
        if u'run_lilypond' in settings and settings[u'run_lilypond'] is True:
            if u'output_pathname' in settings:
                self._settings[u'run_lilypond'] = True
                self._settings[u'output_pathname'] = settings[u'output_pathname']
            else:
                raise RuntimeError(LilyPondIndexer.error_no_pathname)
        elif u'output_pathname' in settings:
            self._settings[u'run_lilypond'] = LilyPondIndexer.default_settings[u'run_lilypond']
            self._settings[u'output_pathname'] = settings[u'output_pathname']
        else:
            self._settings[u'run_lilypond'] = LilyPondIndexer.default_settings[u'run_lilypond']
            self._settings[u'output_pathname'] = LilyPondIndexer.default_settings[u'output_pathname']
        self._settings[u'annotation_part'] = settings[u'annotation_part'] if u'annotation_part' in \
            settings else LilyPondIndexer.default_settings[u'annotation_part']
        super(LilyPondIndexer, self).__init__(score, None)
        # We won't use an indexer function; run() is just going to pass the Score to OutputLilyPond
        self._indexer_func = None

    def run(self):
        """
        Make a string with the LilyPond representation of each score. Run LilyPond, if we're
        supposed to.

        Returns
        =======
        :returns: A list of strings, where each string is the LilyPond-format representation of the
            score that was in that index.
        :rtype: ``list`` of ``unicode``
        """
        # TODO: make this work with more than one file
        lily_setts = LilyPondSettings()
        # append analysis part, if present
        if self._settings[u'annotation_part'] is not None:
            self._score[0].insert(0, self._settings[u'annotation_part'][0])  # TODO: when it works for more than one file, we shouldn't need these [0] things either
        # because OutputLilyPond uses multiprocessing by itself, we'll just call it in series
        the_score = OutputLilyPond.process_score(self._score[0], lily_setts)
        # call LilyPond on each file, if required
        if self._settings[u'run_lilypond'] is True:
            with open(self._settings[u'output_pathname'], 'w') as handle:
                handle.write(the_score)
            OutputLilyPond._run_lilypond(self._settings[u'output_pathname'], lily_setts)
        return the_score


class AnnotationIndexer(indexer.Indexer):
    """
    From any other index, put ``_\markup{""}`` around it.
    """

    required_score_type = pandas.Series
    possible_settings = []  # TODO: add a setting for whether _ or - or ^ before \markup
    default_settings = {}

    def __init__(self, score, settings=None):
        """
        Parameters
        ==========
        :param score: The input from which to produce a new index.
        :type score: ``list`` of :class:`pandas.Series`

        :param settings: Nothing.
        :type settings: ``dict`` or :const:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if ``score`` is the wrong type.
        :raises: :exc:`RuntimeError` if ``score`` is not a list of the same types.
        """
        super(AnnotationIndexer, self).__init__(score, None)
        self._indexer_func = annotation_func

    def run(self):
        """
        Make a new index of the piece.

        Returns
        =======
        :returns: A list of the new indices. The index of each :class:`Series` corresponds to the
            index of the :class:`Part` used to generate it, in the order specified to the
            constructor. Each element in the :class:`Series` is a ``basestring``.
        :rtype: ``list`` of :class:`pandas.Series`
        """
        # Calculate each part separately:
        combinations = [[x] for x in xrange(len(self._score))]
        return self._do_multiprocessing(combinations)


class AnnotateTheNoteIndexer(indexer.Indexer):
    """
    Make a new :class:`~music21.note.Note` object with the input set to the ``lily_markup``
    property, the ``lily_invisible`` property set to ``True``, and everything else as a default
    :class:`Note`.
    """

    required_score_type = pandas.Series
    possible_settings = []  # TODO: maybe how to set lily_invisible?
    default_settings = {}

    def __init__(self, score, settings=None):
        """
        Parameters
        ==========
        :param score: The input from which to produce a new index.
        :type score: ``list`` of :class:`pandas.Series`

        :param settings: Nothing.
        :type settings: ``dict`` or :const:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if ``score`` is the wrong type.
        :raises: :exc:`RuntimeError` if ``score`` is not a list of the same types.
        """
        super(AnnotateTheNoteIndexer, self).__init__(score, None)
        self._indexer_func = annotate_the_note

    def run(self):
        """
        Make a new index of the piece.

        Returns
        =======
        :returns: A list of the new indices. The index of each :class:`Series` corresponds to the
            index of the :class:`Part` used to generate it, in the order specified to the
            constructor. Each element in the :class:`Series` is a ``basestring``.
        :rtype: ``list`` of :class:`pandas.Series`
        """
        # Calculate each part separately:
        combinations = [[x] for x in xrange(len(self._score))]
        return self._do_multiprocessing(combinations)


class PartNotesIndexer(indexer.Indexer):
    """
    From a :class:`Series` full of :class:`Note` objects, craft a :class:`music21.stream.Part`. The
    offset of each :class:`Note` in the output matches its index in the input :class:`Series`, and
    each ``duration`` property is set to match.
    """

    required_score_type = pandas.Series
    possible_settings = []
    default_settings = {}

    def __init__(self, score, settings=None):
        """
        Parameters
        ==========
        :param score: The input from which to produce a new index.
        :type score: ``list`` of :class:`pandas.Series` of :class:`music21.note.Note`

        :param settings: Nothing.
        :type settings: ``dict`` or :const:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if ``score`` is the wrong type.
        :raises: :exc:`RuntimeError` if ``score`` is not a list of the same types.
        """
        super(PartNotesIndexer, self).__init__(score, None)
        self._indexer_func = annotate_the_note

    @staticmethod
    def _fill_space_between_offsets(start_o, end_o):
        """
        Given two offsets, finds the ``quarterLength`` values that fill the whole duration.

        Parameters
        ==========
        :param start_o: The starting offset.
        :type start_o: ``float``
        :param end_o: The ending offset.
        :type end_o: ``float``

        Returns
        =======
        :returns: The ``quarterLength`` values that fill the whole duration (see below).
        :rtype: ``list`` of ``float``

        The algorithm tries to use as few ``quarterLength`` values as possible, but prefers multiple
        values to a single dotted value. The longest single value is ``4.0`` (a whole note).
        """
        # TODO: rewrite this as a single recursive function
        # TODO: port the tests from vis9d
        def highest_valid_ql(rem):
            """
            Returns the largest quarterLength that is less "rem" but not greater than 2.0
            """
            # Holds the valid quarterLength durations from whole note to 256th.
            list_of_durations = [2.0, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0]
            # Easy terminal condition
            if rem in list_of_durations:
                return rem
            # Otherwise, we have to look around
            for dur in list_of_durations:
                if dur < rem:
                    return dur

        def the_solver(ql_remains):
            """
            Given the "quarterLength that remains to be dealt with," this method returns
            the solution.
            """
            if 4.0 == ql_remains:
                # Terminal condition, just return!
                return [4.0]
            elif 4.0 > ql_remains >= 0.0:
                if 0.015625 > ql_remains:
                    # give up... ?
                    return [ql_remains]
                else:
                    possible_finish = highest_valid_ql(ql_remains)
                    if possible_finish == ql_remains:
                        return [ql_remains]
                    else:
                        return [possible_finish] + \
                        the_solver(ql_remains - possible_finish)
            elif ql_remains > 4.0:
                return [4.0] + the_solver(ql_remains - 4.0)
            else:
                msg = u'Impossible quarterLength remaining: ' + unicode(ql_remains) + \
                    u'... we started with ' + unicode(start_o) + u' to ' + unicode(end_o)
                raise RuntimeError(msg)

        start_o = float(start_o)
        end_o = float(end_o)
        result = the_solver(end_o - start_o)
        #return (result[0], result[1:])  # NB: this was the previous "return" statement
        return result

    def run(self):
        """
        Make a new index of the piece.

        Returns
        =======
        :returns: A list of the new indices. The index of each :class:`Part` corresponds to the
            index of the :class:`Series` used to generate it, in the order specified to the
            constructor. Each element in the :class:`Part` is a :class:`Note`.
        :rtype: ``list`` of :class:`music21.stream.Part`
        """
        post = []
        for each_series in self._score:
            prev_offset = None
            new_part = stream.Part()
            new_part.lily_analysis_voice = True
            new_part.lily_instruction = u'\t\\textLengthOn\n'
            # put the Note objects into a new stream.Part, using the right offset
            for off, obj in each_series.iteritems():
                new_part.insert(off, obj)
            # set the duration for each Note event
            for i in xrange(len(new_part)):
                qls = None
                try:
                    qls = PartNotesIndexer._fill_space_between_offsets(new_part[i].offset,
                                                                        new_part[i + 1].offset)
                except stream.StreamException:  # when we access the after-the-last note
                    qls = [1.0]
                new_durat = duration.Duration(quarterLength=qls[0])
                for each_ql in qls[1:]:
                    pass  # TODO: what if there are more than one durations to fill the duration?
                new_part[i].duration = new_durat
            post.append(new_part)
        return post