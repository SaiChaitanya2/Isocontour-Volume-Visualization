#!/usr/bin/env python3
# CS661 Assignment 1 - Part 2
# Group 48
#   Dwij Sukhadiya (240381)
#   Jiya Agarwal (240498)
#   Boppudi Sai Chaitanya (240283)
#
# Loads the 3D pressure volume (Isabel_3D.vti), sets up the colour and opacity
# transfer functions from the assignment tables, and renders it with
# vtkSmartVolumeMapper. Draws an outline box around the volume and can switch
# on Phong shading if the user asks for it.

import os
import sys
import argparse
import vtk

def find_dataset(filename="Isabel_3D.vti"):
    # check the usual spots first, and if it's not there just search the whole
    # folder and take the first match
    search_paths = [
        os.path.join("Assignment_1", "Data", filename),
        os.path.join("Data", filename),
        filename
    ]

    for path in search_paths:
        if os.path.exists(path):
            return path

    print(f"[*] Searching recursively for '{filename}' in the current directory...")
    for root, dirs, files in os.walk("."):
        if filename in files:
            found_path = os.path.join(root, filename)
            return found_path

    return None

def main():
    # the shading choice can come in as a positional arg, the --shading option,
    # or the --phong flag - whichever is used ends up setting use_shading below
    parser = argparse.ArgumentParser(
        description="VTK Volume Rendering with transfer functions and optional Phong shading."
    )
    parser.add_argument(
        "shading_pos",
        nargs="?",
        choices=["yes", "no", "1", "0", "true", "false"],
        help="Optional positional argument to specify shading ('yes' or 'no')."
    )
    parser.add_argument(
        "--shading",
        choices=["yes", "no"],
        help="Specify shading ('yes' or 'no')."
    )
    parser.add_argument(
        "--phong",
        action="store_true",
        help="Enable Phong shading."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="Isabel_3D.vti",
        help="Path to the input VTI file (default: Isabel_3D.vti)"
    )

    args = parser.parse_args()

    # figure out if shading should be on from whichever argument was given
    use_shading = False
    if args.phong:
        use_shading = True
    elif args.shading is not None:
        use_shading = (args.shading == "yes")
    elif args.shading_pos is not None:
        use_shading = (args.shading_pos in ["yes", "1", "true"])
    else:
        # nothing was passed, so ask only if we're actually in a terminal
        if sys.stdin.isatty():
            try:
                user_val = input("Do you want to use Phong shading? (yes/no) [no]: ").strip().lower()
                if user_val in ["yes", "y", "1", "true"]:
                    use_shading = True
            except (KeyboardInterrupt, EOFError):
                pass

    # find and read the .vti volume
    input_path = find_dataset(args.input)
    if not input_path:
        print(f"[Error] Could not find the input dataset '{args.input}' in default locations or current directory.")
        sys.exit(1)

    print(f"[*] Reading input data from: {input_path}")

    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(input_path)
    reader.Update()

    image_data = reader.GetOutput()
    dims = image_data.GetDimensions()
    scalar_range = image_data.GetPointData().GetScalars().GetRange()

    # print a bit of info about what got loaded
    print(f"[Info] Volume Grid Dimensions: {dims[0]}x{dims[1]}x{dims[2]}")
    print(f"[Info] Scalar Data Range: [{scalar_range[0]:.3f}, {scalar_range[1]:.3f}]")
    print(f"[Info] Phong Shading Status: {'ENABLED' if use_shading else 'DISABLED'}")

    # colour transfer function - these are the (value, r, g, b) rows from the table
    color_tf = vtk.vtkColorTransferFunction()
    color_tf.AddRGBPoint(-4931.54, 0.0, 1.0, 1.0)
    color_tf.AddRGBPoint(-2508.95, 0.0, 0.0, 1.0)
    color_tf.AddRGBPoint(-1873.90, 0.0, 0.0, 0.5)
    color_tf.AddRGBPoint(-1027.16, 1.0, 0.0, 0.0)
    color_tf.AddRGBPoint(-298.031, 1.0, 0.4, 0.0)
    color_tf.AddRGBPoint(2594.97, 1.0, 1.0, 0.0)

    # opacity transfer function - the (value, opacity) rows from the table.
    # a vtkPiecewiseFunction is what the assignment wants us to use here.
    opacity_tf = vtk.vtkPiecewiseFunction()
    opacity_tf.AddPoint(-4931.54, 1.0)
    opacity_tf.AddPoint(101.815, 0.002)
    opacity_tf.AddPoint(2594.97, 0.0)

    # hook both functions onto the volume property
    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_tf)
    volume_property.SetScalarOpacity(opacity_tf)

    # linear interpolation gives a smoother result than nearest neighbour
    volume_property.SetInterpolationTypeToLinear()

    # if shading is on, switch it on with the coefficients from the assignment;
    # otherwise leave it off (which is the default)
    if use_shading:
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.5)
        volume_property.SetDiffuse(0.5)
        volume_property.SetSpecular(0.5)
        print("[Info] Applied Shading Parameters: Ambient=0.5, Diffuse=0.5, Specular=0.5")
    else:
        volume_property.ShadeOff()
        print("[Info] Phong Shading is turned OFF.")

    # the smart mapper picks a suitable ray-cast path for us
    volume_mapper = vtk.vtkSmartVolumeMapper()
    volume_mapper.SetInputConnection(reader.GetOutputPort())

    volume = vtk.vtkVolume()
    volume.SetMapper(volume_mapper)
    volume.SetProperty(volume_property)

    # outline box around the volume so its extent is visible
    outline_filter = vtk.vtkOutlineFilter()
    outline_filter.SetInputConnection(reader.GetOutputPort())

    outline_mapper = vtk.vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline_filter.GetOutputPort())

    outline_actor = vtk.vtkActor()
    outline_actor.SetMapper(outline_mapper)
    outline_actor.GetProperty().SetColor(0.2, 0.2, 0.2)  # dark grey, shows up on a light background
    outline_actor.GetProperty().SetLineWidth(1.5)

    # renderer and window
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.95, 0.95, 0.95)  # near-white background

    renderer.AddVolume(volume)
    renderer.AddActor(outline_actor)

    # assignment asks for a 1000x1000 window
    render_window = vtk.vtkRenderWindow()
    render_window.SetSize(1000, 1000)
    render_window.AddRenderer(renderer)
    render_window.SetWindowName("VTK Volume Rendering - CS661 Assignment 1 Part 2")

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    # frame the volume in the camera before showing it
    renderer.ResetCamera()

    print("[*] Starting interactive visualization window (1000x1000)...")
    print("    - Left-click & drag: Rotate volume")
    print("    - Right-click & drag / Scroll wheel: Zoom")
    print("    - Middle-click & drag: Pan")
    print("    - Press 'q' to close the window and exit.")

    render_window.Render()
    interactor.Initialize()
    interactor.Start()
    print("[*] Visualization window closed.")

if __name__ == "__main__":
    main()
