CS661 - Assignment 1
Isocontour and Volume Visualization

=========================================
Part 1: 2D Isocontour Extraction
=========================================

Submitted Files:
- `part1.py` (The Python script containing the entire 2D isocontour extraction algorithm for Part 1)
- `part2.py` (The Python script containing the volume rendering algorithm for Part 2)
- `README.txt` (This documentation file)


Requirements:
- Python 3.x
- VTK Python library (installable via `pip install vtk`)

How to Run:
The script must be run from the command line, passing the target isovalue as a parameter.

Usage:
  python part1.py <isovalue> [--input <path_to_vti>] [--output <path_to_vtp>]

Arguments:
  isovalue              Required float parameter. The isovalue at which to extract the contour.
                        The valid range for this dataset is between -1438 and 630.
  --input               Optional. Custom path to the input VTI file (default: Isabel_2D.vti).
                        The script automatically searches for the file in:
                        1. 'Assignment_1/Data/Isabel_2D.vti'
                        2. 'Data/Isabel_2D.vti'
                        3. Current directory recursively.
  --output              Optional. Custom path to save the output VTP file (default: contour_<isovalue>.vtp).

Examples:
  1. Extract contour for isovalue = 0.0:
     python part1.py 0

  2. Extract contour for isovalue = -1000.0:
     python part1.py -1000

  3. Extract contour for isovalue = 500.0:
     python part1.py 500

Output:
The script prints information about the dataset, dimensions, scalar range, number of processed cells, unique points extracted, and line segments created.
It generates a *.vtp file (e.g. `contour_0.0.vtp`).

How to View the Output Visualization:
=========================================
Using ParaView:
1. Open ParaView.
2. Click File -> Open... and select the generated *.vtp file (e.g. contour_0.0.vtp).
3. Click 'Apply' in the Properties panel.
4. Set representation color to something other than white if you are using a white background in ParaView.


=========================================
Part 2: VTK Volume Rendering and Transfer Function
=========================================

Files:
- `part2.py`: The Python script that performs the volume rendering using ray-casting, applies the specified transfer functions, draws a wireframe outline, and supports optional Phong shading.
- `README.txt`: This documentation file (updated).

Requirements:
- Python 3.x
- VTK Python library (installable via `pip install vtk`)

How to Run:
The script can be run from the command line, optionally passing whether to enable Phong shading.

Usage:
  python part2.py [shading] [--shading <yes/no>] [--phong] [--input <path_to_vti>]

Arguments:
  shading (positional)  Optional. Shading toggle value. Use 'yes' or 'no'.
  --shading             Optional. Shading toggle value. Use 'yes' or 'no'.
  --phong               Optional. Enable Phong shading (flag).
  --input               Optional. Custom path to the input VTI file (default: Isabel_3D.vti).
                        The script automatically searches for the file in:
                        1. 'Assignment_1/Data/Isabel_3D.vti'
                        2. 'Data/Isabel_3D.vti'
                        3. Current directory recursively.

If no arguments are provided, the script will run without Phong shading by default (or prompt interactively if run in an interactive terminal).

Examples:
  1. Render volume without Phong shading (default):
     python part2.py no
     
  2. Render volume with Phong shading:
     python part2.py yes
     
  3. Render volume with Phong shading using flag:
     python part2.py --phong

Output:
The script loads the 3D dataset, configures the specified color and opacity transfer functions, adds a wireframe box around the volume, and pops up a 1000x1000 interactive visualization window.
It prints metadata about the dataset size, range, and shading coefficients to the terminal.

Controls in the window:
- Left-click & drag: Rotate/tilt view
- Right-click & drag / Scroll: Zoom in/out
- Middle-click & drag: Pan
- Press 'q' or close the window to exit.

