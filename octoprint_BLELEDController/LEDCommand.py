"""
Designed based on ELK-BLEDOM Protocol
https://github.com/FergusInLondon/ELK-BLEDOM/blob/master/PROTCOL.md
"""
class LEDCommand():
    def __init__(self, start_code: bytes, end_code: bytes) -> None:
        self.start_code = start_code
        self.end_code = end_code

    def set_start_end_code(self, start_code: bytes, end_code: bytes):
        self.start_code = start_code
        self.end_code = end_code

    """
        BYTE FORMAT IS AS FOLLOWS (FROM HIGH BYTE TO LOW BYTE)
           Byte | Value
           -------------
            1   | 0x7E
            2   | 0x00
            3   | 0x05
            4   | 0x03
            5   | uint8 - RED
            6   | uint8 - GREEN
            7   | uint8 - BLUE
            8   | 0x00
            9   | 0xEF
    """
    def create_set_color_command(self, r_compo: bytes, g_compo: bytes, b_compo: bytes):
        return bytearray([
             self.start_code
            ,0x00
            ,0x05
            ,0x03
            ,r_compo
            ,g_compo
            ,b_compo
            ,0x00
            ,self.end_code
        ])

    """
        BYTE FORMAT IS AS FOLLOWS (FROM HIGH BYTE TO LOW BYTE)
           Byte | Value
            -------------
            1   | 0x7E
            2   | 0x00
            3   | 0x01
            4   | uint8 - brightness (0-100 in decimal)
            5   | uint8 - light mode (?)
            6   | 0x00
            7   | 0x00
            8   | 0x00
            9   | 0xEF
    """
    def create_set_brightness_command(self, brightness: bytes, light_mode: bytes = 0xff):
        adjusted_brightness = brightness if brightness < 100 else 100
        return bytearray([
             self.start_code
            ,0x00
            ,0x01
            ,adjusted_brightness
            ,light_mode
            ,0x00
            ,0x00
            ,0x00
            ,self.end_code
        ])

    def create_turn_off_command(self):
        return self.create_set_brightness_command(0x00)

    def create_turn_on_command(self):
        return self.create_set_brightness_command(0x64)

if __name__ == '__main__':
    ledsController = LEDCommand(0x7e, 0xef)
    cmd = ledsController.create_set_color_command(0xff, 0xff, 0xff)
    for c in cmd:
        print(c)