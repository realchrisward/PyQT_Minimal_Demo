# -*- coding: utf-8 -*-
"""
Minimal pyQT testbed

Created on Tue Mar  8 15:27:24 2022

@author: wardc
"""

#%% import libraries

#some of these might not be neccessary

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
import sys
import queue
import time
import subprocess
import os


#%% define classes

class PyQT_Demo(QMainWindow):
    def __init__(self):
        super(PyQT_Demo, self).__init__()
        
        # file selection window to get 'echo tester' script used with the demo
        # omitted for packaging demo self.path_to_script = QFileDialog.getOpenFileName()[0]
        
        self.rel_path_to_script = '"../echo tester/echo tester.exe"'
        
        self.win_path = "python"
        
        self.path_to_script = [self.win_path,'-u',self.rel_path_to_script]
        
        
        # set basic attributes
        self.setWindowTitle("PyQT_Demo Analysis Pipeline")
        self.isActiveWindow()
        self.setFixedSize(1000,1000)
        
        # add a button to run the SubProcess Thread Example
        self.Button_1 = QPushButton('Test Thread (Subprocess)', parent = self)
        self.Button_1.setFixedSize(200,25)
        self.Button_1.move(25,25)
        self.Button_1.clicked.connect(self.B1_launch)
        
        # add a button to run the Internal Method Example
        self.Button_2 = QPushButton('Test Thread (Internal)', parent = self)
        self.Button_2.setFixedSize(200,25)
        self.Button_2.move(250,25)
        self.Button_2.clicked.connect(self.B2_launch)
        
        # initialize the text window
        self.TextBox = QTextEdit('...Output Goes Here...', parent = self)
        self.TextBox.move(50,50)
        self.TextBox.setFixedSize(900,900)
        
        # create a queue, a counter to keep track of threads launched, and 
        # containers to hold workers and threads
        self.q = queue.Queue()
        self.counter=0
        self.threads = {}
        self.workers = {}
        
        # create a threadpool to help manage and limit the number of spawned
        # threads to a manageable number
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(8)
        
    
    
    # method triggered by Button_1 press
    @pyqtSlot()
    def B1_launch(self):
        # add text to the window indicating signal was received
        self.TextBox.append('...^^^...')
        # loop to simulate large amount of threads needed
        for i in range(10):
            # create a Worker
            self.workers[self.counter] = Worker(
                self.path_to_script,
                self.counter,
                self.q,
                self,
                'external'
                )
            self.workers[self.counter].signals.progress.connect(self.B_run)
            self.workers[self.counter].signals.finished.connect(self.B_Done)
            # Add the 'QRunnable' worker to the threadpool which will manage how
            # many are started at a time
            self.threadpool.start(self.workers[self.counter])
            
            self.counter+=1
    
    # method triggered by Button _2 press
    @pyqtSlot()
    def B2_launch(self):
        # add text to the window indicating signal was received
        self.TextBox.append('...^^^...')
        # loop to simulate large amount of threads needed
        for i in range(5):
            # create a Worker and pass it's 'run' method as the first argument
            self.workers[self.counter] = Worker(
                self.path_to_script,
                self.counter,
                self.q,
                self,
                'internal'
                )
            self.workers[self.counter].signals.progress.connect(self.B_run)
            self.workers[self.counter].signals.finished.connect(self.B_Done)
            # Add the 'QRunnable' worker to the threadpool which will manage how
            # many are started at a time
            self.threadpool.start(self.workers[self.counter])
            
            self.counter+=1
    
    
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_run is triggered by the worker's 'progress' signal
    
    @pyqtSlot(int)
    def B_run(self,worker_id):
        if not self.q.empty():
            self.TextBox.append(f'{worker_id} : {self.q.get_nowait()}')
            """
            note that if multiple workers are emitting their signals it is not
            clear which one will trigger the B_run method, though there should 
            be one trigger of the B_run method for each emission. It appears as
            though the emissions collect in a queue as well.
            If we care about matching the worker-id to the emission/queue 
            contents, I recommend loading the queue with tuples that include
            the worker id and the text contents
            """
    
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_Done is triggered by the worker's 'finished' signal
    @pyqtSlot(int)
    def B_Done(self,worker_id):
        self.TextBox.append('Worker_{} finished'.format(worker_id))
            
    
class WorkerSignals(QObject):
    # create the signals that the Worker can submit
    started = pyqtSignal(int)
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)
    
        


class Worker(QRunnable):
    
    def __init__(self,
                 path_to_script,
                 i,
                 worker_queue,
                 PyQT_Demo,
                 internal_or_external
                 ):
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.i = i
        self.worker_queue = worker_queue
        self.PyQT_Demo = PyQT_Demo
        self.internal_or_external = internal_or_external
    
        #import signals for later use
        self.signals = WorkerSignals()
        
    
    # threading is launched by the QThreadpool calling the run method
    def run(self):
        # demonstration of internal code running on a thread
        if self.internal_or_external == 'internal':
            for j in range(10):
                time.sleep(0.5)
                self.worker_queue.put(
                    f'Internal Threading Test-worker-{self.i} : {j}'
                    )
                self.signals.progress.emit(self.i)
            self.signals.finished.emit(self.i)

        else:
            #demonstration of external code running on a thread
            # use subprocess.Popen to run a seperate program in a new process
            # stdout will be captured by the variable self.echo and extracted below
            print(self.path_to_script+["-i","External Threading Test-WORKER-{self.i}"])
            self.echo = subprocess.Popen(self.path_to_script+["-i","External Threading Test-WORKER-{self.i}"],
                stdout= subprocess.PIPE, 
                stderr = subprocess.STDOUT,
                shell=True
                )
        
            # extract the stdout and feed it to the queue
            # emit signals whenever adding to the queue or finishing
            running = 1
            while running == 1:
                line = self.echo.stdout.readline().decode('utf8')
                if self.echo.poll() is not None:
                    running = 0
                elif line != '':
                    self.worker_queue.put(line.strip())
                    self.signals.progress.emit(self.i)
            self.signals.finished.emit(self.i)


#%% define main

def main():
    app = QApplication(sys.argv)
    window = PyQT_Demo()
    window.show()
    window.update()
    
    app.processEvents()
    app.exec_()


if __name__ == "__main__": 
    main()