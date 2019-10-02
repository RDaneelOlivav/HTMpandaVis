#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay


verbosityLow = 0
verbosityMedium = 1
verbosityHigh = 2
FILE_VERBOSITY = (
    verbosityHigh
)  # change this to change printing verbosity of this file

def printLog(txt, verbosity=verbosityLow):
    if FILE_VERBOSITY >= verbosity:
        print(txt)

class cInteraction:
    
    def __init__(self,base):
        self.base = base
        self.render = base.render
        
        self.focusedCell = None
        self.focusedPath = None
        self.speedBoost = False
        
        self.gui = base.gui
        self.client = base.client
        
    """Updates the camera based on the keyboard input. Once this is
      done, then the CellManager's update function is called."""
    def UpdateCameraMovement(self):
        deltaT = globalClock.getDt()

        speed = self.base.speed

        if self.speedBoost:
            speed *= 4

        """Rotation with mouse while right-click"""
        mw = self.base.mouseWatcherNode
        deltaX = 0
        deltaY = 0

        if mw.hasMouse() and self.base.rotateCamera:
            deltaX = mw.getMouseX() - self.mouseX_last
            deltaY = mw.getMouseY() - self.mouseY_last

            self.mouseX_last = mw.getMouseX()
            self.mouseY_last = mw.getMouseY()

        if deltaT > 0.05:
            # FPS are low, limit deltaT
            deltaT = 0.05

        move_x = deltaT * speed * -self.keys["a"] + deltaT * speed * self.keys["d"]
        move_y = deltaT * speed * self.keys["s"] + deltaT * speed * -self.keys["w"]
        self.base.move_z += (
            deltaT * speed * self.keys["shift"] + deltaT * speed * -self.keys["control"]
        )

        self.base.camera.setPos(self.base.camera, move_x, -move_y, 0)
        self.base.camera.setZ(self.base.move_z)

        self.base.camHeading += (
            deltaT * 90 * self.keys["arrow_left"]
            + deltaT * 90 * -self.keys["arrow_right"]
            + deltaT * 5000 * -deltaX
        )
        self.base.camPitch += (
            deltaT * 90 * self.keys["arrow_up"]
            + deltaT * 90 * -self.keys["arrow_down"]
            + deltaT * 5000 * deltaY
        )
        self.base.camera.setHpr(self.base.camHeading, self.base.camPitch, 0)
        
    def SetupKeys(self):
        # Setup controls
        self.keys = {}
        for key in [
            "arrow_left",
            "arrow_right",
            "arrow_up",
            "arrow_down",
            "a",
            "d",
            "w",
            "s",
            "shift",
            "control",
            "space",
        ]:
            self.keys[key] = 0
            self.base.accept(key, self.onKey, [key, 1])
            self.base.accept("shift-%s" % key, self.onKey, [key, 1])
            self.base.accept("%s-up" % key, self.onKey, [key, 0])
    
        self.base.accept("escape", self.onEscape, [])
        self.base.disableMouse()
        
        self.base.accept("mouse1", self.onMouseEvent, ["left", True])
        self.base.accept("mouse1-up", self.onMouseEvent, ["left", False])
        self.base.accept("mouse3", self.onMouseEvent, ["right", True])
        self.base.accept("mouse3-up", self.onMouseEvent, ["right", False])
        
    def onWindowEvent(self, window):

        if self.base.win.isClosed():
            self.CloseApp()

        width = self.base.win.getProperties().getXSize()
        height = self.base.win.getProperties().getYSize()

        lens = self.base.cam.node().getLens()
        lens.setFov(60)
        lens.setAspectRatio(width / height)

        lens.setFar(500.0)
        # lens.setFilmSize(width,height)
        # lens.setFocalLength(self.FOCAL_LENGTH)
        self.base.cam.node().setLens(lens)

        self.base.gui.onWindowEvent(window)

    def onKey(self, key, value):
        """Stores a value associated with a key."""
        self.keys[key] = value

        if self.keys["space"]:
            self.speedBoost = not self.speedBoost
            self.gui.onSpeedBoostChanged(self.speedBoost)

    def onEscape(self):
        """Event when escape button is pressed."""

        # unfocus all
        for obj in self.base.HTMObjects.values():
            obj.DestroySynapses()

    def onMouseEvent(self, event, press):
        printLog("Mouse event:" + str(event), verbosityHigh)
        if event == "right":
            self.base.rotateCamera = press

            if self.base.mouseWatcherNode.hasMouse():
                self.mouseX_last = self.base.mouseWatcherNode.getMouseX()
                self.mouseY_last = self.base.mouseWatcherNode.getMouseY()
            else:
                self.mouseX_last = 0
                self.mouseY_last = 0
            """if press:
                props = WindowProperties()
                props.setCursorHidden(True)
                props.setMouseMode(WindowProperties.M_relative)
                self.win.requestProperties(props)"""
        elif event == "left" and press:
            self.onClickObject()
            
    def onClickObject(self):
        mpos = self.base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())

        self.myTraverser.traverse(self.render)
        # assume for simplicity's sake that myHandler is a CollisionHandlerQueue
        if self.myHandler.getNumEntries() > 0:
            # get closest object
            self.myHandler.sortEntries()

            pickedObj = self.myHandler.getEntry(0).getIntoNodePath()
            # printLog("----------- "+str(self.myHandler.getNumEntries()))
            print(self.myHandler.getEntries())
            pickedObj = pickedObj.findNetTag("clickable")
            print(pickedObj)
            if not pickedObj.isEmpty():
                self.HandlePickedObject(pickedObj)


    def SetupOnClick(self):

        pickerNode = CollisionNode("mouseRay")
        pickerNP = self.base.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(
            CollisionNode.getDefaultCollideMask()
        )  # GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)

        self.myTraverser = CollisionTraverser("mouseCollisionTraverser")

        # self.myTraverser.showCollisions(self.render) #uncomment to see collision point

        self.myHandler = CollisionHandlerQueue()

        self.myTraverser.addCollider(pickerNP, self.myHandler)

    def CloseApp(self):

        printLog("CLOSE app event")
        __import__("sys").exit(0)
        self.client.terminateClientThread = True
        
    def HandlePickedObject(self, obj):
        printLog("PICKED OBJECT:" + str(obj), verbosityMedium)

        thisId = int(obj.getTag("clickable"))
        printLog("TAG:" + str(thisId), verbosityHigh)

        parent = obj.getParent()  # skip LOD node
        tag = parent.getTag("id")
        if tag == "":
            printLog("Parent is not clickable!", verbosityHigh)
            return
        else:
            parentId = int(tag)
            printLog("PARENT TAG:" + str(parentId), verbosityHigh)

        if obj.getName() == "cell":
            printLog("We clicked on cell", verbosityHigh)

            focusedHTMObject = str(obj).split("/")[1]
            focusedLayer = str(obj).split("/")[2]

            HTMObj = self.base.HTMObjects[focusedHTMObject]
            Layer = HTMObj.layers[focusedLayer]
            newCellFocus = Layer.corticalColumns[parentId].cells[thisId]
            self.focusedPath = [focusedHTMObject, focusedLayer]

            if self.focusedCell != None:
                self.focusedCell.resetFocus()  # reset previous
            self.focusedCell = newCellFocus
            self.focusedCell.setFocus()

            self.gui.focusedCell = self.focusedCell
            self.gui.focusedPath = self.focusedPath
            
            self.gui.columnID = Layer.corticalColumns.index(self.gui.focusedCell.column)
            self.gui.cellID = Layer.corticalColumns[self.gui.columnID].cells.index(self.gui.focusedCell)

            if self.gui.showProximalSynapses:
                self.client.reqProximalData()
            if self.gui.showDistalSynapses:
                self.client.reqDistalData()
            
        elif obj.getName() == "basement":
            self.testRoutine()