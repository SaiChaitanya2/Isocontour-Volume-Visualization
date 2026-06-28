#!/usr/bin/env python3
# CS661 Assignment 1 - Part 1: 2D Isocontour Extraction
# Group 48
#   Dwij Sukhadiya (240381)
#   Jiya Agarwal (240498)
#   Boppudi Sai Chaitanya (240283)
#
# Reads the 2D pressure field (Isabel_2D.vti) and, for a given isovalue, pulls
# out the contour line by hand and saves it as a .vtp that opens in ParaView.
# No vtkContourFilter / marching-squares lookup table is used - I just go cell
# by cell, check each edge for a crossing, and join the crossing points up.

import os
import sys
import argparse
import vtk

def find_dataset(filename="Isabel_2D.vti"):
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

def get_intersection_point(p_a, p_b, s_a, s_b, isovalue):
    # find where the isovalue sits on the edge between p_a and p_b and return
    # that point. plain linear interpolation.

    # if both ends are basically the same value there is no real crossing, so
    # bail out with one endpoint instead of dividing by zero
    if abs(s_b - s_a) < 1e-9:
        return (p_a[0], p_a[1], 0.0)

    t = (isovalue - s_a) / (s_b - s_a)

    # P = (1-t)*Pa + t*Pb,  z stays 0 because this is a flat 2D slice
    p_x = (1.0 - t) * p_a[0] + t * p_b[0]
    p_y = (1.0 - t) * p_a[1] + t * p_b[1]
    p_z = 0.0

    return (p_x, p_y, p_z)

def extract_isocontour(image_data, isovalue):
    # the actual contour logic. walk every cell, go round its 4 edges in ccw
    # order starting from the bottom edge, and make line segments wherever the
    # contour crosses an edge.
    dims = image_data.GetDimensions()
    print(f"[Info] Image Grid Dimensions: {dims[0]}x{dims[1]}x{dims[2]}")

    scalars = image_data.GetPointData().GetScalars()
    if not scalars:
        raise ValueError("No scalar data found in the input VTK image data.")

    # printed so I can quickly sanity check the isovalue is inside the range
    scalar_range = scalars.GetRange()
    print(f"[Info] Scalar Data Range: [{scalar_range[0]:.3f}, {scalar_range[1]:.3f}]")
    print(f"[Info] Target Isovalue: {isovalue:.3f}")

    # what we build up and hand back
    points_output = vtk.vtkPoints()
    lines_output = vtk.vtkCellArray()

    # an edge is shared by two cells, so once I make a point for an edge I keep
    # it here and reuse it instead of adding a duplicate. key = (smaller id, bigger id)
    edge_intersections = {}

    # one fewer cell than points along each axis
    num_cells_x = dims[0] - 1
    num_cells_y = dims[1] - 1

    total_cells = num_cells_x * num_cells_y
    processed_cells = 0
    segments_count = 0

    for j in range(num_cells_y):
        for i in range(num_cells_x):
            # corner point ids of this cell in ccw order:
            # v0 bottom-left, v1 bottom-right, v2 top-right, v3 top-left
            pt_id0 = i + j * dims[0]
            pt_id1 = (i + 1) + j * dims[0]
            pt_id2 = (i + 1) + (j + 1) * dims[0]
            pt_id3 = i + (j + 1) * dims[0]

            pt_ids = [pt_id0, pt_id1, pt_id2, pt_id3]

            # their coordinates
            p0 = image_data.GetPoint(pt_id0)
            p1 = image_data.GetPoint(pt_id1)
            p2 = image_data.GetPoint(pt_id2)
            p3 = image_data.GetPoint(pt_id3)

            cell_points = [p0, p1, p2, p3]

            # and their scalar (pressure) values
            s0 = scalars.GetTuple1(pt_id0)
            s1 = scalars.GetTuple1(pt_id1)
            s2 = scalars.GetTuple1(pt_id2)
            s3 = scalars.GetTuple1(pt_id3)

            cell_scalars = [s0, s1, s2, s3]

            # the 4 edges, ccw, bottom one first (this is the order the
            # assignment asks us to walk them in)
            edges = [
                (0, 1),  # bottom
                (1, 2),  # right
                (2, 3),  # top
                (3, 0)   # left
            ]

            # crossing points found on this cell, kept in edge order
            intersection_pt_ids = []

            for edge_idx, (idx_a, idx_b) in enumerate(edges):
                pt_id_a = pt_ids[idx_a]
                pt_id_b = pt_ids[idx_b]

                s_a = cell_scalars[idx_a]
                s_b = cell_scalars[idx_b]

                # does the contour cross this edge? one side uses <= and the
                # other < on purpose, so a value landing exactly on a corner
                # only gets counted once
                if (s_a <= isovalue < s_b) or (s_b <= isovalue < s_a):
                    edge_key = (min(pt_id_a, pt_id_b), max(pt_id_a, pt_id_b))

                    if edge_key in edge_intersections:
                        # the neighbouring cell already made this point, reuse it
                        output_pt_id = edge_intersections[edge_key]
                    else:
                        p_a = cell_points[idx_a]
                        p_b = cell_points[idx_b]
                        p_interp = get_intersection_point(p_a, p_b, s_a, s_b, isovalue)

                        output_pt_id = points_output.InsertNextPoint(p_interp)
                        edge_intersections[edge_key] = output_pt_id

                    intersection_pt_ids.append(output_pt_id)

            # 2 crossings -> one segment joining them.
            # 4 crossings is the ambiguous case which we don't have to resolve,
            # so just pair them up in the order they were found.
            if len(intersection_pt_ids) == 2:
                id_list = vtk.vtkIdList()
                id_list.InsertNextId(intersection_pt_ids[0])
                id_list.InsertNextId(intersection_pt_ids[1])
                lines_output.InsertNextCell(id_list)
                segments_count += 1

            elif len(intersection_pt_ids) == 4:
                # bottom crossing joined to right crossing
                id_list1 = vtk.vtkIdList()
                id_list1.InsertNextId(intersection_pt_ids[0])
                id_list1.InsertNextId(intersection_pt_ids[1])
                lines_output.InsertNextCell(id_list1)

                # top crossing joined to left crossing
                id_list2 = vtk.vtkIdList()
                id_list2.InsertNextId(intersection_pt_ids[2])
                id_list2.InsertNextId(intersection_pt_ids[3])
                lines_output.InsertNextCell(id_list2)
                segments_count += 2

            processed_cells += 1

    print(f"[Info] Processed {processed_cells} cells.")
    print(f"[Info] Extracted {points_output.GetNumberOfPoints()} unique points.")
    print(f"[Info] Created {segments_count} line segments.")

    # bundle the points and lines into a polydata to write out
    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points_output)
    poly_data.SetLines(lines_output)

    return poly_data

