#!/usr/bin/env python3
"""Fix the broken views.py file."""

# Read the current file
with open(r'MyApp\views.py', 'r') as f:
    lines = f.readlines()

# Fix the last line
if lines and "Ultra-optimized Elo calculation failed" in lines[-1]:
    # Replace the broken line with the correct one
    lines[-1] = "        return JsonResponse({'success': False, 'error': f'Ultra-optimized Elo calculation failed: {str(e)}'})\n"

# Write the fixed file
with open(r'MyApp\views.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed the broken views.py file!")