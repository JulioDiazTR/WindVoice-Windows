#!/usr/bin/env python3
"""
Test script for the CORRECT transparent status dialogs
Tests the SimpleVisibleStatus that the app actually uses
"""

import sys
import os
import time
import threading

# Add src to path to import WindVoice modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from windvoice.ui.simple_visible_status import SimpleVisibleStatusManager, StatusType
    print("✅ Successfully imported SimpleVisibleStatusManager (the correct one!)")
except ImportError as e:
    print(f"❌ Failed to import SimpleVisibleStatusManager: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_transparent_status_dialogs():
    """Test the actual transparent status dialogs used by the app"""
    print("🧪 Testing ACTUAL Transparent Status Dialogs")
    print("=" * 60)
    print("📍 These should appear near your cursor with HIGH transparency!")
    print("🎨 They should have a modern glassmorphism design")
    print("🖱️ You can DRAG them around and they have hover effects")
    print("🖥️ Should work on multi-monitor setups")
    print("👻 50% transparency - SUPER see-through!")
    print("📌 Position persistence - stays where you drag it!")
    print()
    
    # Create manager
    manager = SimpleVisibleStatusManager()
    
    def test_sequence():
        """Run through all status types"""
        
        print("1️⃣ Testing RECORDING status...")
        print("   → Should show SUPER transparent red dialog near cursor")
        print("   → Try DRAGGING it to a different position!")
        manager.show_recording()
        time.sleep(5)  # Give more time to drag it
        
        print("\n2️⃣ Testing PROCESSING status...")
        print("   → Should show transparent blue dialog at SAME position you dragged to")
        print("   → This tests position persistence!")
        manager.show_processing() 
        time.sleep(4)
        
        print("\n3️⃣ Testing SUCCESS status...")
        print("   → Should show transparent green dialog near cursor")
        manager.show_success()
        time.sleep(3)  # This one auto-hides after 2 seconds
        
        print("\n4️⃣ Testing ERROR status...")
        print("   → Should show transparent orange dialog near cursor")
        manager.show_error()
        time.sleep(4)  # This one auto-hides after 3 seconds
        
        print("\n✅ Test sequence completed!")
        print("🎉 All dialogs should have been transparent and appeared near cursor")
    
    # Run test in separate thread to avoid blocking
    test_thread = threading.Thread(target=test_sequence)
    test_thread.daemon = True
    test_thread.start()
    
    # Keep main thread alive
    test_thread.join()
    
    # Final cleanup
    manager.hide()

def test_cursor_positioning():
    """Test that dialogs appear near cursor in different positions"""
    print("\n🎯 Testing Cursor-Aware Positioning")
    print("=" * 50)
    print("📍 Move your cursor to different areas and press Enter")
    print("   → Dialogs should appear near cursor position")
    print("   → Try different monitors if you have multiple")
    print("⏭️ Press Enter to test, 'q' to quit")
    
    manager = SimpleVisibleStatusManager()
    
    while True:
        try:
            user_input = input("\n🎯 Press Enter to show dialog (or 'q' to quit): ")
            if user_input.lower().strip() == 'q':
                break
                
            print("📍 Showing transparent dialog near cursor...")
            manager.show_recording()
            time.sleep(2)
            manager.hide()
            
        except KeyboardInterrupt:
            break
    
    print("🧹 Cleaning up...")
    manager.hide()

def test_visual_design():
    """Test all the visual design improvements"""
    print("\n🎨 Testing Visual Design Improvements")
    print("=" * 50)
    print("🔍 Look for these improvements:")
    print("   • 50% transparency (SUPER see-through!)")
    print("   • Modern glassmorphism effect")
    print("   • No window decorations (clean look)")
    print("   • Shadow text effects")
    print("   • Subtle glow borders")
    print("   • Compact size (160x80)")
    print("   • DRAGGABLE - click and drag to move!")
    print("   • Hover effects - becomes more visible on hover")
    
    manager = SimpleVisibleStatusManager()
    
    statuses = [
        (StatusType.RECORDING, "🎤 Red Recording", 3),
        (StatusType.PROCESSING, "⚡ Blue Processing", 3), 
        (StatusType.SUCCESS, "✅ Green Success", 3),
        (StatusType.ERROR, "❌ Orange Error", 3)
    ]
    
    for status_type, description, duration in statuses:
        print(f"\n🎨 Showing {description} dialog...")
        print("   → Check transparency and modern design!")
        
        if status_type == StatusType.RECORDING:
            manager.show_recording()
        elif status_type == StatusType.PROCESSING:
            manager.show_processing()
        elif status_type == StatusType.SUCCESS:
            manager.show_success()
        elif status_type == StatusType.ERROR:
            manager.show_error()
            
        time.sleep(duration)
    
    manager.hide()
    print("\n✨ Visual design test completed!")

def test_position_persistence():
    """Test that position is maintained when changing states"""
    print("\n📌 Testing Position Persistence")
    print("=" * 50)
    print("🎯 This test checks that dialogs stay where you drag them")
    print("📝 Instructions:")
    print("   1. A RECORDING dialog will appear")
    print("   2. DRAG it to a different location")
    print("   3. Wait for it to change to PROCESSING")
    print("   4. Check if it stayed in the same position!")
    print()
    
    manager = SimpleVisibleStatusManager()
    
    print("▶️ Step 1: Showing RECORDING dialog...")
    print("   🖱️ DRAG this dialog to where you want it!")
    manager.show_recording()
    
    # Give user time to drag
    for i in range(5, 0, -1):
        print(f"   ⏳ {i} seconds to drag the dialog...")
        time.sleep(1)
    
    print("\n▶️ Step 2: Changing to PROCESSING...")
    print("   📍 Dialog should stay at the position you dragged to!")
    manager.show_processing()
    time.sleep(3)
    
    print("\n▶️ Step 3: Changing to SUCCESS...")
    print("   📍 Should still be at your custom position!")
    manager.show_success()
    time.sleep(3)
    
    print("\n▶️ Step 4: Changing to ERROR...")
    print("   📍 Should still be at your custom position!")
    manager.show_error()
    time.sleep(3)
    
    manager.hide()
    print("\n✅ Position persistence test completed!")
    print("🎉 Dialog should have stayed where you dragged it through all state changes!")

if __name__ == "__main__":
    print("🚀 WindVoice ACTUAL Status Dialog Test Suite")
    print("=" * 60)
    print("🎯 Testing SimpleVisibleStatus (the one the app really uses)")
    print()
    
    # Main test
    test_transparent_status_dialogs()
    
    # Additional tests
    while True:
        print("\n" + "="*50)
        print("Choose additional test:")
        print("1️⃣  Test cursor positioning")
        print("2️⃣  Test visual design details")
        print("3️⃣  Test position persistence (IMPORTANT!)")
        print("4️⃣  Exit")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                test_cursor_positioning()
            elif choice == "2":
                test_visual_design()
            elif choice == "3":
                test_position_persistence()
            elif choice == "4":
                break
            else:
                print("❌ Invalid option, try again")
                
        except KeyboardInterrupt:
            break
    
    print("\n✨ All tests completed! Thank you for testing.")
    print("🎉 Your status dialogs should now be transparent and beautiful!")