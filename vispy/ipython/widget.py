# -*- coding: utf-8 -*-
# Copyright (c) 2014, 2015, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

from IPython.html.widgets import DOMWidget
from IPython.utils.traitlets import Unicode, Int, Bool
from vispy.app.backends._ipynb_util import create_glir_message
from vispy.app import Timer

# ---------------------------------------------------------- IPython Widget ---
def _stop_timers(canvas):
    """Stop all timers in a canvas."""
    for attr in dir(canvas):
        try:
            attr_obj = getattr(canvas, attr)
        except NotImplementedError:
            # This try/except is needed because canvas.position raises
            # an error (it is not implemented in this backend).
            attr_obj = None
        if isinstance(attr_obj, Timer):
            attr_obj.stop()

class VispyWidget(DOMWidget):
    _view_name = Unicode("VispyView", sync=True)

    #height/width of the widget is managed by IPython.
    #it's a string and can be anything valid in CSS.
    #here we only manage the size of the viewport.
    viewport_width = Int(sync=True)
    viewport_height = Int(sync=True)
    resizable = Bool(value=True, sync=True)


    def __init__(self, **kwargs):
        super(VispyWidget, self).__init__(**kwargs)
        w, h = kwargs.get('size', (500, 200))
        self.viewport_width = w
        self.viewport_height = h
        self.on_msg(self.events_received)
        self.canvas = None
        self.canvas_backend = None
        self.gen_event = None

    def set_canvas(self, canvas):
        self.canvas = canvas
        self.canvas_backend = self.canvas._backend
        self.canvas_backend.set_widget(self)
        self.gen_event = self.canvas_backend._gen_event
        self.canvas_backend._vispy_set_visible(True)

        #setup the backend widget then.

    def events_received(self, _, msg):
        if msg['msg_type'] == 'events':
            events = msg['contents']
            for ev in events:
                self.gen_event(ev)
        elif msg['msg_type'] == 'status':
            if msg['contents'] == 'removed':
                # Stop all timers associated to the widget.
                _stop_timers(self.canvas_backend._vispy_canvas)

    def send_glir_commands(self, commands):
        # TODO: check whether binary websocket is available (ipython >= 3)
        # Until IPython 3.0 is released, use base64.
        array_serialization = 'base64'
        # array_serialization = 'binary'
        if array_serialization == 'base64':
            msg = create_glir_message(commands, 'base64')
            msg['array_serialization'] = 'base64'
            self.send(msg)
        elif array_serialization == 'binary':
            msg = create_glir_message(commands, 'binary')
            msg['array_serialization'] = 'binary'
            # Remove the buffers from the JSON message: they will be sent
            # independently via binary WebSocket.
            buffers = msg.pop('buffers')
            self.comm.send({"method": "custom", "content": msg},
                           buffers=buffers)
