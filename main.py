import streamlit as st
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
import pyvista as pv
import numpy as np
from scipy.spatial import ConvexHull
import tempfile
import os

# App title
st.title("STEP File Visualization with Convex Hull")

# File upload
uploaded_file = st.file_uploader("Upload a STEP file", type=["step", "stp"])

if uploaded_file is not None:
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp_file:
            tmp_file.write(uploaded_file.read())
            step_file_path = tmp_file.name

        # Load the STEP file
        st.info("Loading STEP file...")
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(step_file_path)
        if status != 1:
            st.error("Failed to read the STEP file.")
            st.stop()

        step_reader.TransferRoot()
        shape = step_reader.OneShape()

        # Tessellate the shape for surface rendering
        st.info("Tessellating surfaces...")
        BRepMesh_IncrementalMesh(shape, 0.01)  # Set mesh resolution

        # Extract vertices and tessellated surfaces for input geometry
        input_vertices = []
        input_faces = []
        vertex_offset = 0
        explorer = TopExp_Explorer(shape, TopAbs_FACE)

        while explorer.More():
            face = topods.Face(explorer.Current())

            # Create a TopLoc_Location object
            location = TopLoc_Location()

            # Retrieve tessellation for the face
            triangulation = BRep_Tool.Triangulation(face, location)
            if triangulation is not None:
                face_vertices = []
                for i in range(1, triangulation.NbNodes() + 1):
                    pnt = triangulation.Node(i)
                    face_vertices.append((pnt.X(), pnt.Y(), pnt.Z()))
                face_vertices = np.array(face_vertices)

                face_faces = []
                for i in range(1, triangulation.NbTriangles() + 1):
                    tri = triangulation.Triangle(i)
                    face_faces.append([
                        3,
                        vertex_offset + tri.Value(1) - 1,
                        vertex_offset + tri.Value(2) - 1,
                        vertex_offset + tri.Value(3) - 1,
                    ])
                face_faces = np.array(face_faces)

                input_vertices.append(face_vertices)
                input_faces.append(face_faces)
                vertex_offset += len(face_vertices)

            explorer.Next()

        # Combine all vertices and faces
        input_vertices = np.vstack(input_vertices)
        input_faces = np.vstack(input_faces)

        # Render input file geometry
        st.subheader("Interactive Visualization of Input Geometry")
        input_plotter = pv.Plotter(window_size=(800, 600))
        if len(input_vertices) > 0 and len(input_faces) > 0:
            input_mesh = pv.PolyData(input_vertices, input_faces)
            input_plotter.add_mesh(input_mesh, color="lightblue", opacity=0.7, show_edges=True)

        input_html_path = os.path.join(tempfile.gettempdir(), "input_geometry.html")
        input_plotter.export_html(input_html_path)
        input_plotter.close()

        # Embed the input geometry visualization in Streamlit
        with open(input_html_path, "r") as f:
            st.components.v1.html(f.read(), height=600)

        st.success("Input geometry rendered successfully!")

        # Convex Hull Calculation
        st.subheader("Convex Hull Calculation")
        if len(input_vertices) >= 3:  # Convex hull requires at least 3 points
            hull = ConvexHull(input_vertices, qhull_options="Qt Qf QJ")  # Handle planar surfaces with QJ option

            # Remap hull.simplices indices to match hull_points
            hull_indices = {index: i for i, index in enumerate(hull.vertices)}
            hull_faces = []
            for simplex in hull.simplices:
                remapped_simplex = [hull_indices[idx] for idx in simplex]
                hull_faces.append([3] + remapped_simplex)  # Each face has 3 points

            # Extract hull points
            hull_points = input_vertices[hull.vertices]

            # Flatten the faces for PyVista
            hull_faces_flattened = np.hstack(hull_faces)

            # Create PyVista PolyData for the convex hull
            hull_mesh = pv.PolyData(hull_points, hull_faces_flattened)

            # Display Convex Hull Properties
            st.write(f"Convex Hull Volume: {hull.volume:.6f} cubic units")
            st.write(f"Convex Hull Vertices: {len(hull.vertices)}")
            st.write(f"Convex Hull Faces: {len(hull.simplices)}")

            # Render the convex hull
            st.subheader("Interactive Convex Hull Visualization")
            hull_plotter = pv.Plotter(window_size=(800, 600))
            hull_plotter.add_mesh(hull_mesh, color="green", opacity=0.5, show_edges=True)

            # Add convex hull vertices as points
            hull_plotter.add_points(hull_points, color="blue", point_size=12, render_points_as_spheres=True)

            # Export convex hull visualization to HTML
            hull_html_path = os.path.join(tempfile.gettempdir(), "convex_hull.html")
            hull_plotter.export_html(hull_html_path)
            hull_plotter.close()

            # Embed the convex hull visualization in Streamlit
            with open(hull_html_path, "r") as f:
                st.components.v1.html(f.read(), height=600)

            st.success("Convex hull calculated and visualized successfully!")
        else:
            st.warning("Not enough points to calculate a convex hull.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a STEP file to begin.")
