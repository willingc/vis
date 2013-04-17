#! /usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Program Name:              vis
# Program Description:       Measures sequences of vertical intervals.
#
# Filename: vis_controller.py
# Purpose: Holds the VisController class, which maintains interactions between all
#          parts of vis.
#
# Copyright (C) 2012 Jamie Klassen, Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
'''
Holds the VisController class, which maintains interactions between all parts of vis.
'''


# Imports from...
# vis
from controllers.controller import Controller
from controllers.importer import Importer
from controllers.analyzer import Analyzer
from controllers.experimenter import Experimenter
from controllers.visualizer import Visualizer
from models.importing import ListOfFiles
from models.analyzing import ListOfPieces
from models.info import VisInfo
# PyQt4
from PyQt4.QtCore import pyqtSignal


class VisController(Controller):
   '''
   This class creates an interface and the various controllers required to run a vis
   implementation, and manages the interactions amongst them.

   TODO: doctest
   '''
   def __init__(self, argv, interface='PyQt4', details=None):
      
      active_controller_changed = pyqtSignal(str)
      info_signal = pyqtSignal()
      
      '''
      Create a new VisController instance.

      The first argument, "interface", is a string specifying which GUI to use:
      - 'PyQt4'
      - 'HTML5' (not implemented)
      - others?

      The second argument, "details", is a list of arguments specifying settings
      to be used when creating the specific interface. So far, there are none.
      '''
      super(Controller, self).__init__() # required for signals
      
      # Setup sub-controllers
      self.importer = Importer()
      self.analyzer = Analyzer()
      self.experimenter = Experimenter()
      self.visualizer = Visualizer()
      
      # Connect signals
      self.importer.thread.finished.connect(self.setup_analysis)
      self.analyzer.thread.finished.connect(self.setup_experiment)
      
      # Set instance variables
      self.importer.thread.list_of_pieces = self.analyzer.list_of_pieces
      self.info = VisInfo()
      self.active_controller = None
      
      if 'PyQt4' == interface:
         from interfaces.visqtinterface import VisQtInterface
         self.interface = VisQtInterface(self, argv)
      
      self.set_active_controller(self.importer)
   
   def exec_(self):
      '''
      Runs the application.
      '''
      return self.interface.exec_()
   
   def set_active_controller(self, value):
      if not self._active_controller is value:
         self._active_controller = value
         self.active_controller_changed.emit(value.__class__.__name__)
   
   def choose_files(self):
      '''
      Set the application to its initial state, clearing all the models except
      the ListOfFiles managed by self.importer.
      '''
      pieces_list = ListOfPieces()
      self.analyzer.list_of_pieces = pieces_list
      self.importer.thread.list_of_pieces = pieces_list
      # clear importer and visualizer?
      self.set_active_controller(self.importer)
   
   def import_files(self):
      '''
      Start importing the files contained in the self.importer's ListOfFiles.
      '''
      self.importer.thread.start()
   
   def setup_analysis(self):
      '''
      Set the application to its intermediate state, where users can define the
      settings for analyzing.
      '''
      # clear importer and visualizer?
      self.set_active_controller(self.analyzer)
   
   def analyze_pieces(self):
      '''
      Analyze the selected voice pairs in self.analyzer's ListOfPieces.
      '''
      self.analyzer.thread.start()
   
   def setup_experiment(self):
      '''
      Set the application to its intermediate state, where users can choose an
      experiment and define its settings before performing it.
      '''
      # clear visualizer?
      self.set_active_controller(self.experimenter)
   
   def get_info(self):
      '''
      Returns the VisInfo instance contained in this VisController.
      '''
      self.info_signal.emit()
      return self.info
# End class VisController ------------------------------------------------------
