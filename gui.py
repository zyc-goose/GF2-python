"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT
from PIL import Image

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.
    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)

        self.monitors = monitors
        self.devices = devices
        self.parent = parent

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position
        # Newly defined variables
        self.current_x = 0  # Current mouse x position
        self.current_y = 0  # Current mouse y position
        self.run = 0  # run flag
        self.cycles = 0  # number of cycles for display
        self.texture = None  # texture ID
        self.use_hero = 0  # whether to use texture or not
        self.signal_width = 0  # Total signal length on canvas

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def initTexture(self):
        """init the texture - this has to happen after an OpenGL context
        has been created
        """

        # make the OpenGL context associated with this canvas the current one
        self.SetCurrent(self.context)

        # Get image from current folder
        im = Image.open('./graphics/hero.jpg')
        try:
            ix, iy, image = im.size[0], im.size[1], im.tobytes("raw", "RGBX", 0, -1)
        except SystemError:
            ix, iy, image = im.size[0], im.size[1], im.tobytes("raw", "RGBA", 0, -1)

        # generate a texture id, make it current
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # texture mode and parameters controlling wrapping and scaling
        GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        # map the image data to the texture. note that if the input
        # type is GL_FLOAT, the values must be in the range [0..1]
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, ix, iy, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, image)

    def init_gl(self):
        self.initTexture()
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, 1, self.zoom)

    def render(self, text):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        self.signal_width = self.GetClientSize().width*self.zoom
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        if self.use_hero == 1:
            self.texture_mapping()

        # Draw specified text at position (10, 10)
        self.render_text(text, 10/self.zoom, 10)

        if self.run == 1:
            # If run button clicked, render all signals
            self.render_signal()

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        size = self.GetClientSize()
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        self.current_x = event.GetX()
        self.current_y = event.GetY()
        size = self.GetClientSize()
        self.current_y = size.height-self.current_y
        text = ''
        #text = "".join(["X: ", str(self.current_x), " Y: ", str(self.current_y)])

        # Double Click reset to original place, single click shows the position
        if event.ButtonDClick():
            self.zoom = 1
            self.pan_x = 0
            self.pan_y = 0
            self.init_gl()
            self.init = True
            text = "Mouse double clicked"
        elif event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        elif event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if text:
            self.render(text)
            # Here called the parent, but better to do it in other ways
            self.parent.update_scroll_bar()
        else:
            self.Refresh()  # triggers the paint event

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

    def draw_horizontal_signal(self, start, cycle_count, step, level, pos):
        # Two vertices having same y coord
        x = start+cycle_count*step
        x_next = start+(cycle_count+1)*step
        y = 75+25*level+pos*50
        GL.glVertex2f(x/self.zoom, y)
        GL.glVertex2f(x_next/self.zoom, y)

    def render_signal(self):
        """Display the signal trace(s) in GUI"""

        # To confine name lengths, edit in the future
        margin = 10

        # local variables
        cycle_count = 0  # count number of cycles displayed
        pos = 0  # signal position, shifted upward for each signal
        start = 70  # start point for rasterisation
        end = max(self.cycles*20*self.zoom, start)  # end point for rasterisation
        if self.cycles != 0:
            step = (end-start)/self.cycles
        else:
            step = 0

        self.signal_width = max(end+10, self.GetClientSize().width*self.zoom)

        # Iterate over each device and render
        for device_id, output_id in self.monitors.monitors_dictionary:
            monitor_name = self.devices.get_signal_name(device_id, output_id)
            signal_list = self.monitors.monitors_dictionary[(device_id, output_id)]

            # Display signal name
            self.render_text(monitor_name[0:margin], 10/self.zoom, 80+pos*50)

            # Start drawing the current signal
            GL.glColor3f(0.0, 0.0, 1.0)  # signal trace is blue
            GL.glBegin(GL.GL_LINE_STRIP)

            # Iterate over each cycle and render
            cycle_count = 0
            for signal in signal_list:
                if signal == self.devices.HIGH:
                    self.draw_horizontal_signal(start, cycle_count, step, 1, pos)
                    cycle_count += 1
                if signal == self.devices.LOW:
                    self.draw_horizontal_signal(start, cycle_count, step, 0, pos)
                    cycle_count += 1
                if signal == self.devices.RISING:
                    continue
                if signal == self.devices.FALLING:
                    continue
                if signal == self.devices.BLANK:
                    # ASK TOMORROW
                    cycle_count += 1
                # if cycle_count > self.cycles:
                #    break
            pos = pos+1
            GL.glEnd()

    def texture_mapping(self):
        """draw function """
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # enable textures, bind to our texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glColor3f(1, 1, 1)

        # draw a quad
        size = self.GetClientSize()
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0, 1)
        GL.glVertex2f(0, size.height)
        GL.glTexCoord2f(0, 0)
        GL.glVertex2f(0, 0)
        GL.glTexCoord2f(1, 0)
        GL.glVertex2f(size.width, 0)
        GL.glTexCoord2f(1, 1)
        GL.glVertex2f(size.width, size.height)
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)

        # swap the front and back buffers so that the texture is visible
        #self.SwapBuffers()


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_spin(self, event): Event handler for when the user changes the spin
                           control value.

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_text_box(self, event): Event handler for when the user enters text.
    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        # Make objects local
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.names = names

        # Get device terminals
        monitored_list, unmonitored_list = self.monitors.get_signal_names()
        self.total_list = monitored_list + unmonitored_list

        # Get switch list
        self.switch_ids = self.devices.find_devices(self.devices.SWITCH)
        self.switches = []
        for each_id in self.switch_ids:
            self.switches.append(names.get_name_string(each_id))

        # Configure the file menu
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenu.Append(wx.ID_EXIT, "&Exit")
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, devices, monitors)
        self.canvas.signals = monitored_list

        # Preparing Bitmaps for zoom buttons
        image_1 = wx.Image("./graphics/plus.png") 
        image_1.Rescale(30, 30) 
        plus = wx.Bitmap(image_1)
        image_2 = wx.Image("./graphics/minus.png") 
        image_2.Rescale(30, 30) 
        minus = wx.Bitmap(image_2) 

        # Basic cycle control widgets
        self.text = wx.StaticText(self, wx.ID_ANY, "Cycles")
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", max = 10000000)
        self.run_button = wx.Button(self, wx.ID_ANY, "Run")
        self.cont_button = wx.Button(self,wx.ID_ANY,"Add")
        self.del_button = wx.Button(self, wx.ID_ANY, "Delete")

        # Monitor add/delete widgets
        self.cb_monitor = wx.ComboBox(self,wx.ID_ANY,size=(100,30),choices=self.total_list)
        self.text2 = wx.StaticText(self, wx.ID_ANY, "Monitors")
        self.sig_add_button = wx.Button(self,wx.ID_ANY,"Add")
        self.sig_del_button = wx.Button(self, wx.ID_ANY, "Delete")

        # Switch toggle widgets
        self.text3 = wx.StaticText(self, wx.ID_ANY, "Switches")
        self.cb_switch = wx.ComboBox(self,wx.ID_ANY,size=(100,30),choices=self.switches)
        self.set_button = wx.Button(self, wx.ID_ANY, "1")
        self.clr_button = wx.Button(self, wx.ID_ANY, "0")

        # Zoom in/out functions
        self.text4 = wx.StaticText(self, wx.ID_ANY, "Zoom in/out")
        self.zoom_in_button = wx.BitmapButton(self, wx.ID_ANY, plus, size=(40,40))
        self.zoom_out_button = wx.BitmapButton(self, wx.ID_ANY, minus, size=(40,40))
        # self.clear_button = wx.Button(self, wx.ID_ANY, "Clear")

        # Display texture mapping
        self.hero_button = wx.Button(self, wx.ID_ANY, "HERO")
        # self.text_box = wx.TextCtrl(self, wx.ID_ANY, "",
        #                            style=wx.TE_PROCESS_ENTER)

        # Scroll Bars
        self.full_width = 600
        self.hbar = wx.ScrollBar(self, id=wx.ID_ANY, size=(600,15), style=wx.SB_HORIZONTAL)
        self.hbar.SetScrollbar(0, self.full_width, self.full_width, 1)

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.spin.Bind(wx.EVT_SPINCTRL, self.on_spin)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.cont_button.Bind(wx.EVT_BUTTON, self.on_cont_button)
        # self.del_button.Bind(wx.EVT_BUTTON, self.on_del_button)

        self.set_button.Bind(wx.EVT_BUTTON, self.on_set_button)
        self.clr_button.Bind(wx.EVT_BUTTON, self.on_clr_button)

        self.sig_add_button.Bind(wx.EVT_BUTTON, self.on_sig_add_button)
        self.sig_del_button.Bind(wx.EVT_BUTTON, self.on_sig_del_button)

        self.zoom_in_button.Bind(wx.EVT_BUTTON, self.on_zoom_in_button)
        self.zoom_out_button.Bind(wx.EVT_BUTTON, self.on_zoom_out_button)
        # self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear_button)
        self.hero_button.Bind(wx.EVT_BUTTON, self.on_hero_button)
        self.hbar.Bind(wx.EVT_SCROLL, self.on_hbar)
        # self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer_second = wx.BoxSizer(wx.VERTICAL)
        double_butt = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_2 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_3 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_4 = wx.BoxSizer(wx.HORIZONTAL)


        main_sizer.Add(main_sizer_second, 5, wx.EXPAND | wx.RIGHT | wx.TOP | wx.LEFT, 5)
        main_sizer_second.Add(self.canvas, 25, wx.EXPAND | wx.ALL, 5)
        main_sizer_second.Add(self.hbar, 1, wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

        side_sizer.Add(self.text, 1, wx.TOP, 10)
        side_sizer.Add(self.spin, 1, wx.ALL, 5)
        side_sizer.Add(self.run_button, 1, wx.ALL, 5)
        side_sizer.Add(double_butt, 1, wx.ALL, 0)
        double_butt.Add(self.cont_button, 1, wx.ALL, 5)
        double_butt.Add(self.del_button, 1, wx.ALL, 5)  # Currently not using

        side_sizer.Add(self.text2, 1, wx.TOP, 10)
        side_sizer.Add(self.cb_monitor, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_2, 1, wx.ALL, 0)
        double_butt_2.Add(self.sig_add_button, 1, wx.ALL, 5)
        double_butt_2.Add(self.sig_del_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text3, 1, wx.TOP, 10)
        side_sizer.Add(self.cb_switch, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_3, 1, wx.ALL, 0)
        double_butt_3.Add(self.set_button, 1, wx.ALL, 5)
        double_butt_3.Add(self.clr_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text4, 1, wx.TOP, 10)
        side_sizer.Add(double_butt_4, 0.5, wx.ALL, 0)
        double_butt_4.Add(self.zoom_in_button, 1, wx.ALL, 5)
        double_butt_4.Add(self.zoom_out_button, 1, wx.ALL, 5)
        side_sizer.Add(self.hero_button, 1 , wx.ALL, 5)
        # side_sizer.Add(self.text_box, 1, wx.TOP, 10)

        # side_sizer.Add(self.clear_button, 1, wx.ALL, 5)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nTeam 4 Version\n2018",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def on_spin(self, event):
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join(["New spin control value: ", str(spin_value)])
        self.canvas.render(text)

    def run_network(self, cycles):
        """Run the network for the specified number of simulation cycles."""
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                return False
        return True

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        status = False
        if self.canvas.run == 0:
            self.canvas.run = 1
            self.canvas.cycles = self.spin.GetValue()
            status = self.run_network(self.canvas.cycles)
        else:
            text = "Already in Run mode"
        if status:
            text = "Run button pressed."
        else:
            device_name = self.names.get_name_string(self.network.device_no_input)
            text = 'DEVICE \"' + device_name + '\" is oscillatory!'
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join(["New text box value: ", text_box_value])
        self.canvas.render(text)

    def on_cont_button(self, event):
        text = "Add Cycles button pressed."
        self.canvas.run = 1
        self.canvas.cycles += self.spin.GetValue()
        self.run_network(self.spin.GetValue())
        self.canvas.render(text)
        self.update_scroll_bar()

    # def on_del_button(self, event):
    #     text = "Delete Cycles button pressed."
    #     self.canvas.run = 1
    #     self.canvas.cycles -= self.spin.GetValue()
    #     if self.canvas.cycles<0:
    #         self.canvas.cycles=0
    #     self.canvas.render(text)

    def switch_signal(self, switch_state):
        text = ""
        if self.cb_switch.GetSelection() != wx.NOT_FOUND:
            device = self.switches[self.cb_switch.GetSelection()]
        else:
            device = None
        if device is not None:
            switch_id = self.names.query(device)
            if self.devices.set_switch(switch_id, switch_state):
                text = "Successfully set switch."
            else:
                text = "Error! Invalid switch."
        else:
            text = "Button no effect!"
        self.canvas.render(text)

    def on_set_button(self, event):
        """Set the specified switch"""
        if self.canvas.run != 1:
            text = 'You should run the simulation first'
        else:
            self.switch_signal(1)

    def on_clr_button(self, event):
        """Clear the specified switch"""
        if self.canvas.run != 1:
            text = 'You should run the simulation first'
        else:
            self.switch_signal(0)

    def get_monitor_ids(self):
        if self.cb_monitor.GetSelection() != wx.NOT_FOUND:
            signal = self.total_list[self.cb_monitor.GetSelection()]
        else:
            signal = None
        if signal is not None and '.' in signal:
            device, port = signal.split('.')
            device_id = self.names.query(device)
            port_id = self.names.query(port)
        else:
            device = signal
            device_id = self.names.query(device)
            port_id = None
        return device_id, port_id

    def on_sig_add_button(self, event):
        # Get user selected signal and split to get IDs
        device_id, port_id = self.get_monitor_ids()

        # Add monitor using the IDs above
        if self.canvas.run != 1:
            text = 'You should run the simulation first'
        elif device_id is not None:
            monitor_error = self.monitors.make_monitor(device_id, port_id,
                                                       self.canvas.cycles)
            if monitor_error == self.monitors.NO_ERROR:
                text = "Successfully made monitor."
            else:
                text = "Error! Could not make monitor."
        else:
            text = "Button no effect!"
        self.canvas.render(text)

    def on_sig_del_button(self, event):
        # Get user selected signal and split to get IDs
        device_id, port_id = self.get_monitor_ids()

        # Delete monitor using the IDs above
        if self.canvas.run != 1:
            text = 'You should run the simulation first'
        elif device_id is not None:
            if self.monitors.remove_monitor(device_id, port_id):
                text = "Successfully zapped monitor"
            else:
                text = "Error! Could not zap monitor."
        else:
            text = "Button no effect!"
        self.canvas.render(text)

    # Should be added together with delete cycle function
    # def on_clear_button(self, event):
    #     text = 'Clear the Canvas'
    #     self.canvas.signals = []
    #     self.canvas.cycles = self.spin.GetValue()
    #     self.canvas.render(text)

    def on_zoom_in_button(self, event):
        text = 'Zoom in'
        self.canvas.zoom = self.canvas.zoom*2
        self.canvas.init = False
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_zoom_out_button(self, event):
        text = 'Zoom out'
        self.canvas.zoom = self.canvas.zoom*0.5
        self.canvas.init = False
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_hero_button(self, event):
        text = 'OUR HERO!!!'
        if self.canvas.use_hero == 1:
            self.canvas.use_hero = 0
            self.canvas.render(text)
        else:
            message = "Do You Want To See Our Leader?"
            dlg = wx.MessageDialog(self, message, caption="PLEASE ANSWER!!!",
                  style=wx.YES_NO|wx.CENTER)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.canvas.use_hero = 1
                self.canvas.render(text)
            dlg.Destroy()

    def on_hbar(self, event):
        pos = self.hbar.GetThumbPosition()
        length = self.hbar.GetRange()
        thumbsize = self.hbar.GetThumbSize()
        if length > thumbsize:
            self.canvas.pan_x = -int((self.canvas.signal_width-self.full_width)*(pos/(length-thumbsize)))
            self.canvas.init = False
            self.canvas.render(str(self.canvas.pan_x))

    def update_scroll_bar(self):
        pos = self.hbar.GetThumbPosition()
        if self.full_width < self.canvas.signal_width:
            self.hbar.SetScrollbar(pos, self.full_width, self.canvas.signal_width, self.canvas.zoom)
        else:
            self.hbar.SetScrollbar(pos, self.full_width, self.full_width, self.canvas.zoom)