def main():
    # command line args: isovalue is required, input/output are optional
    parser = argparse.ArgumentParser(
        description="Extract 2D isocontour from VTKImageData file Isabel_2D.vti."
    )
    parser.add_argument(
        "isovalue",
        type=float,
        help="The isovalue to extract (must be between -1438 and 630)."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="Isabel_2D.vti",
        help="Path to the input VTI file (default: Isabel_2D.vti)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="contour.vtp",
        help="Path to save the output VTP file (default: contour.vtp)"
    )

    args = parser.parse_args()

    # make sure the isovalue is inside the dataset's range before doing any work
    isovalue = args.isovalue
    if not (-1438.0 <= isovalue <= 630.0):
        print(f"[Error] The isovalue {isovalue} is out of the valid range [-1438, 630].")
        sys.exit(1)

    # locate the .vti file
    input_path = find_dataset(args.input)
    if not input_path:
        print(f"[Error] Could not find the input dataset '{args.input}' in default locations or current directory.")
        sys.exit(1)

    print(f"[Info] Reading input data from: {input_path}")

    # load it
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(input_path)
    reader.Update()

    image_data = reader.GetOutput()

    # run our own contour extraction
    print("[*] Starting isocontour extraction...")
    try:
        contour_polydata = extract_isocontour(image_data, isovalue)
    except Exception as e:
        print(f"[Error] Contour extraction failed: {e}")
        sys.exit(1)

    # write the result. if the output was left at the default, tag the isovalue
    # onto the name so separate runs don't overwrite each other
    output_path = args.output
    if output_path == "contour.vtp":
        output_path = f"contour_{isovalue}.vtp"

    print(f"[*] Writing extracted contour to: {output_path}")

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(contour_polydata)
    writer.Write()

    print("[*] Done! Extraction completed successfully.")

if __name__ == "__main__":
    main()
