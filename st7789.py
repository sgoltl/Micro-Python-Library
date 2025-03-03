import framebuf
import time
from machine import Pin, SPI

# Constants for the ST7789 commands
ST7789_NOP = 0x00
ST7789_SWRESET = 0x01
ST7789_RDDID = 0x04
ST7789_RDDST = 0x09

ST7789_SLPIN = 0x10
ST7789_SLPOUT = 0x11
ST7789_PTLON = 0x12
ST7789_NORON = 0x13

ST7789_INVOFF = 0x20
ST7789_INVON = 0x21
ST7789_DISPOFF = 0x28
ST7789_DISPON = 0x29
ST7789_CASET = 0x2A
ST7789_RASET = 0x2B
ST7789_RAMWR = 0x2C
ST7789_RAMRD = 0x2E

ST7789_PTLAR = 0x30
ST7789_COLMOD = 0x3A
ST7789_MADCTL = 0x36

ST7789_MADCTL_MY = 0x80
ST7789_MADCTL_MX = 0x40
ST7789_MADCTL_MV = 0x20
ST7789_MADCTL_ML = 0x10
ST7789_MADCTL_RGB = 0x00

COLOR_MODE_65K = 0x50
COLOR_MODE_262K = 0x60
COLOR_MODE_12BIT = 0x03
COLOR_MODE_16BIT = 0x05
COLOR_MODE_18BIT = 0x06
COLOR_MODE_16M = 0x07

