#!/usr/bin/env python3

"""
This program reminds you to relax after working for a certain period.
"""

"""
https://github.com/shuangye/relax_eyes
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import webbrowser
from datetime import datetime
from tkinter import *
from PIL import Image, ImageDraw, ImageTk
import pystray
import threading

g_root                          = None
g_windows                       = []        # List to store all monitor windows
g_tray_icon                     = None      # System tray icon
g_primary_app                   = None      # Primary application instance
g_minimize_to_tray_enabled      = False     # Whether user wants to use system tray
g_workDuration                  = 30 * 60   # in seconds; change as needed
g_relaxDuration                 = 5 * 60    # in seconds; change as needed
g_notifyDurationBeforeRelax     = 2         # in seconds; change as needed
g_minimizeDelay                 = 3         # in seconds; change as needed
gc_FONT                         = 'Arial'
gc_DEFAULT_BG_COLOR             = '#DDDDDD'
gc_DEFAULT_FG_COLOR             = 'black'
gc_NOTIFY_FG_COLOR              = 'green'
gc_RELAX_FG_COLOR               = gc_DEFAULT_BG_COLOR
gc_RELAX_BG_COLOR               = gc_DEFAULT_FG_COLOR
gc_TIMER_RESOLUTION             = 1         # in seconds
gc_REPO_URL                     = 'https://github.com/shuangye/have-a-rest'
gc_MODE_RELAX                   = 0
gc_MODE_WORK                    = 1

class Application(Frame):
    def __init__(self, master = None, is_primary = True):
        Frame.__init__(self, master)
        self.master = master
        self.is_primary = is_primary
        self.lapsed = 0
        self.remaining = 0
        self.mode = gc_MODE_WORK
        self.countdownText = StringVar()
        self.currentTime = StringVar()
        self.pack(expand = True, fill = 'both')
        self.place(in_ = master, anchor = CENTER, relx = .5, rely = .5)
        self.createWidgets()
        if self.is_primary:
            self.timeMeas()

    def createWidgets(self):
        self.statusLabel = Label(self, font = (gc_FONT, 60), pady = 20)
        self.statusLabel.pack()
        self.countdownLabel = Label(self, font = (gc_FONT, 200), textvariable = self.countdownText, pady = 30)
        self.countdownLabel.pack()
        self.currentTimeLabel = Label(self, font = (gc_FONT, 70), textvariable = self.currentTime, pady = 30)
        self.currentTimeLabel.pack()
        self.bottomFrame = Frame(master = self.master)
        self.bottomFrame.pack(expand = True, fill = X, anchor = S, side = BOTTOM)
        self.actionButton = Button(self.bottomFrame, font = (gc_FONT, 20), command = lambda: self.switchMode(gc_MODE_RELAX),
                                   bd=0, highlightthickness=0, pady=10, padx=10)
        self.actionButton.pack(side = RIGHT, anchor = SE)
        self.minimizeButton = Button(self.bottomFrame, font = (gc_FONT, 20), text = 'Minimize to Tray', command = enable_and_hide_to_tray,
                                     bd=0, highlightthickness=0, pady=10, padx=10)
        self.minimizeButton.pack(side = RIGHT, anchor = SE, padx = 10)
        self.linkLabel = Label(self.bottomFrame, font = (gc_FONT, 12), text = gc_REPO_URL, cursor="hand2")
        self.linkLabel.pack(side = LEFT, anchor = SW)
        self.linkLabel.bind("<Button-1>", lambda e: webbrowser.open_new(gc_REPO_URL))
        self.configureUI()

    def timeMeas(self):
        if (self.mode == gc_MODE_RELAX):
            self.remaining = g_relaxDuration - self.lapsed
            if self.remaining == 0: self.switchMode(gc_MODE_WORK)
        elif (self.mode == gc_MODE_WORK):
            # If tray is enabled and we're in the minimize countdown period
            if g_minimize_to_tray_enabled and self.lapsed < g_minimizeDelay:
                countdown = g_minimizeDelay - self.lapsed
                # Update all windows with minimize countdown message
                for win in g_windows:
                    try:
                        app = win.nametowidget('!application')
                        app.statusLabel.configure(text = f"Minimizing to System Tray in {countdown}s...")
                    except:
                        pass
            elif g_minimize_to_tray_enabled and self.lapsed == g_minimizeDelay:
                # Time to hide to tray
                hide_windows()
            elif g_minimize_to_tray_enabled and self.lapsed == g_minimizeDelay + 1:
                # Restore normal status label after hiding
                for win in g_windows:
                    try:
                        app = win.nametowidget('!application')
                        app.statusLabel.configure(text = 'Time To Rest')
                    except:
                        pass

            self.remaining = g_workDuration - self.lapsed
            if self.remaining == 0: self.switchMode(gc_MODE_RELAX)
            elif self.remaining == g_notifyDurationBeforeRelax:
                self.updateAllWindows('notify')
                self.bringUpWindow(True)
        self.updateAllWindows('time')
        self.lapsed += gc_TIMER_RESOLUTION
        self.after(gc_TIMER_RESOLUTION * 1000, self.timeMeas)

    def bringUpWindow(self, temporary):
        for win in g_windows:
            win.update()
            win.deiconify()
            win.lift()
            win.focus_force()
            win.attributes('-topmost', True)
            if temporary:
                win.update()
                win.attributes('-topmost', False)

    def configureUI(self):
        if self.mode == gc_MODE_RELAX: bgColor = gc_RELAX_BG_COLOR; fgColor = gc_RELAX_FG_COLOR; statusLebel = 'Time To Work';
        else: bgColor = gc_DEFAULT_BG_COLOR; fgColor = gc_DEFAULT_FG_COLOR; statusLebel = 'Time To Rest';
        self.master.configure(bg = bgColor)
        self.configure(bg = bgColor)
        self.bottomFrame.configure(bg = bgColor)
        self.statusLabel.configure(bg = bgColor, fg = fgColor, text = statusLebel)
        self.countdownLabel.configure(bg = bgColor, fg = fgColor)
        self.currentTimeLabel.configure(bg = bgColor, fg = fgColor)
        self.linkLabel.configure(bg = bgColor, fg = fgColor)
        self.minimizeButton.configure(bg = bgColor, fg = fgColor)
        if self.mode == gc_MODE_RELAX:
            self.actionButton.configure(bg = bgColor, fg = fgColor, text = 'Work Now', command = lambda: self.switchMode(gc_MODE_WORK))
            toggleFullscreen(True)
            self.bringUpWindow(False)
        else:
            self.actionButton.configure(bg = bgColor, fg = fgColor, text = 'Rest Now', command = lambda: self.switchMode(gc_MODE_RELAX))
            toggleFullscreen(False)
            self.bringUpWindow(True)

    def updateUI(self):
        self.countdownText.set("{0:02}:{1:02}".format(self.remaining // 60, self.remaining % 60))
        self.currentTime.set(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

    def updateAllWindows(self, update_type):
        """Update all windows: 'time' for countdown/time, 'notify' for notification color"""
        for win in g_windows:
            try:
                app = win.nametowidget('!application')
                if update_type == 'time':
                    app.remaining = self.remaining
                    app.updateUI()
                elif update_type == 'notify':
                    app.statusLabel.configure(fg = gc_NOTIFY_FG_COLOR)
                    app.currentTimeLabel.configure(fg = gc_NOTIFY_FG_COLOR)
                    app.countdownLabel.configure(fg = gc_NOTIFY_FG_COLOR)
            except:
                pass

    def switchMode(self, mode):
        self.mode = mode
        self.remaining = g_workDuration if self.mode == gc_MODE_WORK else g_relaxDuration
        self.lapsed = 0
        # Update all windows to sync mode
        for win in g_windows:
            try:
                app = win.nametowidget('!application')
                app.mode = mode
                app.remaining = self.remaining
                app.lapsed = 0
                app.configureUI()
                app.updateUI()
            except:
                pass

def maximizeWindow(win):
    import platform
    system = platform.system()
    if system == 'Linux':
        win.attributes('-zoomed', True)
    else:
        win.state('zoomed')


def toggleFullscreen(full):
    for win in g_windows:
        win.attributes('-fullscreen', full)

def draw_eye_icon(draw, scale=1.0, offset_x=0, offset_y=0):
    """Draw an eye icon on the given draw object
    Args:
        draw: PIL ImageDraw object
        scale: Scale factor for the eye size (default 1.0)
        offset_x, offset_y: Position offset for the eye
    """
    # Base coordinates
    outer_left = 10
    outer_top = 20
    outer_right = 54
    outer_bottom = 44

    inner_left = 20
    inner_top = 24
    inner_right = 44
    inner_bottom = 40

    pupil_left = 28
    pupil_top = 28
    pupil_right = 36
    pupil_bottom = 36

    # Apply scale and offset
    def transform(x, y):
        center_x = 32  # Center of 64x64 image
        center_y = 32
        x_scaled = center_x + (x - center_x) * scale + offset_x
        y_scaled = center_y + (y - center_y) * scale + offset_y
        return x_scaled, y_scaled

    ol, ot = transform(outer_left, outer_top)
    oright, ob = transform(outer_right, outer_bottom)
    il, it = transform(inner_left, inner_top)
    iright, ib = transform(inner_right, inner_bottom)
    pl, pt = transform(pupil_left, pupil_top)
    pright, pb = transform(pupil_right, pupil_bottom)

    # Draw eye components
    draw.ellipse([ol, ot, oright, ob], fill='black', outline='black')
    draw.ellipse([il, it, iright, ib], fill='white', outline='white')
    draw.ellipse([pl, pt, pright, pb], fill='black', outline='black')

def create_tray_icon():
    """Create a simple icon for system tray with transparent background"""
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # Transparent background
    draw = ImageDraw.Draw(image)
    draw_eye_icon(draw, scale=1.25)
    return image

# Create taskbar icon with window number overlay
def create_taskbar_icon(window_id):
    width = 64
    height = width
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw_eye_icon(draw, scale=1.4)

    # Add screen number at 1/4 bottom-right corner
    circle_radius = width // 4
    circle_x = width - circle_radius
    circle_y = circle_x
    draw.ellipse([circle_x - circle_radius, circle_y - circle_radius,
                  circle_x + circle_radius, circle_y + circle_radius],
                 fill=gc_DEFAULT_BG_COLOR, width=2)

    # Draw the window number
    text = str(window_id)
    try:
        from PIL import ImageFont
        font = ImageFont.load_default(20)
        if font:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = circle_x - text_width // 2
            text_y = circle_y - text_height // 2 - 2
            draw.text((text_x, text_y), text, fill='black', font=font)
    except Exception as e:
        # Fallback if font doesn't work
        print(f"  Warning: Could not render text with font: {e}")
        draw.text((circle_x - 5, circle_y - 8), text, fill='black')

    return image

def show_windows():
    for win in g_windows:
        win.deiconify()
        win.lift()

def hide_windows():
    """Hide all windows to tray"""
    for win in g_windows:
        win.withdraw()

def enable_and_hide_to_tray():
    """Enable tray mode and hide windows"""
    global g_minimize_to_tray_enabled
    g_minimize_to_tray_enabled = True
    hide_windows()

def on_tray_rest_now():
    """Trigger relax mode from tray"""
    if g_primary_app:
        g_root.after(0, lambda: g_primary_app.switchMode(gc_MODE_RELAX))

def on_tray_quit():
    if g_tray_icon:
        g_tray_icon.stop()
    g_root.quit()

def setup_tray_icon():
    """Setup system tray icon"""
    global g_tray_icon

    menu = pystray.Menu(
        pystray.MenuItem('Show', show_windows),
        pystray.MenuItem('Hide', hide_windows),
        pystray.MenuItem('Rest Now', on_tray_rest_now),
        pystray.MenuItem('Quit', on_tray_quit)
    )

    # Left click shows windows, right click shows menu
    g_tray_icon = pystray.Icon(
        'have_a_rest',
        create_tray_icon(),
        'Have A Rest',
        menu,
        on_click=lambda icon, item: show_windows()
    )
    # Run tray icon in a separate thread
    tray_thread = threading.Thread(target=g_tray_icon.run, daemon=True)
    tray_thread.start()

# Returns list of (x, y, width, height) tuples
def get_monitor_geometry():
    monitors = []

    # Try screeninfo library (cross-platform)
    try:
        from screeninfo import get_monitors
        for monitor in get_monitors():
            monitors.append((monitor.x, monitor.y, monitor.width, monitor.height))
            print(f"Detected monitor: {monitor.width}x{monitor.height} at position ({monitor.x}, {monitor.y})")
        if monitors:
            return monitors
    except ImportError:
        print("Install 'screeninfo' package for better multi-monitor support: pip install screeninfo")
    except Exception as e:
        print(f"screeninfo error: {e}")

    # Fallback to tkinter (single monitor)
    try:
        root_temp = Tk()
        root_temp.withdraw()
        width = root_temp.winfo_screenwidth()
        height = root_temp.winfo_screenheight()
        root_temp.destroy()
        monitors.append((0, 0, width, height))
        print(f"Using fallback: {width}x{height} (single monitor)")
    except Exception as e:
        print(f"Fallback error: {e}")

    return monitors

def main():
    global g_root, g_windows, g_primary_app

    monitors = get_monitor_geometry()

    # Create window for each monitor
    for i, (x, y, width, height) in enumerate(monitors):
        if i == 0:
            # First monitor: use root window
            win = Tk()
            g_root = win
            is_primary = True
        else:
            # Additional monitors: use Toplevel
            win = Toplevel(g_root)
            win.wm_group(g_root)
            is_primary = False

        win.title(f'Have A Rest - Screen {i+1}')
        win.resizable(True, True)

        # Position window on specific monitor
        win_width = width // 3 * 2
        win_height = height // 3 * 2
        win_x = x + (width - win_width) // 2
        win_y = y + (height - win_height) // 2
        win.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")

        try:
            icon_image = create_taskbar_icon(i + 1)
            icon_photo = ImageTk.PhotoImage(icon_image)     # Convert PIL Image to PhotoImage for Tkinter
            win.iconphoto(True, icon_photo)
            win._icon_photo = icon_photo                    # Keep a reference to prevent garbage collection
        except Exception as e:
            print(f"  Warning: Could not set window icon: {e}")

        maximizeWindow(win)
        win.configure(bg = gc_DEFAULT_BG_COLOR)
        g_windows.append(win)

        app = Application(master = win, is_primary = is_primary)
        if is_primary:
            g_primary_app = app

    setup_tray_icon()
    g_root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) >= 3:  # specify duration in minutes
        g_workDuration = int(sys.argv[1]) * 60
        g_relaxDuration = int(sys.argv[2]) * 60
    main()
