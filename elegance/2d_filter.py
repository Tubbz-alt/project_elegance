"""
###############################################################################
# A script that suppresses all the information in the 2D images of C. Elegans #
# except the worm itself (i.e. image filtering).                              #
#                                                                             #
#                                                                             #
# Author: Othman Alikhan                                                      #
# Email: sc14omsa@leeds.ac.uk                                                 #
#                                                                             #
# Python Version: 2.7.12                                                      #
# Date Created: 2016-07-15                                                    #
###############################################################################
"""
import os
import sys
import time

import cv2
import numpy as np
from pyqtgraph import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.examples
#pyqtgraph.examples.run()


class ImageController:

    def main(self):
        # Reading
        dataType = "C"
        cameraNum = "1"
        imageReader = ImageReader(cameraNum, dataType)
        img1 = imageReader.readFrame(1)
        img2 = imageReader.readFrame(20)

        # Subtracting
        imageFilter = ImageFilter()
        diff = imageFilter.computeDifferenceAlgorithm(img1, img2)

        # Displaying
        imageDisplay = ImageDisplay(img1)


class ImageDisplay:
    """
    Responsible for rendering the images on screen using pyqtgraph.
    """

    def __init__(self, img):
        """
        Initializes the Qt GUI framework.
        """
        app = QtGui.QApplication([])

        ## Create window with ImageView widget
        window = QtGui.QMainWindow()
        window.resize(800, 800)
        window.setWindowTitle("I See Elegance. I C. Elegans")
        window.setContentsMargins(0, 0, 0, 0)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)

        mainWidget = QtGui.QWidget()
        mainWidget.setContentsMargins(0, 0, 0, 0)

        imageViewA = pg.ImageView()
        imageViewA.setImage(img)
        imageViewA.setContentsMargins(0, 0, 0, 0)

        imageViewB = pg.ImageView()
        imageViewB.setImage(img)
        imageViewB.setContentsMargins(0, 0, 0, 0)

        mainWidget.setLayout(mainLayout)
        mainLayout.addWidget(imageViewA)
        mainLayout.addWidget(imageViewB)
        window.setCentralWidget(mainWidget)
        window.show()

        ## Start Qt event loop unless running interactive mode or using pyside.
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()


################################### DONE #######################################
class ImageFilter:
    """
    Responsible for applying filtering algorithms on the images.
    """

    def __init__(self):
        """
        A simple constructor that initializes variables used to crudely
        time algorithms.
        """
        self.currentFrame = 0
        self.timeStart = None

    def computeOtsuAlgorithm(self, img, *args):
        """
        Wrapper function that simply runs the OpenCV Otsu's thresholding.

        :param img: The image to perform the algorithm on.
        :return: The outputs of the OpenCV thresholding function.
        """
        return cv2.threshold(img, *args)

    def computeDifferenceAlgorithm(self, img1, img2):
        """
        Computes the absolute difference between two frames.

        :param img1: The first image to be used in the difference.
        :param img2: The second image to be used in the difference.
        :return: The difference of two images in OpenCV format.
        """
        return cv2.absdiff(img1, img2)

    def trackWormAlgorithm(self, fOne, fDiff):
        """
        Blurs two images, takes their absolute difference, applies a local
        gaussian threshold, then attempts to find contours of the worm and
        draws a rectangle around it.

        :param fOne: Integer number of the first frame.
        :param fDiff: How many frames ahead the next image is.
        :return: The difference of two images in OpenCV format.
        """
        # Magic Parameters
        downSize = (256, 256)
        threshold = 25
        dilationIter = 10
        contourMinArea = 100   # worm ~ 200 x 10 pixels^2




        self.img = cv2.imread(self._generateFramePath(self.fStart))

        img1 = cv2.imread(self._generateFramePath(fOne))
        img2 = cv2.imread(self._generateFramePath(fOne + fDiff))

        # Downsize images
        img1 = cv2.resize(img1, downSize, img1)
        img2 = cv2.resize(img2, downSize, img2)

        # Computes the absolute difference
        diff = cv2.absdiff(img1, img2)
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Applies global thresholding to binary
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # Dilates image to fill gaps and finding all contours
        dillation = cv2.dilate(thresh, None, iterations=dilationIter)
        (contours, _) = cv2.findContours(dillation.copy(),
                                         cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)


        img = cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)



        # Extracting only sufficiently large contours and drawing a
        # rectangle around them
        for c in contours:
            if cv2.contourArea(c) < contourMinArea:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
#            print("Contours Rectangle at: (%d %d) (%d %d)" % (x, y, w, h))
#            print("Contours Area: %d " % cv2.contourArea(c))
            cv2.rectangle(self.img, (x, y), (x+w, y+h), (170, 0, 0), 2)


        return self.img

    def _updatePerformanceMeasuring(self):
        """
        Updates the last frame called in the animation and prints the time
        elapsed, and average FPS since the last call to _beginTiming function.
        """
        print("--- PERFORMANCE MEASUREMENTS UPDATING ---")
        self.currentFrame += 1
        dt = time.time() - self.timeStart
        fps = (self.currentFrame / dt)

        print("Time Elapsed: %d seconds" % dt)
        print("Current Frame: %d" % self.currentFrame)
        print("Overall FPS: %.2f" % fps)

    def _startPerformanceMeasuring(self):
        """
        Starts the measuring of time and current frame.
        To be used in conjunction with it's update method.
        """
        print("--- PERFORMANCE MEASUREMENTS STARTING NOW ---")
        self.timeStart = time.time()
        self.currentFrame = 0


class ImageReader:
    """
    Responsible for handling image I/O.
    """

    def __init__(self, cameraNum, dataType):
        """
        A simple constructor.

        :param cameraNum: The camera number that took the images.
        :param dataType: A capitalized alphabetical character that denotes
        directory.
        """

        self.camera = "cam" + str(cameraNum)
        self.type = dataType

    def readFrame(self, fNum, flag=1):
        """
        Reads the worm image for the given frame number using OpenCV read.

        :param fNum: The frame number to be read.
        :param flag: The flag for the opencv image read method.
        :return: An image in OpenCV format.
        """
        return cv2.imread(self._generateFramePath(fNum), flag)

    def _generateFramePath(self, fNum):
        """
        Generates the absolute path to a given frame number in the 2D images
        directory for C. Elegans. This requires the frames to be named
        chronologically using the form "frame_0000XY.png", where six digits (
        can be leading zeros) are present after the frame prefix.

        :param fNum: The frame number of the 2D image.
        :return: A string of the absolute path to a worm image.
        """
        frame = "frame_%06d.png" % fNum
        path = ["..", "..", "assets", "images", self.type, self.camera, frame]

        relPath = os.path.join(*path)
        absPath = os.path.abspath(relPath)

        if os.path.exists(absPath):
            return absPath
        else:
            raise NameError("Could not generate a path frame number %d!" % fNum)
################################### DONE #######################################

if __name__ == "__main__":
    # Control variables
    fStart = 1
    fDiff = 25*10
    fEnd = 680
    fPause = 1000       # milliseconds

    # Run
    imageController = ImageController()
    imageController.main()


