import cadquery as cq
import pyvista as pv
import streamlit as st
import numpy as np
from scipy.spatial import ConvexHull
import tempfile
import os

# App title
st.title("STEP File Visualization and Convex Hull Calculation")

# File upload
uploaded_file = st.file_uploader("Upload a STEP file", type=["step", "stp"])

if uploaded_file is not None:
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp_file:
            tmp_file.write(uploaded_file.read())
            step_file_path = tmp_file.name

        # Load STEP file with cadquery
        st.info("Loading STEP file...")
        compound = cq.importers.importStep(step_file_path)

        # Debugging: Show the structure of the file
        solids_count = len(list(compound.solids()))
        faces_count = len(list(compound.faces()))
        edges_count = len(list(compound.edges()))
        vertices_count = len(list(compound.vertices()))

        st.write("### File Structure:")
        st.write(f"- Number of Solids: {solids_count}")
        st.write(f"- Number of Faces: {faces_count}")
        st.write(f"- Number of Edges: {edges_count}")
        st.write(f"- Number of Vertices: {vertices_count}")

        # Initialize PyVista PolyData for faces, edges, and vertices
        faces_mesh = pv.PolyData()
        edges_mesh = pv.PolyData()
        vertices = []

        # Tessellation tolerance
        tolerance = 1e-3

        # Extract faces
        for face in compound.faces():
            tessellation = face.tessellate(tolerance)  # Generate triangles with the given tolerance
            face_points = np.array([v.toTuple() for v in tessellation[0]])  # Extract points
            face_indices = tessellation[1]  # Extract face indices
            vertices.extend(face_points)

            # Create a PolyData object for the face
            faces = [[len(triangle)] + list(triangle) for triangle in face_indices]
            face_polydata = pv.PolyData(face_points, np.hstack(faces))
            faces_mesh = faces_mesh + face_polydata

        # Extract edges
        for edge in compound.edges():
            edge_points = [v.toTuple() for v in edge.vertices()]
            if len(edge_points) > 1:  # Ensure valid edge
                edge_polydata = pv.PolyData(np.array(edge_points))
                edges_mesh = edges_mesh + edge_polydata

        # Render Faces and Edges
        st.subheader("Interactive Visualization of Faces and Edges")
        plotter = pv.Plotter(window_size=(800, 600))
        if faces_mesh.n_points > 0:
            plotter.add_mesh(faces_mesh, color="lightblue", opacity=0.7, show_edges=True, edge_color="black")
        if edges_mesh.n_points > 0:
            plotter.add_mesh(edges_mesh, color="gray", line_width=2)

        # Export visualization to HTML
        html_path = os.path.join(tempfile.gettempdir(), "visualization.html")
        plotter.export_html(html_path)
        plotter.close()

        # Embed the HTML in Streamlit
        with open(html_path, "r") as f:
            st.components.v1.html(f.read(), height=600)

        st.success("Faces and edges rendered correctly!")

        # Convex Hull Calculation
        st.subheader("Convex Hull Calculation")
        vertices = np.array(vertices)
        if len(vertices) >= 3:  # Convex hull requires at least 3 points
            hull = ConvexHull(vertices)
            hull_points = vertices[hull.vertices]

            # Construct faces for pyvista using hull.simplices
            hull_faces = []
            for simplex in hull.simplices:
                hull_faces.append([3] + list(simplex))  # Each face has 3 points (triangle)

            # Flatten the faces for PyVista
            hull_faces_flattened = np.hstack(hull_faces)

            # Create PyVista PolyData for the convex hull
            hull_mesh = pv.PolyData(vertices, hull_faces_flattened)
            st.write(f"Convex Hull Vertices: {len(hull.vertices)}")
            st.write(f"Convex Hull Faces: {len(hull.simplices)}")
            st.write(f"Convex Hull Volume: {hull.volume:.6f} cubic units")


            # Render Convex Hull
            st.subheader("Interactive Convex Hull Visualization")
            hull_plotter = pv.Plotter(window_size=(800, 600))
            hull_plotter.add_mesh(hull_mesh, color="green", opacity=0.5, show_edges=True)

            # Add convex hull vertices as points
            hull_plotter.add_points(hull_points, color="red", point_size=10, render_points_as_spheres=True)

            # Export convex hull visualization to HTML
            hull_html_path = os.path.join(tempfile.gettempdir(), "convex_hull.html")
            hull_plotter.export_html(hull_html_path)
            hull_plotter.close()

            # Embed Convex Hull in Streamlit
            with open(hull_html_path, "r") as f:
                st.components.v1.html(f.read(), height=600)

            st.success("Convex hull calculated and visualized successfully!")
        else:
            st.warning("Not enough points to calculate a convex hull.")


    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a STEP file to begin.")
