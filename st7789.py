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
            self.framebuf.pixel(x0 + x, y0 + y, color)
            self.framebuf.pixel(x0 - x, y0 + y, color)
            self.framebuf.pixel(x0 + x, y0 - y, color)
            self.framebuf.pixel(x0 - x, y0 - y, color)
            self.framebuf.pixel(x0 + y, y0 + x, color)
            self.framebuf.pixel(x0 - y, y0 + x, color)
            self.framebuf.pixel(x0 + y, y0 - x, color)
            self.framebuf.pixel(x0 - y, y0 - x, color)

    def fill_circle(self, x0, y0, r, color):
        self.draw_line(x0, y0 - r, x0, y0 + r, color)
        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = 0
        y = r
        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x
            self.draw_line(x0 + x, y0 - y, x0 + x, y0 + y, color)
            self.draw_line(x0 - x, y0 - y, x0 - x, y0 + y, color)
            self.draw_line(x0 + y, y0 - x, x0 + y, y0 + x, color)
            self.draw_line(x0 - y, y0 - x, x0 - y, y0 + x, color)

    def draw_image(self, x, y, img_data, img_width, img_height):
        for j in range(img_height):
            for i in range(img_width):
                color = img_data[j * img_width + i]
                self.draw_pixel(x + i, y + j, color)

