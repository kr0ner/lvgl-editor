# LVGL Project Summary
# 
# This document provides an overview of your LVGL project
# and the widgets/pages it contains.

## Display Configuration
- Size: 320x240 pixels
- Color Depth: 16 bits
- Buffer Size: 100%

## Pages (2)
- **main_page**: 5 widgets
- **settings_page**: 6 widgets

## Widget Details

### Page: main_page

1. **Label** (`title_label`)
   - Position: (10, 10)
   - Size: 300 x 30
   - Text: "LVGL Demo"

2. **Button** (`start_btn`)
   - Position: (50, 60)
   - Size: 100 x 40
   - Actions: on_click

3. **Button** (`settings_btn`)
   - Position: (170, 60)
   - Size: 100 x 40
   - Actions: on_click

4. **Slider** (`volume_slider`)
   - Position: (50, 120)
   - Size: 220 x 20
   - Value: 50 (range: 0-100)
   - Actions: on_value_changed

5. **Label** (`volume_label`)
   - Position: (50, 100)
   - Size: 220 x 20
   - Text: "Volume: 50%"

### Page: settings_page

1. **Label** (`settings_title`)
   - Position: (10, 10)
   - Size: 300 x 30
   - Text: "Settings"

2. **Switch** (`wifi_switch`)
   - Position: (50, 60)
   - Size: 60 x 30

3. **Label** (`wifi_label`)
   - Position: (120, 65)
   - Size: 100 x 20
   - Text: "Wi-Fi"

4. **Switch** (`bluetooth_switch`)
   - Position: (50, 100)
   - Size: 60 x 30

5. **Label** (`bluetooth_label`)
   - Position: (120, 105)
   - Size: 100 x 20
   - Text: "Bluetooth"

6. **Button** (`back_btn`)
   - Position: (50, 180)
   - Size: 80 x 30
   - Actions: on_click

## Statistics

- Total Widgets: 11
- Widget Types Used: 4

### Widget Type Breakdown:
- Button: 3
- Label: 5
- Slider: 1
- Switch: 2
