import os, sys, re
import pyfirmata
import time
import async

class TwitchController:
    def __init__(self):
        # Want to maybe pass port through config
        self.board = pyfirmata.Arduino('/dev/ttyS3')
        self.it = pyfirmata.util.Iterator(self.board)
        self.it.start()
        
        # Joystick
        self.analog_x = None
        self.analog_y = None
        self.switch = None

    async def joystick_source(self):
        sw = self.board.get_pin('d:2:i')
        
        joystick_x = self.board.get_pin('a:0:i')
        joystick_y = self.board.get_pin('a:1:i')
        
        def sanitize_analog_out(x_input, y_input):
            new_x_range = [-1920/2, 1920/1]
            new_y_range = [-1080/2, 1080/1]
            
            # because old range is 0 to 1
            # normalized = ((new_range_max - new_range_min) * input) + new_range_min
            new_x = ((new_x_range[1] - new_x_range[0])* x_input) + new_x_range[0]
            new_y = ((new_y_range[1] - new_y_range[0])* y_input) + new_y_range[0]
            return new_x, new_y

        while True:
            x = joystick_x.read()
            y = joystick_y.read()
            if x is not None and y is not None:
                self.analog_x, self.analog_y = sanitize_analog_out(x,y)  
            self.switch = sw.read()
            yield self.analog_x, self.analog_y, self.switch
            asyncio.sleep(0.05)
        
        return 
            
if __name__ == "__main__":
    controller = TwitchController()
    vals = asyncio.ensure_future(controller.joystick_source())
    while True:
        
        print(contoller.analog_x, contoller.analog_y)
