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


#%% define classes

class PyQT_Demo(QMainWindow):
    def __init__(self):
        super(PyQT_Demo, self).__init__()
        
        # file selection window to get 'echo tester' script used with the demo
        self.path_to_script = QFileDialog.getOpenFileName()[0]
        
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
        
    # method triggered by Button_1 press
    @pyqtSlot()
    def B1_launch(self):
        # add text to the window indicating signal was received
        self.TextBox.append('...^^^...')
        # create a QThread object
        self.threads[self.counter] = QThread()
        # create a Worker
        self.workers[self.counter] = Worker(self.path_to_script,self.counter,self.q)
        # move worker to thread
        self.workers[self.counter].moveToThread(self.threads[self.counter])
        # connect signals and slots
        self.threads[self.counter].started.connect(self.workers[self.counter].run_external)
        self.workers[self.counter].finished.connect(self.threads[self.counter].quit)
        self.workers[self.counter].finished.connect(self.workers[self.counter].deleteLater)
        self.threads[self.counter].finished.connect(self.threads[self.counter].deleteLater)
        self.workers[self.counter].progress.connect(self.B_run)
        self.workers[self.counter].finished.connect(self.B_Done)
        # start the thread
        self.threads[self.counter].start()
        # advance the counter - used to test launching multiple threads
        self.counter+=1
    
    # method triggered by Button _2 press
    @pyqtSlot()
    def B2_launch(self):
        # add text to the window indicating signal was received
        self.TextBox.append('...###...')
        # create a QThread object
        self.threads[self.counter] = QThread()
        # create a Worker
        self.workers[self.counter] = Worker(self.path_to_script,self.counter,self.q)
        # move worker to thread
        self.workers[self.counter].moveToThread(self.threads[self.counter])
        # connect signals and slots
        self.threads[self.counter].started.connect(self.workers[self.counter].run_internal)
        self.workers[self.counter].finished.connect(self.threads[self.counter].quit)
        self.workers[self.counter].finished.connect(self.workers[self.counter].deleteLater)
        self.threads[self.counter].finished.connect(self.threads[self.counter].deleteLater)
        self.workers[self.counter].progress.connect(self.B_run)
        self.workers[self.counter].finished.connect(self.B_Done)
        # start the thread
        self.threads[self.counter].start()
        # advance the counter - used to test launching multiple threads
        self.counter+=1
        
    
    
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_run is triggered by the worker's 'progress' signal
    @pyqtSlot(int)
    def B_run(self,worker_id):
        while not self.q.empty():
            self.TextBox.append(f'{worker_id} : {self.q.get_nowait()}')
    
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_Done is triggered by the worker's 'finished' signal
    @pyqtSlot(int)
    def B_Done(self,worker_id):
        self.TextBox.append('Worker_{} finished'.format(worker_id))
            
    
    
        


class Worker(QObject):
    # create the signals that the Worker can submit
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)
    
    def __init__(self,path_to_script,i,worker_queue):
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.i = i
        self.worker_queue = worker_queue
        self.PyQT_Demo = PyQT_Demo
    
    # method to demonstrate threading while running code from the same program
    # threading is launched by the B2_Launch Method 
    def run_internal(self):
        for j in range(10):
            time.sleep(0.5)
            self.worker_queue.put(
                f'Internal Threading Test-worker-{self.i} : {j}'
                )
            self.progress.emit(self.i)
        self.finished.emit(self.i)
    
    # method to demonstrate threading while running code through 
    # subprocess.popen
    # threading is launched by the B1_Launch Method
    def run_external(self):
        # use subprocess.Popen to run a seperate program in a new process
        # stdout will be captured by the variable self.echo and extracted below
        self.echo = subprocess.Popen(
            f'python -u "{self.path_to_script}" -i "External Threading Test-WORKER-{self.i}"',
            stdout= subprocess.PIPE, 
            stderr = subprocess.STDOUT
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
                self.progress.emit(self.i)
        self.finished.emit(self.i)


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