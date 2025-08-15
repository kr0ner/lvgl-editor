#!/usr/bin/env python3
"""
Test script to verify widget creation
"""

from widgets import create_widget

def test_widget_creation():
    """Test creating various widgets"""
    
    print("Testing widget creation...")
    
    # Test creating different widget types
    widget_types = ['label', 'button', 'image', 'slider', 'switch']
    
    for widget_type in widget_types:
        try:
            widget = create_widget(
                widget_type,
                id=f"test_{widget_type}",
                x=10,
                y=10
            )
            print(f"✓ {widget_type}: {widget.__class__.__name__} created successfully")
            print(f"  - ID: {widget.id}")
            print(f"  - Type: {widget.widget_type}")
            print(f"  - Position: ({widget.x}, {widget.y})")
            
        except Exception as e:
            print(f"✗ {widget_type}: Failed - {e}")
            
    print("\nWidget creation test completed!")

if __name__ == '__main__':
    test_widget_creation()
