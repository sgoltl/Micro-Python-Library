import st7789
import framebuf
import time
from machine import Pin, SPI

# intialize LCD 
spi = SPI(1, baudrate=40000000, polarity=1, phase=1)
cs = Pin(9, Pin.OUT)
dc = Pin(13, Pin.OUT)
rst = Pin(12, Pin.OUT)

lcd = st7789.ST7789(spi, cs, dc, rst)
lcd.framebuf.fill(0)

# Example Methods
lcd.framebuf.text('Hello, World!', 50, 50, 0xFFFF)
lcd.draw_pixel(10, 10, 0xFFFF)  # Draw a white pixel
lcd.draw_triangle(60, 60, 100, 100, 60, 140, 0x07E0)  # Draw a green triangle
lcd.fill_rect(10, 10, 50, 30, 0xF800)  # Draw a filled red rectangle
lcd.draw_circle(160, 120, 50, 0x001F)  # Draw a blue circle
lcd.fill_circle(240, 120, 30, 0x07E0)  # Draw a filled green circle
# Example raw image data (2x2 pixels)
image_data = [0xF800, 0x07E0, 0x001F, 0xFFFF]  # Red, Green, Blue, White
lcd.draw_image(200, 50, image_data, 2, 2)  # Draw the image at position (200, 50)
# Example bitmap data (4x4 pixels, RGB565 format)
bitmap_data = bytearray([
    0xF8, 0x00, 0x07, 0xE0, 0x00, 0x1F, 0xFF, 0xFF,  # Red, Green, Blue, White
    0xF8, 0x00, 0x07, 0xE0, 0x00, 0x1F, 0xFF, 0xFF,  # Red, Green, Blue, White
    0xF8, 0x00, 0x07, 0xE0, 0x00, 0x1F, 0xFF, 0xFF,  # Red, Green, Blue, White
    0xF8, 0x00, 0x07, 0xE0, 0x00, 0x1F, 0xFF, 0xFF   # Red, Green, Blue, White
])
lcd.draw_bitmap(10, 150, bitmap_data, 4, 4)  # Draw the bitmap at position (100, 100)
lcd.show()