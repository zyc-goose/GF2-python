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
import threading
import time

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
        self.page_number = 1
        self.current_page = 1

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)

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
        page_disp = 'Page: '+str(self.current_page)+'/'+str(self.page_number)
        self.render_text(page_disp, (520-self.pan_x)/self.zoom, 10)

        if self.run == 1:
            # If run button clicked, render all signals
            self.render_signal()
        self.parent.update_scroll_bar()

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

    def on_key(self,event):
        key_code = event.GetKeyCode()

        if key_code in (wx.WXK_LEFT, wx.WXK_RIGHT):
            full_width = self.parent.full_width
            length = self.parent.hbar.GetRange()
            thumb_size = self.parent.hbar.GetThumbSize()
            if key_code == wx.WXK_LEFT:
                self.pan_x += 10
                if self.pan_x > 0:
                    self.pan_x = 0
            elif key_code == wx.WXK_RIGHT:
                self.pan_x -= 10
                if self.pan_x < -(self.signal_width-self.parent.full_width):
                    self.pan_x = -(self.signal_width-self.parent.full_width)
            thumb_pos = self.pan_x * (length - thumb_size) / (self.signal_width - full_width)
            self.parent.hbar.SetThumbPosition(thumb_pos)
        if key_code == wx.WXK_UP:
            pass
        if key_code == wx.WXK_DOWN:
            pass

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

    def draw_rect_background(self, start_x, start_y, end_x, end_y):
        greylevel_f = 0.94
        GL.glColor3f(greylevel_f, greylevel_f, greylevel_f)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(start_x, start_y)
        GL.glVertex2f(start_x, end_y)
        GL.glVertex2f(end_x, end_y)
        GL.glVertex2f(end_x, start_y)
        GL.glEnd()

    def render_signal(self):
        """Display the signal trace(s) in GUI"""

        # To confine name lengths, edit in the future
        margin = 10

        # local variables
        cycle_count = 0  # count number of cycles displayed
        pos = 0  # signal position, shifted upward for each signal
        start = 50  # start point for rasterisation
        # No of cycles to be displayed on this page
        last_cycle = min((self.cycles-(self.current_page-1)*60),60)
        end = max(last_cycle*9*self.zoom + start, start)  # end point for rasterisation
        if last_cycle != 0:
            step = (end-start)/last_cycle
        else:
            step = 0

        self.signal_width = end+10
        # Use below when texture is mapped
        # self.signal_width = max(end+10, self.GetClientSize().width*self.zoom)

        # Draw the first strip under the first device
        strip_raise = 113
        self.draw_rect_background(0, strip_raise+2-50,
                                  max(600, 600/self.zoom), strip_raise-2-50)

        # Iterate over each device and render
        for device_id, output_id in self.monitors.monitors_dictionary:
            monitor_name = self.devices.get_signal_name(device_id, output_id)
            signal_list = self.monitors.monitors_dictionary[(device_id, output_id)]

            # Draw the grey strip between devices
            self.draw_rect_background(0, strip_raise+2+pos*50,
                                      max(600, 600/self.zoom), strip_raise-2+pos*50)
            #if pos % 2 == 0:
                #self.draw_rect_background(0, 110+pos*50, 600/self.zoom, 60+pos*50)

            # Display signal name
            self.render_text(monitor_name[0:margin], 10/self.zoom, 80+pos*50)

            # Start drawing the current signal
            GL.glColor3f(0.0, 0.0, 1.0)  # signal trace is blue
            GL.glBegin(GL.GL_LINE_STRIP)

            # Iterate over each cycle and render
            cycle_count = 0
            for signal in signal_list[(self.current_page-1)*60:(self.current_page-1)*60+last_cycle]:
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

        # Get monitors
        self.monitored_list, self.unmonitored_list = self.monitors.get_signal_names()
        self.total_list = self.monitored_list + self.unmonitored_list

        # Cycles completed and worker for multithread
        self.cycles_completed = 0
        self.worker = RunThread(self, 1)

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
        self.canvas.signals = self.monitored_list

        # Preparing Bitmaps for zoom buttons
        image_1 = wx.Image("./graphics/plus.png")
        image_1.Rescale(30, 30)
        plus = wx.Bitmap(image_1)
        image_2 = wx.Image("./graphics/minus.png")
        image_2.Rescale(30, 30)
        minus = wx.Bitmap(image_2)

        # Basic cycle control widgets
        self.text = wx.StaticText(self, wx.ID_ANY, "Cycles")
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", max = 10**10)
        self.run_button = wx.Button(self, wx.ID_ANY, "Run")
        self.cont_button = wx.Button(self,wx.ID_ANY,"Add")
        self.del_button = wx.Button(self, wx.ID_ANY, "Delete")

        # Monitor add/delete widgets
        # self.cb_monitor = wx.ComboBox(self,wx.ID_ANY,size=(100,30),choices=self.total_list)
        self.text2 = wx.StaticText(self, wx.ID_ANY, "Monitors")
        self.sig_add_button = wx.Button(self,wx.ID_ANY,"Add/Delete Monitor")
        # self.sig_del_button = wx.Button(self, wx.ID_ANY, "Delete")

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
        #self.hero_button = wx.Button(self, wx.ID_ANY, "HERO")
        self.prev_button = wx.Button(self, wx.ID_ANY, "Prev Page")
        self.next_button = wx.Button(self, wx.ID_ANY, "Next Page")
        self.text_box = wx.TextCtrl(self, wx.ID_ANY, "",
                                   style=wx.TE_PROCESS_ENTER)
        self.goto_button = wx.Button(self, wx.ID_ANY, "Goto")

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
        # self.sig_del_button.Bind(wx.EVT_BUTTON, self.on_sig_del_button)

        self.zoom_in_button.Bind(wx.EVT_BUTTON, self.on_zoom_in_button)
        self.zoom_out_button.Bind(wx.EVT_BUTTON, self.on_zoom_out_button)
        # self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear_button)
        #self.hero_button.Bind(wx.EVT_BUTTON, self.on_hero_button)
        self.hbar.Bind(wx.EVT_SCROLL, self.on_hbar)
        self.prev_button.Bind(wx.EVT_BUTTON, self.on_prev_button)
        self.next_button.Bind(wx.EVT_BUTTON, self.on_next_button)
        self.goto_button.Bind(wx.EVT_BUTTON, self.on_goto_button)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer_second = wx.BoxSizer(wx.VERTICAL)
        double_butt = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_2 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_3 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_4 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_5 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_6 = wx.BoxSizer(wx.HORIZONTAL)


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
        # side_sizer.Add(self.cb_monitor, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_2, 1, wx.ALL, 0)
        double_butt_2.Add(self.sig_add_button, 1, wx.ALL, 5)
        # double_butt_2.Add(self.sig_del_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text3, 1, wx.TOP, 10)
        side_sizer.Add(self.cb_switch, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_3, 1, wx.ALL, 0)
        double_butt_3.Add(self.set_button, 1, wx.ALL, 5)
        double_butt_3.Add(self.clr_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text4, 1, wx.TOP, 10)
        side_sizer.Add(double_butt_4, 0.5, wx.ALL, 0)
        double_butt_4.Add(self.zoom_in_button, 1, wx.ALL, 5)
        double_butt_4.Add(self.zoom_out_button, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_5, 1, wx.ALL, 0)
        double_butt_5.Add(self.prev_button, 0.8 , wx.ALL, 0)
        double_butt_5.Add(self.next_button, 0.8, wx.ALL, 0)
        side_sizer.Add(double_butt_6, 1, wx.ALL, 0)
        double_butt_6.Add(self.text_box, 0.8 , wx.ALL, 0)
        double_butt_6.Add(self.goto_button, 0.8, wx.ALL, 0)
        # side_sizer.Add(self.hero_button, 1 , wx.ALL, 5)

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
        self.canvas.run = 1
        self.canvas.cycles = self.spin.GetValue()
        self.canvas.page_number = int(self.canvas.cycles/60)+1
        self.canvas.current_page = 1
        self.cycles_completed = min(self.canvas.cycles, 60)
        self.monitors.reset_monitors()
        if self.run_network(self.cycles_completed):
            text = "Run button pressed."
        else:
            device_name = self.names.get_name_string(self.network.device_no_input)
            text = 'DEVICE \"' + device_name + '\" is oscillatory!'
        self.worker = RunThread(self, 1)
        self.worker.start()
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
        added_cycles = self.spin.GetValue()
        self.canvas.cycles += added_cycles
        self.canvas.page_number = int(self.canvas.cycles/60)+1
        next_to_run = min((60-self.cycles_completed%60), added_cycles)
        self.run_network(next_to_run)
        self.cycles_completed += next_to_run
        # self.run_network(self.spin.GetValue())
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

    def get_monitor_ids(self, signal):
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
        top = MonitorFrame(self, "Monitors", self.monitored_list, self.unmonitored_list)
        top.Show()

        # Add monitor using the IDs above
        # if self.canvas.run != 1:
        #     text = 'You should run the simulation first'
        # else:
        #     for signal in self.to_add:
        #         device_id, port_id = self.get_monitor_ids(signal)
        #         monitor_error = self.monitors.make_monitor(device_id, port_id,
        #                                                self.canvas.cycles)
        #         if monitor_error == self.monitors.NO_ERROR:
        #             text = "Successfully made monitor."
        #         else:
        #             text = "Error! Could not make monitor: "+ signal
        # self.canvas.render(text)

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

    def on_prev_button(self, event):
        if self.canvas.current_page > 1:
            self.canvas.current_page -= 1
            self.canvas.pan_x = 0
            self.canvas.init = False
        else:
            self.canvas.current_page = 1
        self.canvas.render('Turn to Previous Page')

    def on_next_button(self, event):
        if self.canvas.current_page < self.canvas.page_number:
            next_to_run = min(self.canvas.cycles-self.canvas.current_page*60, 60)
            self.canvas.current_page += 1
            self.canvas.pan_x = 0
            self.canvas.init = False
            if self.canvas.current_page*60 > self.cycles_completed:
                self.run_network(next_to_run)
                self.cycles_completed += next_to_run
        else:
            self.canvas.current_page = self.canvas.page_number
        self.canvas.render('Turn to Next Page')

    def on_goto_button(self, event):
        self.worker.stop()
        time.sleep(.100)
        page_number = self.text_box.GetValue()
        text = "Go to page: " + page_number
        page_number = page_number if page_number is not '' else self.canvas.current_page
        to_run = int(page_number)*60-self.cycles_completed
        if to_run > 0:
            self.run_network(to_run)
            self.cycles_completed += to_run
        self.canvas.current_page = int(page_number)
        self.canvas.render(text)

        #self.worker = RunThread(self, 1)
        #self.worker.start()


