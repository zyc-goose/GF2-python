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
import gettext
import os
import sys

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser

offset = 29
zoom_upper = 10
zoom_lower = 0.5


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

    init_parameters(self): Init parameters for panning

    initTexture(self): Initialise texture mapping

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    on_key(self, event): Read and process keyboard input

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.

    draw_horizontal_signal(self, start, cycle_count, step, level, pos):
        Draw signal High or Low

    draw_rect_background(self, start_x, start_y, end_x, end_y, color=0.94):
        Draw rectangular background.

    draw_rect_frame(self, start_x, start_y, end_x, end_y, color=0):
        Draw rectangular frame.

    draw_ruler(self, step, start_x, start_y): Draw ruler

    get_ruler_cycle_num(self, step, start_x): Detect corresponding cycle

    mouse_in_active_region(self, strip_raise, max_pos, ruler_offset):
        detect if mouse is on one of the signals

    find_nearest_signal_pos(self, strip_raise, max_pos, ruler_offset):
        Find the closest signal and get its position

    render_signal(self): Display the signal trace(s) in GUI, also calls
                         all relavent rendering functions

    draw_vertical_stipple_line(self, stipple_y_bottom, stipple_y_top):
        draw dashed cursor line

    draw_info_box(self, cycle, port, value): Draw the MATLAB-like
                            yellow info box which moves with mouse.

    draw_info_box_lang_en(self cycle, port, value): Draw box with English
                                                    language setting

    draw_info_box_lang_cn(cycle, port, value): Draw box with Chinese
                                                language setting

    texture_mapping(self, x_offset): Texture mapping for info box
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

        self.init_parameters()

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)

    def init_parameters(self):
        """Initialise variables for panning"""
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
        self.signal_count = 0
        self.page_number = 1
        self.current_page = 1
        self.max_signal_count = 10
        # parameters for signal dragging support
        self.monitored_list = []
        self.monitored_list_pressed_id = None
        self.mouse_button_is_down = False
        self.drag_mode = False

        # Initialise variables for zooming
        self.zoom = 1

    def initTexture(self):
        """init the texture - this has to happen after an OpenGL context
        has been created
        """

        # make the OpenGL context associated with this canvas the current one
        self.SetCurrent(self.context)

        # Get image from current folder
        im = Image.open('./graphics/infobox_cn.png')
        try:
            ix, iy, image = im.size[0], im.size[1],\
                im.tobytes("raw", "RGBA", 0, -1)
        except SystemError:
            ix, iy, image = im.size[0], im.size[1],\
                im.tobytes("raw", "RGBX", 0, -1)

        # generate a texture id, make it current
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # texture mode and parameters controlling wrapping and scaling
        GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE,
                     GL.GL_MODULATE)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S,
                           GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T,
                           GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR)

        # map the image data to the texture. note that if the input
        # type is GL_FLOAT, the values must be in the range [0..1]
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, ix, iy, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, image)

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        self.initTexture()
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

        if self.run == 1:
            # If run button clicked, render all signals
            self.render_signal()
        self.parent.update_scroll_bar()

        # Display page info in status bar
        page_disp = _('Page: ')+str(self.current_page) \
            + '/'+str(self.page_number)
        self.parent.page_disp(page_disp)
        self.parent.text_bar(text)

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
        text = "".join([_("Canvas redrawn on paint event, size is "),
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        size = self.GetClientSize()
        self.max_signal_count = int(size.height/50) - 2
        self.parent.full_length = size.height
        self.parent.update_vbar()
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        self.current_x = event.GetX()
        self.current_y = event.GetY()
        size = self.GetClientSize()
        self.current_y = size.height-self.current_y
        text = ''
        # Double Click reset to original place, single click shows the position
        if event.ButtonDClick():
            self.zoom = 1
            self.pan_x = 0
            self.pan_y = 0
            self.init_gl()
            self.init = True
            text = _("Mouse double clicked")
        elif event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.mouse_button_is_down = True
            self.monitored_list_pressed_id = None
            if self.mouse_in_active_region(113,
                                           len(self.monitored_list) - 1, 65):
                self.drag_mode = True
            else:
                self.drag_mode = False
            text = "".join([_("Mouse button pressed at: "), str(event.GetX()),
                            ", ", str(event.GetY())])
        elif event.ButtonUp():
            self.mouse_button_is_down = False
            self.drag_mode = False
            text = "".join([_("Mouse button released at: "), str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join([_("Mouse left canvas at: "), str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.zoom = max(self.zoom, zoom_lower)
            self.init = False
            text = "".join([_("Negative mouse wheel rotation. Zoom is now: "),
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.zoom = min(self.zoom, zoom_upper)
            self.init = False
            text = "".join([_("Positive mouse wheel rotation. Zoom is now: "),
                            str(self.zoom)])
        if text:
            self.render(text)
            # Here called the parent, but better to do it in other ways
            self.parent.update_scroll_bar()
        else:
            self.Refresh()  # triggers the paint event

    def on_key(self, event):
        """Read and process keyboard input"""
        key_code = event.GetKeyCode()
        text = _('Keyboard Input')

        if (key_code in (wx.WXK_LEFT, wx.WXK_RIGHT)) \
                and (self.signal_width > self.parent.full_width):
            full_width = self.parent.full_width
            length = self.parent.hbar.GetRange()
            thumb_size = self.parent.hbar.GetThumbSize()
            if key_code == wx.WXK_LEFT:
                self.pan_x += 10
                if self.pan_x > 0:
                    self.pan_x = 0
            elif key_code == wx.WXK_RIGHT:
                self.pan_x -= 10
                if self.pan_x < -(self.signal_width-full_width):
                    self.pan_x = -(self.signal_width-full_width)
            thumb_pos = -self.pan_x * (length - thumb_size) \
                / (self.signal_width - full_width)
            self.parent.hbar.SetThumbPosition(thumb_pos)
        if key_code in (wx.WXK_UP, wx.WXK_DOWN) \
                and (self.signal_count > self.max_signal_count):
            full_length = self.parent.full_length
            length = self.parent.vbar.GetRange()
            thumb_size = self.parent.vbar.GetThumbSize()
            if key_code == wx.WXK_DOWN:
                self.pan_y += 10
                if self.pan_y > 0:
                    self.pan_y = 0
            elif key_code == wx.WXK_UP:
                self.pan_y -= 10
                if self.pan_y < -50*(self.signal_count-self.max_signal_count):
                    self.pan_y = -50*(self.signal_count-self.max_signal_count)

            thumb_pos = (self.pan_y + 50 *
                         (self.signal_count-self.max_signal_count)) *\
                full_length/(self.signal_count*50)
            self.parent.vbar.SetThumbPosition(thumb_pos)

        if text:
            self.init = False
            self.render(text)

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        y_pos = y_pos - offset
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
        """Two vertices having same y coord"""
        x = start+cycle_count*step
        x_next = start+(cycle_count+1)*step
        y = 75+25*level+pos*50-offset
        GL.glVertex2f(x/self.zoom, y)
        GL.glVertex2f(x_next/self.zoom, y)

    def draw_rect_background(self, start_x, start_y, end_x, end_y, color=0.94):
        """Draw rectangular background.

        if type(color) == float, then use grey level.
        if type(color) == list, then use RGB.
        """
        start_y = start_y - offset
        end_y = end_y - offset
        if isinstance(color, (int, float)) and 0 <= color <= 1:
            red_f = green_f = blue_f = color
        elif isinstance(color, list) and len(color) == 3:
            red_f, green_f, blue_f = color
        else:
            raise TypeError("wrong type or value for 'color'")
        GL.glColor3f(red_f, green_f, blue_f)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(start_x, start_y)
        GL.glVertex2f(start_x, end_y)
        GL.glVertex2f(end_x, end_y)
        GL.glVertex2f(end_x, start_y)
        GL.glEnd()

    def draw_rect_frame(self, start_x, start_y, end_x, end_y, color=0):
        """Draw rectangular frame.

        if type(color) == float, then use grey level.
        if type(color) == list, then use RGB.
        """
        start_y = start_y - offset
        end_y = end_y - offset
        if isinstance(color, (int, float)) and 0 <= color <= 1:
            red_f = green_f = blue_f = color
        elif isinstance(color, list) and len(color) == 3:
            red_f, green_f, blue_f = color
        else:
            raise TypeError("wrong type or value for 'color'")
        GL.glColor3f(red_f, green_f, blue_f)
        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex2f(start_x, start_y)
        GL.glVertex2f(start_x, end_y)
        GL.glVertex2f(end_x, end_y)
        GL.glVertex2f(end_x, start_y)
        GL.glVertex2f(start_x, start_y)
        GL.glEnd()

    def draw_ruler(self, step, start_x, start_y):
        """Draw ruler under monitors"""
        start_y = start_y - offset
        GL.glColor3f(1, 69.0/255, 0)  # orangered
        GL.glBegin(GL.GL_LINE_STRIP)
        cur_x = start_x
        cur_y = start_y
        GL.glVertex2f(cur_x, cur_y)
        for cycle in range(60):
            if cycle % 10 == 0:
                scale_len = 8
            elif cycle % 5 == 0:
                scale_len = 6
            else:
                scale_len = 4
            GL.glVertex2f(cur_x, cur_y + scale_len)
            GL.glVertex2f(cur_x, cur_y)
            GL.glVertex2f(cur_x + step, cur_y)
            cur_x += step
        GL.glVertex2f(cur_x, cur_y + 8)
        GL.glEnd()
        # Draw scale numbers
        scale_num = 60 * (self.current_page - 1)
        cur_x = start_x
        cur_y = start_y - 15
        offset_ratio = 3.5/self.zoom
        for cycle in range(6):
            self.render_text(str(scale_num),
                             cur_x - len(str(scale_num)) *
                             offset_ratio, cur_y + offset)
            scale_num += 10
            cur_x += step * 10
        self.render_text(str(scale_num),
                         cur_x - len(str(scale_num)) *
                         offset_ratio, cur_y + offset)

    def get_ruler_cycle_num(self, step, start_x):
        """Get the current cycle number based on current x pos."""
        cursor_pos_on_ruler = self.current_x - self.pan_x - start_x*self.zoom
        cursor_pos_on_ruler /= self.zoom
        if cursor_pos_on_ruler < 0:
            return 0
        return int(cursor_pos_on_ruler / step) + 1

    def mouse_in_active_region(self, strip_raise, max_pos, ruler_offset):
        """ Detect if mouse is on one of the signal """
        return ruler_offset < self.current_y + offset \
            <= strip_raise + 50*max_pos + self.pan_y

    def find_nearest_signal_pos(self, strip_raise, max_pos, ruler_offset):
        """Find the nearest signal position in the active region."""
        min_pos = 0
        while ruler_offset - self.pan_y >= strip_raise + 50*min_pos:
            min_pos += 1
        for pos in range(min_pos, max_pos):
            if self.current_y + offset - self.pan_y <= strip_raise + 50*pos:
                return pos
        return max_pos

    def render_signal(self):
        """Display the signal trace(s) in GUI"""

        # To confine name lengths, edit in the future
        margin = 10

        # local variables
        cycle_count = 0  # count number of cycles displayed
        pos = 0  # signal position, shifted upward for each signal
        start = 50  # start point for rasterisation
        # No of cycles to be displayed on this page
        last_cycle = min((self.cycles-(self.current_page-1)*60), 60)
        # end point for rasterisation
        end = max(last_cycle*9*self.zoom + start, start)
        if last_cycle != 0:
            step = (end-start)/last_cycle
        else:
            step = 0

        self.signal_width = end+10

        size = self.GetClientSize()
        # cycle num between 1 and 60
        current_cycle_num = self.get_ruler_cycle_num(step/self.zoom,
                                                     50/self.zoom)
        # real cycle num here
        current_cycle_num_real = current_cycle_num + 60*(self.current_page - 1)

        # Draw the first strip under the first device
        strip_raise = 113
        self.draw_rect_background(0, strip_raise+2-50,
                                  max(2000, 2000/self.zoom), strip_raise-2-50)

        # infobox states
        infobox_cycle = current_cycle_num_real
        infobox_port = None
        infobox_value = _('empty')

        self.signal_count = len(self.monitors.monitors_dictionary)
        self.max_signal_count = int(size.height / 50) - 2

        current_pressed_id = self.monitored_list_pressed_id
        # Iterate over each device and render
        for list_id, (device_id, output_id) in enumerate(self.monitored_list):
            monitor_name = self.devices.get_signal_name(device_id, output_id)
            signal_list = self.monitors.monitors_dictionary[(device_id,
                                                             output_id)]

            # Highlight current monitored device
            if strip_raise + 50*(pos - 1) < self.current_y - \
                    self.pan_y + offset <= strip_raise + 50*pos \
                    and 0 < self.current_x < size.width - 1:
                if self.mouse_button_is_down and self.drag_mode:
                    current_pressed_id = list_id
                    if self.monitored_list_pressed_id is None:
                        self.monitored_list_pressed_id = list_id
                    self.draw_rect_background(0, strip_raise-2+pos*50,
                                              max(2000, 2000/self.zoom),
                                              strip_raise+2+(pos-1)*50,
                                              [1, 0.75, 0.65])  # orange
                else:
                    self.draw_rect_background(0, strip_raise-2+pos*50,
                                              max(2000, 2000/self.zoom),
                                              strip_raise+2+(pos-1)*50,
                                              [0.9, 1, 0.95])  # green
                names = self.devices.names
                if output_id is None:
                    infobox_port = names.get_name_string(device_id)
                else:
                    infobox_port = names.get_name_string(device_id) +\
                        '.'+names.get_name_string(output_id)
                monitor_highlighted = True
            elif self.drag_mode and \
                    pos == self.find_nearest_signal_pos(
                        113, len(self.monitored_list)-1, 65):
                self.draw_rect_background(0, strip_raise-2+pos*50,
                                          max(2000, 2000/self.zoom),
                                          strip_raise+2+(pos-1)*50,
                                          [1, 0.75, 0.65])  # orange
                monitor_highlighted = True
            else:
                monitor_highlighted = False

            # Draw the grey strip between devices
            self.draw_rect_background(0, strip_raise+2+pos*50,
                                      max(2000, 2000/self.zoom),
                                      strip_raise-2+pos*50)

            # Display signal name
            self.render_text(monitor_name[0:margin], 10/self.zoom, 80+pos*50)

            # Start drawing the current signal
            GL.glColor3f(0.0, 0.0, 1.0)  # signal trace is blue
            GL.glBegin(GL.GL_LINE_STRIP)

            # Iterate over each cycle and render
            cycle_count = 0
            for signal in signal_list[(self.current_page-1)*60:
                                      (self.current_page-1)*60+last_cycle]:
                if signal == self.devices.HIGH:
                    self.draw_horizontal_signal(start,
                                                cycle_count, step, 1, pos)
                    cycle_count += 1
                    if monitor_highlighted and \
                            cycle_count == current_cycle_num:
                        infobox_value = 1
                if signal == self.devices.LOW:
                    self.draw_horizontal_signal(start,
                                                cycle_count, step, 0, pos)
                    cycle_count += 1
                    if monitor_highlighted and \
                            cycle_count == current_cycle_num:
                        infobox_value = 0
                if signal == self.devices.RISING:
                    continue
                if signal == self.devices.FALLING:
                    continue
                if signal == self.devices.BLANK:
                    cycle_count += 1
            pos = pos+1
            GL.glEnd()

        # Draw grey background for ruler
        self.draw_rect_background(0, 29-self.pan_y,
                                  max(2000, 2000/self.zoom), 65-self.pan_y)

        if self.mouse_button_is_down:
            if self.monitored_list_pressed_id != current_pressed_id:
                k1, k2 = self.monitored_list_pressed_id, current_pressed_id
                mlist = self.monitored_list
                mlist[k1], mlist[k2] = mlist[k2], mlist[k1]  # swap elements
                self.monitored_list_pressed_id = current_pressed_id
        else:  # Draw the stipple line
            stipple_y_bottom = 64 - self.pan_y
            stipple_y_top = strip_raise+(pos-1)*50
            if 0 < self.current_x < size.width - 1 \
                    and 1 <= current_cycle_num <= 60 \
                    and stipple_y_bottom \
                    <= self.current_y - self.pan_y + offset <= stipple_y_top:
                self.draw_vertical_stipple_line(stipple_y_bottom,
                                                stipple_y_top)
                self.draw_info_box(infobox_cycle, infobox_port,
                                   infobox_value)

        # Draw white background for text
        self.draw_rect_background(0, 0-self.pan_y,
                                  max(2000, 2000/self.zoom), 29-self.pan_y, 1)

        # Draw the ruler
        self.draw_ruler(step/self.zoom, 50/self.zoom, 49 - self.pan_y)

    def draw_vertical_stipple_line(self, stipple_y_bottom, stipple_y_top):
        """Draw the vertical dotted line for cycle number alignment."""
        stipple_y_top = stipple_y_top - offset
        stipple_y_bottom = stipple_y_bottom - offset
        GL.glEnable(GL.GL_LINE_STIPPLE)
        GL.glLineStipple(1, 0x3333)
        GL.glColor3f(1, 0.65, 0)
        GL.glBegin(GL.GL_LINES)
        GL.glVertex2f((self.current_x-self.pan_x) /
                      self.zoom, stipple_y_bottom-14)
        GL.glVertex2f((self.current_x - self.pan_x)/self.zoom, stipple_y_top)
        GL.glEnd()
        GL.glDisable(GL.GL_LINE_STIPPLE)

    def draw_info_box(self, cycle, port, value):
        """Draw the MATLAB-like yellow info box which moves with mouse."""
        if self.parent.language == 0:
            self.draw_info_box_lang_en(cycle, port, value)
        else:
            self.draw_info_box_lang_cn(cycle, port, value)

    def draw_info_box_lang_en(self, cycle, port, value):
        """Draw the MATLAB-like yellow info box which moves with mouse.
           For English mode."""
        hsep = 6.2
        vsep = 14
        info1 = 'cycle: ' + str(cycle)
        info2 = 'port: ' + str(port)
        info3 = 'value: ' + str(value)
        rect_width = max(map(len, (info1, info2, info3)))*hsep + 4
        rect_height = 3*vsep + 4
        size = self.GetClientSize()
        if self.current_x + rect_width + 5 > size.width:  # left aligned
            x_pos = (self.current_x - self.pan_x + 3 - rect_width)/self.zoom
            y_pos = self.current_y - self.pan_y + 6 + offset
            rect_x_start = (self.current_x - self.pan_x - rect_width)/self.zoom
            rect_y_start = self.current_y - self.pan_y + offset
            rect_x_end = (self.current_x - self.pan_x)/self.zoom
            rect_y_end = self.current_y - self.pan_y + rect_height + offset
        else:  # right aligned
            x_pos = (self.current_x - self.pan_x + 2)/self.zoom
            y_pos = self.current_y - self.pan_y + 6 + offset
            rect_x_start = (self.current_x - self.pan_x)/self.zoom
            rect_y_start = self.current_y - self.pan_y + offset
            rect_x_end = (self.current_x - self.pan_x + rect_width)/self.zoom
            rect_y_end = self.current_y - self.pan_y + rect_height + offset
        self.draw_rect_background(rect_x_start, rect_y_start,
                                  rect_x_end, rect_y_end, [1, 0.98, 0.81])
        self.draw_rect_frame(rect_x_start, rect_y_start,
                             rect_x_end, rect_y_end)
        self.render_text(info1, x_pos, y_pos + vsep*2)
        self.render_text(info2, x_pos, y_pos + vsep)
        self.render_text(info3, x_pos, y_pos)

    def draw_info_box_lang_cn(self, cycle, port, value):
        """Draw the MATLAB-like yellow info box which moves with mouse.
           For Chinese mode (use texture mapping)."""
        hsep = 6.2
        vsep = 16.2
        info1 = str(cycle)
        info2 = str(port)
        info3 = str(value)
        box_height = 54
        box_width = 76/46 * box_height
        size = self.GetClientSize()
        if self.current_x + box_width + 5 > size.width:
            x_offset = box_width
        else:
            x_offset = 0
        self.texture_mapping(x_offset)
        x_pos = (self.current_x - self.pan_x + 40 - x_offset)/self.zoom
        y_pos = self.current_y - self.pan_y + 7 + offset
        self.render_text(info1, x_pos, y_pos + vsep*2)
        self.render_text(info2, x_pos, y_pos + vsep)
        self.render_text(info3, x_pos, y_pos)

    def texture_mapping(self, x_offset):
        """draw function """
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # enable textures, bind to our texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glColor3f(1, 1, 1)

        x_orig = (self.current_x - self.pan_x - x_offset) / self.zoom
        y_orig = self.current_y - self.pan_y
        box_height = 54
        box_width = 76/46 * box_height

        # draw a quad
        size = self.GetClientSize()
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0, 1)
        GL.glVertex2f(x_orig, y_orig + box_height)
        GL.glTexCoord2f(0, 0)
        GL.glVertex2f(x_orig, y_orig)
        GL.glTexCoord2f(1, 0)
        GL.glVertex2f(x_orig + box_width/self.zoom, y_orig)
        GL.glTexCoord2f(1, 1)
        GL.glVertex2f(x_orig + box_width/self.zoom, y_orig + box_height)
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    open_new(self, path): Open new definition file

    on_open(self): Event handler for open

    on_close(self, event): Event handler for close, including stop worker

    reset_all_labels(self): re-initialise labels when changed language

    on_menu(self, event): Event handler for the file menu.

    on_spin(self, event): Event handler for when the user changes the spin
                           control value.

    get_switch_signals(self): Get switch signals from switch IDs

    pop_switch_list(self, new_instance=0): Pop switch names in switch table

    run_network(self, cycles): Run the network for the specified number of
                               simulation cycles.

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_text_box(self, event): Event handler for when the user enters text.

    page_disp(self, text): Page display on the status bar

    text_bar(self, text): Display text on the status bar

    on_cont_button(self, event): Handle the event when continue button pressed

    switch_signal(self, switch_state): Update switch id and name list

    on_set_button(self, event): Handle the event when set button pressed

    on_clr_button(self, event): Handle the event when clear button pressed

    get_monitor_ids(self, signal): Get id according to the name

    on_sig_add_button(self, event): Handle the event when
                                    Add/Delete signal button pressed

    on_zoom_in_button(self, event): Handle the event when zoom
                                    in button pressed

    on_zoom_out_button(self, event): Handle the event when
                                     zoom out button pressed

    on_hbar(self, event): Handle the event when horizontal scroll bar is moved

    on_vbar(self, event): Handle the event when vertical scroll bar is moved

    update_vbar(self): Update vertical bar settings

    update_scroll_bar(self): Update horizontal scroll bar settings

    on_prev_button(self, event): Handle the event when PrevPage button Pressed

    on_next_button(self, event): Handle the event when NextPage button Pressed

    on_goto_button(self, event): Handle the event when Goto button pressed

    reinit(self, names, devices, network, monitors): Re-initialisation
                                                     when new file is opened
    """

    def __init__(self, title, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(900, 700))

        basepath = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.localedir = os.path.join(basepath, "locale")
        gettext.install('gui', self.localedir)
        self.language = 0
        if os.environ['LANG'] == 'en_GB.UTF-8':
            self.langauge = 0
        else:
            self.language = 1

        # Make objects local
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.names = names

        # Get monitors
        self.monitored_list, self.unmonitored_list = \
            self.monitors.get_signal_names()
        self.total_list = self.monitored_list + self.unmonitored_list
        self.monitor_window = 0

        # Cycles completed and worker for multithread
        self.cycles_completed = 0
        self.worker = RunThread(self)

        # Get switch list
        self.switch_ids = self.devices.find_devices(self.devices.SWITCH)
        self.switches = []
        self.get_switch_signals()

        # Configure the file menu
        fileMenu = wx.Menu()
        helpMenu = wx.Menu()

        self.menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, _("&About"))
        fileMenu.Append(wx.ID_OPEN, _("&Open"))
        fileMenu.Append(wx.ID_PREFERENCES, _("&Language"))
        fileMenu.Append(wx.ID_EXIT, _("&Exit"))
        helpMenu.Append(wx.ID_HELP, _("&Help"))
        self.menuBar.Append(fileMenu, _("&File"))
        self.menuBar.Append(helpMenu, _("&Help"))
        self.SetMenuBar(self.menuBar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, devices, monitors)

        # Preparing Bitmaps for zoom buttons
        image_1 = wx.Image("./graphics/plus.png")
        image_1.Rescale(30, 30)
        plus = wx.Bitmap(image_1)
        image_2 = wx.Image("./graphics/minus.png")
        image_2.Rescale(30, 30)
        minus = wx.Bitmap(image_2)

        # Basic cycle control widgets
        self.text = wx.StaticText(self, wx.ID_ANY, _("Cycles"))
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", max=10**10)
        self.run_button = wx.Button(self, wx.ID_ANY, _("Run"))
        self.cont_button = wx.Button(self, wx.ID_ANY, _("Add"))

        # Monitor add/delete widgets
        self.text2 = wx.StaticText(self, wx.ID_ANY, _("Monitors"))
        self.sig_add_button = wx.Button(self,
                                        wx.ID_ANY, _("Add/Delete Monitor"))

        # Switch toggle widgets
        self.text3 = wx.StaticText(self, wx.ID_ANY, _("Switches"))

        # Define switch table
        self.list_ctrl = wx.ListCtrl(self, size=(-1, 100),
                                     style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, _('Switches'), width=90)
        self.list_ctrl.InsertColumn(1, _('Values'), width=75)
        self.pop_switch_list(new_instance=1)
        self.set_button = wx.Button(self, wx.ID_ANY, "1")
        self.clr_button = wx.Button(self, wx.ID_ANY, "0")

        # Zoom in/out functions
        self.text4 = wx.StaticText(self, wx.ID_ANY, _("Zoom in/out"))
        self.zoom_in_button = wx.BitmapButton(self, wx.ID_ANY, plus,
                                              size=(50, 50))
        self.zoom_out_button = wx.BitmapButton(self, wx.ID_ANY, minus,
                                               size=(50, 50))

        # Display texture mapping
        # self.hero_button = wx.Button(self, wx.ID_ANY, "HERO")
        self.prev_button = wx.Button(self, wx.ID_ANY, _("Prev Page"))
        self.next_button = wx.Button(self, wx.ID_ANY, _("Next Page"))
        self.text_box = wx.TextCtrl(self, wx.ID_ANY, "",
                                    style=wx.TE_PROCESS_ENTER)
        self.goto_button = wx.Button(self, wx.ID_ANY, _("Goto"))
        self.textbar = self.CreateStatusBar(2)
        self.textbar.SetStatusWidths([800, 200])
        self.textbar.SetMinHeight(20)

        # Scroll Bars
        self.full_width = 645
        self.hbar = wx.ScrollBar(self, id=wx.ID_ANY, size=(-1, 15),
                                 style=wx.SB_HORIZONTAL)
        self.hbar.SetScrollbar(0, self.full_width, self.full_width, 1)

        # Vertical Scroll Bar
        self.full_length = 1000
        self.vbar = wx.ScrollBar(self, id=wx.ID_ANY, size=(15, 1000),
                                 style=wx.SB_VERTICAL)
        self.vbar.SetScrollbar(0, self.full_length, self.full_length, 1)

        # Bind events to widgets
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.spin.Bind(wx.EVT_SPINCTRL, self.on_spin)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.cont_button.Bind(wx.EVT_BUTTON, self.on_cont_button)

        self.set_button.Bind(wx.EVT_BUTTON, self.on_set_button)
        self.clr_button.Bind(wx.EVT_BUTTON, self.on_clr_button)

        self.sig_add_button.Bind(wx.EVT_BUTTON, self.on_sig_add_button)

        self.zoom_in_button.Bind(wx.EVT_BUTTON, self.on_zoom_in_button)
        self.zoom_out_button.Bind(wx.EVT_BUTTON, self.on_zoom_out_button)
        # self.hero_button.Bind(wx.EVT_BUTTON, self.on_hero_button)
        self.hbar.Bind(wx.EVT_SCROLL, self.on_hbar)
        self.vbar.Bind(wx.EVT_SCROLL, self.on_vbar)
        self.prev_button.Bind(wx.EVT_BUTTON, self.on_prev_button)
        self.next_button.Bind(wx.EVT_BUTTON, self.on_next_button)
        self.goto_button.Bind(wx.EVT_BUTTON, self.on_goto_button)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer_second = wx.BoxSizer(wx.VERTICAL)
        main_sizer_third = wx.BoxSizer(wx.HORIZONTAL)
        double_butt = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_2 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_3 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_4 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_5 = wx.BoxSizer(wx.HORIZONTAL)
        double_butt_6 = wx.BoxSizer(wx.HORIZONTAL)

        # Sizer arrangement
        main_sizer.Add(main_sizer_second, 25,
                       wx.EXPAND | wx.RIGHT | wx.TOP | wx.LEFT, 5)
        main_sizer_second.Add(self.canvas, 20,
                              wx.EXPAND | wx.RIGHT | wx.TOP | wx.LEFT, 5)
        main_sizer_second.Add(self.hbar, 1,
                              wx.EXPAND | wx.RIGHT | wx.BOTTOM | wx.LEFT, 5)
        main_sizer.Add(main_sizer_third, 1, wx.EXPAND, 5)
        main_sizer_third.Add(self.vbar, 1, wx.BOTTOM, 80)
        main_sizer.Add(side_sizer, 5, wx.ALL, 5)

        side_sizer.Add(self.text, 1, wx.TOP, 10)
        side_sizer.Add(self.spin, 1, wx.ALL, 5)
        side_sizer.Add(double_butt, 1, wx.ALL, 0)
        double_butt.Add(self.run_button, 1, wx.ALL, 5)
        double_butt.Add(self.cont_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text2, 1, wx.TOP, 10)
        side_sizer.Add(double_butt_2, 1, wx.ALL, 0)
        double_butt_2.Add(self.sig_add_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text3, 1, wx.TOP, 10)
        side_sizer.Add(self.list_ctrl, 1, wx.ALL, 5)
        side_sizer.Add(double_butt_3, 1, wx.ALL, 0)
        double_butt_3.Add(self.set_button, 1, wx.ALL, 5)
        double_butt_3.Add(self.clr_button, 1, wx.ALL, 5)

        side_sizer.Add(self.text4, 1, wx.TOP, 10)
        side_sizer.Add(double_butt_4, 0.2, wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        double_butt_4.Add(self.zoom_in_button, 1, wx.RIGHT | wx.LEFT, 18)
        double_butt_4.Add(self.zoom_out_button, 1, wx.RIGHT | wx.LEFT, 18)
        side_sizer.Add(double_butt_5, 1, wx.ALL, 0)
        double_butt_5.Add(self.prev_button, 0.8, wx.ALL, 0)
        double_butt_5.Add(self.next_button, 0.8, wx.ALL, 0)
        side_sizer.Add(double_butt_6, 1, wx.ALL, 0)
        double_butt_6.Add(self.text_box, 0.8, wx.ALL, 0)
        double_butt_6.Add(self.goto_button, 0.8, wx.ALL, 0)

        self.SetSizeHints(700, 600)
        self.SetSizer(main_sizer)

    def open_new(self, path):
        """Initialise instances of the four inner simulator classes"""
        new_names = Names()
        new_devices = Devices(new_names)
        new_network = Network(new_names, new_devices)
        new_monitors = Monitors(new_names, new_devices, new_network)
        new_scanner = Scanner(path, new_names)
        parser = Parser(new_names, new_devices, new_network,
                        new_monitors, new_scanner)
        if parser.parse_network():
            if self.monitor_window == 1:
                self.top.program_close()
            self.worker.stop()
            self.reinit(new_names, new_devices, new_network, new_monitors)
            self.canvas.monitored_list = \
                list(self.monitors.monitors_dictionary.keys())
        else:
            message = parser.message
            count = parser.error_count
            message = _('Parser: ') + str(count) + \
                _(' Errors Generated!!\n\n') + message
            errormsg = ErrorDispFrame(self, message)
            errormsg.Show()

    def on_open(self):
        """ask the user what new file to open"""
        with wx.FileDialog(self, _("Open definition file"),
                           wildcard="XYZ files (*.txt)|*.txt",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) \
                as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                self.open_new(pathname)
            except IOError:
                wx.LogError("Cannot open file '%s'." % newfile)
        fileDialog.Destroy()

    def on_close(self, event):
        """Stop everything running in background"""
        if self.monitor_window == 1:
            self.top.program_close()

        # Stop workers
        self.worker.stop()
        event.Skip()

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            wx.MessageBox(_("Logic Simulator\nTeam 4 Version\n2018"),
                          _("About Logsim"), wx.ICON_INFORMATION | wx.OK)
        if Id == wx.ID_OPEN:
            self.on_open()
        if Id == wx.ID_HELP:
            f = open("help.txt")
            message = f.read()
            box = wx.MessageDialog(self, message,
                                   _("Definition Description"),
                                   wx.ICON_INFORMATION | wx.OK)
            box.ShowModal()
        if Id == wx.ID_PREFERENCES:
            message = _('Do you want to use Chinese Version?')
            box = wx.MessageDialog(self, message,
                                   _("Language"),
                                   wx.ICON_INFORMATION | wx.YES_NO)
            result = box.ShowModal()
            if result == wx.ID_YES:
                mytranslation = gettext.translation('gui',
                                                    self.localedir, ['zh_CN'])
                self.language = 1
                mytranslation.install()
                self.reset_all_labels()
            else:
                mytranslation = gettext.NullTranslations()
                self.language = 0
                mytranslation.install()
                self.reset_all_labels()

    def reset_all_labels(self):
        """Reset all labels when changing language"""
        self.SetTitle(_("Logic Simulator"))
        self.run_button.SetLabel(_('Run'))
        self.text.SetLabel(_("Cycles"))
        self.text2.SetLabel(_("Monitors"))
        self.text3.SetLabel(_("Switches"))
        self.text4.SetLabel(_("Zoom in/out"))
        self.cont_button.SetLabel(_("Add"))
        self.sig_add_button.SetLabel(_("Add/Delete Monitor"))

        col = self.list_ctrl.GetColumn(0)
        col.SetText(_('Switches'))
        self.list_ctrl.SetColumn(0, col)
        col = self.list_ctrl.GetColumn(1)
        col.SetText(_('Values'))
        self.list_ctrl.SetColumn(1, col)

        self.prev_button.SetLabel(_("Prev Page"))
        self.next_button.SetLabel(_("Next Page"))
        self.goto_button.SetLabel(_("Goto"))
        self.menuBar.SetLabel(wx.ID_ABOUT, _("&About"))
        self.menuBar.SetLabel(wx.ID_OPEN, _("&Open"))
        self.menuBar.SetLabel(wx.ID_PREFERENCES, _("&Language"))
        self.menuBar.SetLabel(wx.ID_EXIT, _("&Exit"))
        self.menuBar.SetLabel(wx.ID_HELP, _("&Help"))
        self.menuBar.SetMenuLabel(0, _("&File"))
        self.menuBar.SetMenuLabel(1, _("&Help"))

    def on_spin(self, event):
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join([_("New spin control value: "), str(spin_value)])
        self.canvas.render(text)

    def get_switch_signals(self):
        """Get switch signals from switch IDs"""
        self.switches = []
        for each_id in self.switch_ids:
            switch_pair = (self.names.get_name_string(each_id),
                           self.devices.get_device(each_id).switch_state)
            self.switches.append(switch_pair)

    def pop_switch_list(self, new_instance=0):
        """Pop switch names in switch table"""
        index = 0
        for switch in self.switches:
            if new_instance == 1:
                self.list_ctrl.InsertItem(index, switch[0])
            else:
                self.list_ctrl.SetItem(index, 0, switch[0])
            self.list_ctrl.SetItem(index, 1, str(switch[1]))
            index = index+1

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
        self.network.cycle_count = 0
        self.canvas.cycles = self.spin.GetValue()
        if self.canvas.cycles % 60 == 0:
            self.canvas.page_number = int(self.canvas.cycles/60)
        else:
            self.canvas.page_number = int(self.canvas.cycles/60)+1
        self.canvas.current_page = 1
        self.cycles_completed = min(self.canvas.cycles, 60)
        self.monitors.reset_monitors()
        if self.run_network(self.cycles_completed):
            text = _("Run button pressed.")
        else:
            device_name = \
                self.names.get_name_string(self.network.device_no_input)
            text = _('DEVICE \"') + device_name + _('\" is oscillatory!')
        # Set another threading to run unfinished cycles in the background
        self.worker = RunThread(self)
        self.worker.start()
        # Update scroll bars
        self.update_vbar()
        self.canvas.init = False
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join([_("New text box value: "), text_box_value])
        self.canvas.render(text)

    def page_disp(self, text):
        """Page display on the status bar"""
        self.textbar.SetStatusText(text, 1)

    def text_bar(self, text):
        """Display text on the status bar"""
        self.textbar.SetStatusText(text, 0)

    def on_cont_button(self, event):
        """Handles the event when continue button pressed"""
        text = ''
        if self.canvas.run == 0:
            text = _('Press Run Button First!')
        else:
            text = _('Continue Button Pressed')
            added_cycles = self.spin.GetValue()
            self.canvas.cycles += added_cycles
            if self.canvas.cycles % 60 == 0:
                self.canvas.page_number = int(self.canvas.cycles/60)
            else:
                self.canvas.page_number = int(self.canvas.cycles/60)+1
            next_to_run = min((60-self.cycles_completed % 60), added_cycles)
            self.run_network(next_to_run)
            self.cycles_completed += next_to_run
        # Reset the worker with more cycles to run
        self.worker = RunThread(self)
        self.worker.start()
        # Update scroll bar
        self.canvas.render(text)
        self.update_scroll_bar()

    def switch_signal(self, switch_state):
        """Updates switch id and name list"""
        devices = []
        text = ''
        index = -1
        while True:
            index = self.list_ctrl.GetNextItem(index, wx.LIST_NEXT_ALL,
                                               wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            devices.append(self.switches[index][0])
        for device in devices:
            switch_id = self.names.query(device)
            if self.devices.set_switch(switch_id, switch_state):
                text = _("Successfully set switches.")
            else:
                text = _("Error! Invalid switch.")
        self.get_switch_signals()
        self.pop_switch_list()
        self.canvas.render(text)

    def on_set_button(self, event):
        """Handles the event when set button pressed"""
        if self.cycles_completed >= self.canvas.cycles:
            self.switch_signal(1)
        else:
            self.canvas.render(_("Warning! Still have uncompleted cycles!"))

    def on_clr_button(self, event):
        """Handles the event when clear button pressed"""
        if self.cycles_completed >= self.canvas.cycles:
            self.switch_signal(0)
        else:
            self.canvas.render(_("Warning! Still have uncompleted cycles!"))

    def get_monitor_ids(self, signal):
        """Gets id according to the name"""
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
        """Handles the event when Add/Delete signal button pressed"""
        if self.monitor_window == 0:
            self.top = MonitorFrame(self, _("Monitors"),
                                    self.monitored_list,
                                    self.unmonitored_list)
            self.top.Show()
            self.monitor_window = 1
        else:
            # Top the window if same button is pressed
            # without closing the previous frame
            self.top.ToggleWindowStyle(wx.STAY_ON_TOP)

    def on_zoom_in_button(self, event):
        """Handles the event when zoom_in button pressed"""
        text = 'Zoom in'
        self.canvas.zoom = self.canvas.zoom*2
        if self.canvas.zoom >= zoom_upper:
            self.canvas.zoom = zoom_upper
        self.canvas.init = False
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_zoom_out_button(self, event):
        """Handles the event when zoom out button pressed"""
        text = 'Zoom out'
        self.canvas.zoom = self.canvas.zoom*0.5
        if self.canvas.zoom <= zoom_lower:
            self.canvas.zoom = zoom_lower
        self.canvas.init = False
        self.canvas.render(text)
        self.update_scroll_bar()

    def on_hbar(self, event):
        """Handles the event when horizontal scroll bar is moved"""
        pos = self.hbar.GetThumbPosition()
        length = self.hbar.GetRange()
        thumbsize = self.hbar.GetThumbSize()
        if length > thumbsize:
            self.canvas.pan_x = -int((self.canvas.signal_width -
                                     self.full_width)*(pos/(length-thumbsize)))
            self.canvas.init = False
            self.canvas.render('')

    def on_vbar(self, event):
        """Handles the event when vertical scroll bar is moved"""
        pos = self.vbar.GetThumbPosition()
        length = self.vbar.GetRange()
        thumbsize = self.vbar.GetThumbSize()
        self.full_length = self.canvas.GetClientSize().height
        if length > thumbsize:
            self.canvas.pan_y = \
                -(self.canvas.signal_count -
                    self.canvas.max_signal_count)*50+50*pos *\
                self.canvas.signal_count/self.full_length
            self.canvas.init = False
            self.canvas.render(str(self.canvas.pan_y))

    def update_vbar(self):
        """Updates vertical bar settings"""
        self.canvas.pan_y = 0
        self.full_length = self.canvas.GetClientSize().height
        if self.canvas.max_signal_count < self.canvas.signal_count:
            vpos = self.full_length - \
                self.canvas.max_signal_count * \
                self.full_length/self.canvas.signal_count
            self.vbar.SetScrollbar(vpos,
                                   self.canvas.max_signal_count *
                                   self.full_length/self.canvas.signal_count,
                                   self.full_length, 1)
        else:
            self.vbar.SetScrollbar(0, self.full_length,
                                   self.full_length, self.canvas.zoom)

    def update_scroll_bar(self):
        """Updates horizontal scroll bar settings"""
        hpos = self.hbar.GetThumbPosition()
        if self.full_width < self.canvas.signal_width:
            self.hbar.SetScrollbar(hpos, self.full_width,
                                   self.canvas.signal_width, self.canvas.zoom)
        else:
            self.hbar.SetScrollbar(hpos, self.full_width,
                                   self.full_width, self.canvas.zoom)
        if self.canvas.max_signal_count < self.canvas.signal_count:
            vpos = self.vbar.GetThumbPosition()
            self.full_length = self.canvas.GetClientSize().height
            self.vbar.SetScrollbar(vpos,
                                   self.canvas.max_signal_count *
                                   self.full_length/self.canvas.signal_count,
                                   self.full_length, 1)
        else:
            self.vbar.SetScrollbar(0, self.full_length, self.full_length, 1)

    def on_prev_button(self, event):
        """Handles the event when PrevPage button Pressed"""
        if self.canvas.current_page > 1:
            self.canvas.current_page -= 1
            self.canvas.pan_x = 0
            self.canvas.init = False
        else:
            self.canvas.current_page = 1
        self.canvas.render(_('Turn to Previous Page'))

    def on_next_button(self, event):
        """Handles the event when NextPage button Pressed"""
        if self.canvas.current_page < self.canvas.page_number:
            next_to_run = min(self.canvas.cycles-self.canvas.current_page*60,
                              60)
            self.canvas.current_page += 1
            self.canvas.pan_x = 0
            self.canvas.init = False
            if self.canvas.current_page*60 > self.cycles_completed:
                self.run_network(next_to_run)
                self.cycles_completed += next_to_run
        else:
            self.canvas.current_page = self.canvas.page_number
        self.canvas.render(_('Turn to Next Page'))

    def on_goto_button(self, event):
        """Handles the event when Goto button pressed"""
        self.worker.stop()
        time.sleep(.100)
        page_number = self.text_box.GetValue()
        text = _("Go to page: ") + page_number
        page_number = page_number if page_number is not '' else \
            self.canvas.current_page
        to_run = int(page_number)*60-self.cycles_completed
        if to_run > 0:
            self.run_network(to_run)
            self.cycles_completed += to_run
        self.canvas.current_page = int(page_number)
        self.canvas.render(text)

        self.worker = RunThread(self)
        self.worker.start()

    def reinit(self, names, devices, network, monitors):
        """Re-initialisation when new file is opened"""
        # Make objects local
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.names = names

        # Get monitors
        self.monitored_list, self.unmonitored_list = \
            self.monitors.get_signal_names()
        self.total_list = self.monitored_list + self.unmonitored_list
        self.monitor_window = 0

        # Cycles completed and worker for multithread
        self.cycles_completed = 0
        self.worker = RunThread(self)

        self.switch_ids = self.devices.find_devices(self.devices.SWITCH)
        self.switches = []
        self.get_switch_signals()

        self.list_ctrl.ClearAll()
        self.list_ctrl.InsertColumn(0, _('Switches'), width=90)
        self.list_ctrl.InsertColumn(1, _('Values'), width=75)
        self.pop_switch_list(new_instance=1)

        self.hbar.SetScrollbar(0, self.full_width, self.full_width, 1)
        self.canvas.init = False
        self.canvas.monitors = self.monitors
        self.canvas.devices = self.devices
        self.canvas.parent = self
        self.canvas.init_parameters()
        self.canvas.signal_count = \
            len(self.canvas.monitors.monitors_dictionary)
        self.update_vbar()


class MonitorFrame(wx.Frame):
    """Configure the Monitor Window and the widgets.

    This class provides a promprt Frame for Monitor lists and
    enables the user to change the monitors.

    Parameters
    ----------
    title: the title of the application

    Public methods
    --------------
    refresh_lists(self): Update list display after add/delete button pressed

    on_close(self, event): Handle the event when close button pressed

    on_close(self, event): Handle the event when close button pressed

    on_add(self, event): Handle the event when add button pressed

    on_delete(self, event): Handle the event when delete button pressed
    """
    def __init__(self, parent, title, monitored, unmonitored):
        """Initialise Widgets and layouts"""
        wx.Frame.__init__(self, None, title=title,
                          pos=(350, 150), size=(350, 600))
        # make class objects local
        self.parent = parent
        self.monitored = monitored
        self.unmonitored = unmonitored
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Menu bar settings
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, _("E&xit\tAlt-X"),
                             _("Close window and exit program."))
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        menuBar.Append(menu, _("&File"))
        self.SetMenuBar(menuBar)

        panel = wx.Panel(self)
        # Instantiate Sizers
        box = wx.BoxSizer(wx.VERTICAL)
        list_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Set and add text
        m_text = wx.StaticText(panel, -1, _("Select Signal"))
        m_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        m_text.SetSize(m_text.GetBestSize())
        box.Add(m_text, 1, wx.ALL, 5)

        # Instantiate and set list control object
        self.list_ctrl_1 = wx.ListCtrl(panel, size=(-1, 100),
                                       style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl_2 = wx.ListCtrl(panel, size=(-1, 100),
                                       style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl_1.InsertColumn(0, _('Monitored'), width=160)
        self.list_ctrl_2.InsertColumn(0, _('Unmonitored'), width=160)
        index = 0
        for signal in self.monitored:
            self.list_ctrl_1.InsertItem(index, signal)
            index = index+1

        for signal in self.unmonitored:
            self.list_ctrl_2.InsertItem(index, signal)
            index = index+1

        # Add list control to the panel
        box.Add(list_sizer, 10, wx.ALL, 0)
        list_sizer.Add(self.list_ctrl_1, 1, wx.EXPAND | wx.ALL, 5)
        list_sizer.Add(self.list_ctrl_2, 1, wx.EXPAND | wx.ALL, 5)

        side_sizer = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(side_sizer, 1, wx.ALL, 5)

        # Instantiate functional buttons
        add = wx.Button(panel, wx.ID_CLOSE, _("ADD"))
        delete = wx.Button(panel, wx.ID_CLOSE, _("DELETE"))
        close = wx.Button(panel, wx.ID_CLOSE, _("CLOSE"))
        # Bind buttons to the functions
        add.Bind(wx.EVT_BUTTON, self.on_add)
        delete.Bind(wx.EVT_BUTTON, self.on_delete)
        close.Bind(wx.EVT_BUTTON, self.on_close)
        # Add buttons to the panel
        side_sizer.Add(add, 1, wx.ALL, 5)
        side_sizer.Add(delete, 1, wx.ALL, 5)
        side_sizer.Add(close, 1, wx.ALL, 5)

        panel.SetSizer(box)
        panel.Layout()

    def refresh_lists(self):
        """Updates list display after add/delete button pressed"""
        self.list_ctrl_1.DeleteAllItems()
        self.list_ctrl_2.DeleteAllItems()
        for index, signal in enumerate(self.monitored):
            self.list_ctrl_1.InsertItem(index, signal)
        for index, signal in enumerate(self.unmonitored):
            self.list_ctrl_2.InsertItem(index, signal)

    def on_close(self, event):
        """Handles the event when close button pressed"""
        self.parent.monitor_window = 0
        self.Destroy()

    def program_close(self):
        """Handles other close event"""
        self.Destroy()

    def on_add(self, event):
        """Handles the event when add button pressed"""
        signals = []
        text = ''
        index = -1
        while True:
            index = self.list_ctrl_2.GetNextItem(index, wx.LIST_NEXT_ALL,
                                                 wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            signals.append(self.unmonitored[index])

        # Delete monitor using the IDs above
        for signal in signals:
            device_id, port_id = self.parent.get_monitor_ids(signal)
            monitor_error = \
                self.parent.monitors.make_monitor(device_id, port_id,
                                                  self.parent.canvas.cycles)
            if monitor_error == self.parent.monitors.NO_ERROR:
                text = _("Successfully made monitor.")
                self.parent.monitored_list.append(signal)
                self.parent.unmonitored_list.remove(signal)
                self.parent.canvas.monitored_list.append((device_id, port_id))
                self.parent.canvas.signal_count += 1
            else:
                text = _("Error! Could not make monitor: ") + signal
        self.parent.update_vbar()
        self.parent.canvas.init = False
        self.parent.canvas.render(text)
        self.refresh_lists()

    def on_delete(self, event):
        """Handles the event when delete button pressed"""
        signals = []
        text = ''
        index = -1
        while True:
            index = self.list_ctrl_1.GetNextItem(index, wx.LIST_NEXT_ALL,
                                                 wx.LIST_STATE_SELECTED)
            if index == -1:
                break
            signals.append(self.monitored[index])

        # Delete monitor using the IDs above
        for signal in signals:
            device_id, port_id = self.parent.get_monitor_ids(signal)
            if self.parent.monitors.remove_monitor(device_id, port_id):
                text = _("Successfully zapped monitor")
                self.parent.unmonitored_list.append(signal)
                self.parent.monitored_list.remove(signal)
                self.parent.canvas.monitored_list.remove((device_id, port_id))
                self.parent.canvas.signal_count -= 1
            else:
                text = _("Error! Could not zap monitor: ") + signal
        self.parent.update_vbar()
        self.parent.canvas.init = False
        self.parent.canvas.render(text)
        self.refresh_lists()


class RunThread(threading.Thread):
    """Configure the Monitor Window and the widgets.

    This class provides a promprt Frame for Monitor lists and
    enables the user to change the monitors.

    Parameters
    ----------

    Public methods
    --------------
    run(self): Set the worker to run

    stop(self): Stop the worker, raise stop flag
    """
    def __init__(self, parent):
        """
        Workers running at the background without blocking the program
        or waiting for so long to finish
        @param parent: The gui object that should recieve the value
        """
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self._parent = parent

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        while self._parent.cycles_completed+1000 <= self._parent.canvas.cycles:
            time.sleep(.200)
            self._parent.run_network(500)
            self._parent.cycles_completed += 500
            if self._stop_event.is_set():
                break
        if not self._stop_event.is_set():
            left_to_run = self._parent.canvas.cycles - \
                self._parent.cycles_completed
            self._parent.run_network(left_to_run)
            self._parent.cycles_completed += left_to_run

    def stop(self):
        self._stop_event.set()


class ErrorDispFrame(wx.Frame):
    """Configure the Monitor Window and the widgets.

    This class provides a promprt Frame for Monitor lists and
    enables the user to change the monitors.

    Parameters
    ----------

    Public methods
    --------------
    on_confirm(self, event): Handle the event when confirm button is pressed
    """
    def __init__(self, parent, message):
        """initilise widgets and layout"""
        wx.Frame.__init__(self, None, title=_('Error in the File!!!'),
                          pos=(350, 100), size=(500, 550))
        self.parent = parent
        self.message = message

        # Set a monospace font for error display
        font1 = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                        wx.NORMAL, wx.NORMAL, False, u'Courier')

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        text = wx.TextCtrl(panel, wx.ID_ANY, message, size=(320, 250),
                           style=wx.TE_MULTILINE | wx.HSCROLL)
        text.SetFont(font1)
        box.Add(text, 20, wx.EXPAND | wx.ALL, 5)
        confirm = wx.Button(panel, wx.ID_CLOSE, _("Confirm"))
        confirm.Bind(wx.EVT_BUTTON, self.on_confirm)
        box.Add(confirm, 1, wx.RIGHT | wx.LEFT, 125)

        panel.SetSizer(box)
        panel.Layout()

    def on_confirm(self, event):
        """Handles the event when confirm button is pressed"""
        self.Destroy()