class ST7789:

    COLORS = {
        "BLACK": 0x0000,
        "WHITE": 0xFFFF,
        "RED": 0x07E0,   
        "GREEN": 0x001F,  
        "BLUE": 0xF800,
        "YELLOW": 0x07FF,
        "CYAN": 0xF81F,       
        "PURPLE": 0x79E0,        
        "GRAY": 0x8410,       
        "DARK_GRAY": 0x4208,
    }




    def draw_centered_text(self, y, text, scale, color):
        """
        Draw text centered on the screen.
        """
        text_width = len(text) * 8 * scale
        x = (self.width - text_width) // 2
        self.draw_big_text(x, y, text, scale, color)

    def draw_outlined_text(self, x, y, text, scale, color, outline_color):
        """
        Draw outlined text for better readability.
        """
        offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in offsets:
            self.draw_big_text(x + dx, y + dy, text, scale, outline_color)
        self.draw_big_text(x, y, text, scale, color)

    def draw_multiline_text(self, x, y, text, scale, color, max_width=None):
        """
        Draw text with automatic line wrapping.
        """
        if max_width is None:
            max_width = self.width

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * 8 * scale <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            self.draw_big_text(x, y + (i * 10 * scale), line, scale, color)

    def draw_sprite(self, x, y, sprite, scale, color):
        """
        Draw a sprite (scale=2) on the LCD.
        """
        #scale = 2
        for row, line in enumerate(sprite):
            for col, pixel in enumerate(line):
                if pixel == "1":
                    self.framebuf.fill_rect(x + col * scale, y + row * scale, scale, scale, color)
    
    def draw_big_text(self, x, y, text, scale, color):
        """
        Draw bigger text by scaling the built-in 8x8 font.
        Renders each character into a small buffer, then scales that buffer.
        """
        char_width, char_height = 8, 8
        temp_buf = framebuf.FrameBuffer(
            bytearray(char_width * char_height * 2),
            char_width, char_height,
            framebuf.RGB565
        )

        offset_x = x
        for char in text:
            temp_buf.fill(0)
            temp_buf.text(char, 0, 0, color)
            for cy in range(char_height):
                for cx in range(char_width):
                    px_color = temp_buf.pixel(cx, cy)
                    if px_color != 0:
                        for sy in range(scale):
                            for sx in range(scale):
                                self.framebuf.pixel(offset_x + cx * scale + sx,
                                                    y + cy * scale + sy,
                                                    px_color)
            offset_x += char_width * scale
    
    def __init__(self, spi, cs, dc, rst, width=320, height=240):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = width
        self.height = height
        self.buffer = bytearray(self.width * self.height * 2)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)
        
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        
        self.reset()
        self.init_display()
        
    def reset(self):
        self.rst(1)
        time.sleep_ms(50)
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(50)
        
    def write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
        
    def write_data(self, data):
        self.cs(0)
        self.dc(1)
        self.spi.write(bytearray([data]))
        self.cs(1)
        
    def init_display(self):
        self.write_cmd(ST7789_SWRESET)
        time.sleep_ms(150)
        self.write_cmd(ST7789_SLPOUT)
        time.sleep_ms(500)
        
        self.write_cmd(ST7789_COLMOD)
        self.write_data(COLOR_MODE_16BIT)
        time.sleep_ms(10)
        
        self.write_cmd(ST7789_MADCTL)
        self.write_data(ST7789_MADCTL_MY | ST7789_MADCTL_MV | ST7789_MADCTL_RGB)
        
        self.set_window(0, 0, self.width - 1, self.height - 1)
        
        self.write_cmd(ST7789_INVON)
        time.sleep_ms(10)
        
        self.write_cmd(ST7789_NORON)
        time.sleep_ms(10)
        
        self.write_cmd(ST7789_DISPON)
        time.sleep_ms(500)
        
    def show(self):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.write_cmd(ST7789_RAMWR)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)
        
    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(ST7789_CASET)
        self.write_data(x0 >> 8)
        self.write_data(x0 & 0xFF)
        self.write_data(x1 >> 8)
        self.write_data(x1 & 0xFF)
        
        self.write_cmd(ST7789_RASET)
        self.write_data(y0 >> 8)
        self.write_data(y0 & 0xFF)
        self.write_data(y1 >> 8)
        self.write_data(y1 & 0xFF)
        
        self.write_cmd(ST7789_RAMWR)

    def rotate(self, rotation):
        self.write_cmd(ST7789_MADCTL)
        if rotation == 0:
            self.write_data(ST7789_MADCTL_MX | ST7789_MADCTL_MY | ST7789_MADCTL_RGB)
            self.width, self.height = 240, 320
        elif rotation == 1:
            self.write_data(ST7789_MADCTL_MY | ST7789_MADCTL_MV | ST7789_MADCTL_RGB)
            self.width, self.height = 320, 240
        elif rotation == 2:
            self.write_data(ST7789_MADCTL_RGB)
            self.width, self.height = 240, 320
        elif rotation == 3:
            self.write_data(ST7789_MADCTL_MX | ST7789_MADCTL_MV | ST7789_MADCTL_RGB)
            self.width, self.height = 320, 240
        
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)
        self.set_window(0, 0, self.width - 1, self.height - 1)
    
    def draw_pixel(self, x, y, color):
        self.framebuf.pixel(x, y, color)
            
    def draw_line(self, x0, y0, x1, y1, color):
        self.framebuf.line(x0, y0, x1, y1, color)
        
    def draw_rect(self, x, y, w, h, color):
        self.framebuf.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color):
        self.framebuf.fill_rect(x, y, w, h, color)
        
    def draw_triangle(self, x0, y0, x1, y1, x2, y2, color):
        self.draw_line(x0, y0, x1, y1, color)
        self.draw_line(x1, y1, x2, y2, color)
        self.draw_line(x2, y2, x0, y0, color)
        
    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        def draw_line(x0, y0, x1, y1):
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            while True:
                self.framebuf.pixel(x0, y0, color)
                if x0 == x1 and y0 == y1:
                    break
                e2 = err * 2
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        if y0 > y2:
            x0, y0, x2, y2 = x2, y2, x0, y0
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        if y1 == y2:
            a = x0
            b = x0
            if x1 < a:
                a = x1
            elif x1 > b:
                b = x1
            if x2 < a:
                a = x2
            elif x2 > b:
                b = x2
            draw_line(a, y1, b, y1)
        else:
            dx01 = x1 - x0
            dy01 = y1 - y0
            dx02 = x2 - x0
            dy02 = y2 - y0
            dx12 = x2 - x1
            dy12 = y2 - y1
            sa = 0
            sb = 0
            if y1 == y2:
                last = y1
            else:
                last = y1 - 1
            for y in range(y0, last + 1):
                a = x0 + sa // dy01
                b = x0 + sb // dy02
                sa += dx01
                sb += dx02
                if a > b:
                    a, b = b, a
                draw_line(a, y, b, y)
            sa = dx12 * (y - y1)
            sb = dx02 * (y - y0)
            for y in range(last + 1, y2 + 1):
                a = x1 + sa // dy12
                b = x0 + sb // dy02
                sa += dx12
                sb += dx02
                if a > b:
                    a, b = b, a
                draw_line(a, y, b, y)


    def draw_circle(self, x0, y0, r, color):
        x0, y0, r = int(x0), int(y0), int(r)  # Ensure all inputs are integers
        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = 0
        y = r

        self.framebuf.pixel(x0, y0 + r, color)
        self.framebuf.pixel(x0, y0 - r, color)
        self.framebuf.pixel(x0 + r, y0, color)
        self.framebuf.pixel(x0 - r, y0, color)

        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x

            # Ensure integer conversion before using pixel function
            self.framebuf.pixel(int(x0 + x), int(y0 + y), color)
            self.framebuf.pixel(int(x0 - x), int(y0 + y), color)
            self.framebuf.pixel(int(x0 + x), int(y0 - y), color)
            self.framebuf.pixel(int(x0 - x), int(y0 - y), color)
            self.framebuf.pixel(int(x0 + y), int(y0 + x), color)
            self.framebuf.pixel(int(x0 - y), int(y0 + x), color)
            self.framebuf.pixel(int(x0 + y), int(y0 - x), color)
            self.framebuf.pixel(int(x0 - y), int(y0 - x), color)