# Monitor Selection Frame
class MonitorFrame(wx.Frame):
    def __init__(self, parent, title, monitored, unmonitored):
        wx.Frame.__init__(self, None, title=title, pos=(350,150), size=(350,300))
        self.parent = parent
        self.monitored = monitored
        self.unmonitored = unmonitored
        self.Bind(wx.EVT_CLOSE, self.on_close)

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)

        self.statusbar = self.CreateStatusBar()

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        list_sizer = wx.BoxSizer(wx.HORIZONTAL)

        m_text = wx.StaticText(panel, -1, "Select Signal")
        m_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        m_text.SetSize(m_text.GetBestSize())
        box.Add(m_text, 1, wx.ALL, 5)

        self.list_ctrl_1 = wx.ListCtrl(panel, size=(-1,100), style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.list_ctrl_2 = wx.ListCtrl(panel, size=(-1,100), style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.list_ctrl_1.InsertColumn(0, 'Monitored', width = 160)
        self.list_ctrl_2.InsertColumn(0, 'Unmonitored', width = 160)
        index = 0
        for signal in self.monitored:
            self.list_ctrl_1.InsertItem(index, signal)
            index = index+1

        for signal in self.unmonitored:
            self.list_ctrl_2.InsertItem(index, signal)
            index = index+1

        box.Add(list_sizer, 10, wx.ALL, 0)
        list_sizer.Add(self.list_ctrl_1, 1, wx.EXPAND|wx.ALL, 5)
        list_sizer.Add(self.list_ctrl_2, 1, wx.EXPAND|wx.ALL, 5)

        side_sizer = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(side_sizer, 1, wx.ALL, 5)

        add = wx.Button(panel, wx.ID_CLOSE, "ADD")
        delete = wx.Button(panel, wx.ID_CLOSE, "DELETE")
        close = wx.Button(panel, wx.ID_CLOSE, "CLOSE")
        add.Bind(wx.EVT_BUTTON, self.on_add)
        delete.Bind(wx.EVT_BUTTON, self.on_delete)
        close.Bind(wx.EVT_BUTTON, self.on_close)
        side_sizer.Add(add, 1, wx.ALL, 5)
        side_sizer.Add(delete, 1, wx.ALL, 5)
        side_sizer.Add(close, 1, wx.ALL, 5)

        panel.SetSizer(box)
        panel.Layout()

    def refresh_lists(self):
        self.list_ctrl_1.DeleteAllItems()
        self.list_ctrl_2.DeleteAllItems()
        for index, signal in enumerate(self.monitored):
            self.list_ctrl_1.InsertItem(index, signal)
        for index, signal in enumerate(self.unmonitored):
            self.list_ctrl_2.InsertItem(index, signal)

    def on_close(self, event):
        self.Destroy()

    def on_add(self, event):
        signals = []
        text = ''
        index = -1
        while True:
            index = self.list_ctrl_2.GetNextItem(index, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            signals.append(self.unmonitored[index])

        # Delete monitor using the IDs above
        if self.parent.canvas.run != 1:
            text = 'You should run the simulation first'
        else:
            for signal in signals:
                device_id, port_id = self.parent.get_monitor_ids(signal)
                monitor_error = self.parent.monitors.make_monitor(device_id, port_id,
                                                       self.parent.canvas.cycles)
                if monitor_error == self.parent.monitors.NO_ERROR:
                    text = "Successfully made monitor."
                    self.parent.monitored_list.append(signal)
                    self.parent.unmonitored_list.remove(signal)
                else:
                    text = "Error! Could not make monitor: "+ signal
        self.parent.canvas.render(text)
        self.refresh_lists()

    def on_delete(self, event):
        signals = []
        text = ''
        index = -1
        while True:
            index = self.list_ctrl_1.GetNextItem(index, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            signals.append(self.monitored[index])

        # Delete monitor using the IDs above
        if self.parent.canvas.run != 1:
            text = 'You should run the simulation first'
        else:
            for signal in signals:
                device_id, port_id = self.parent.get_monitor_ids(signal)
                if self.parent.monitors.remove_monitor(device_id, port_id):
                    text = "Successfully zapped monitor"
                    self.parent.unmonitored_list.append(signal)
                    self.parent.monitored_list.remove(signal)
                else:
                    text = "Error! Could not zap monitor: "+ signal
        self.parent.canvas.render(text)
        self.refresh_lists()


# Multithreading
class RunThread(threading.Thread):
    def __init__(self, parent, value):
        """
        @param parent: The gui object that should recieve the value
        @param value: value to 'calculate' to
        """
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self._parent = parent
        self._value = value

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        while self._parent.cycles_completed+1000 <= self._parent.canvas.cycles:
            time.sleep(.100)
            self._parent.run_network(1000)
            self._parent.cycles_completed += 1000
            if self._stop_event.is_set():
                break
    def stop(self):
        self._stop_event.set()
        # wx.PostEvent(self._parent, evt)
