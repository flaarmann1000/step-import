import streamlit as st
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.TCollection import TCollection_AsciiString
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCC.Core.TDF import TDF_LabelSequence
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDocStd import TDocStd_Document
import matplotlib.pyplot as plt
import colorsys

import pyvista as pv
import numpy as np
from scipy.spatial import ConvexHull
import tempfile
import os

# App title
st.title("STEP File Visualization with Convex Hull and Layers")

# File upload
uploaded_file = st.file_uploader("Upload a STEP file", type=["step", "stp"])

if uploaded_file is not None:
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp_file:
            tmp_file.write(uploaded_file.read())
            step_file_path = tmp_file.name
        
        st.info(f"Temporary file saved at: {step_file_path}")

        # Initialize document and reader
        doc = TDocStd_Document("pythonocc-doc")
        step_reader = STEPCAFControl_Reader()
        
        # Read and transfer
        status = step_reader.ReadFile(step_file_path)
        if status != 1:
            st.error(f"Failed to read the STEP file. Status: {status}")
            st.stop()
            
        step_reader.Transfer(doc)

        # Get shape tool
        shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
        if shape_tool is None:
            st.error("Shape tool initialization failed")
            st.stop()

        # Get free shapes
        label_seq = TDF_LabelSequence()
        shape_tool.GetFreeShapes(label_seq)
        num_shapes = label_seq.Length()
        
        if num_shapes == 0:
            st.error("No shapes found in the STEP file")
            st.stop()

        # Process shapes
        all_input_vertices = []
        all_input_faces = []
        all_layers = []
        total_vertex_offset = 0

        for shape_idx in range(1, num_shapes + 1):
            current_label = label_seq.Value(shape_idx)
            current_shape = shape_tool.GetShape(current_label)
            
            if current_shape is None:
                continue

            # Tessellate
            mesh = BRepMesh_IncrementalMesh(current_shape, 0.8)
            
            # Process faces
            explorer = TopExp_Explorer(current_shape, TopAbs_FACE)
            face_count = 0

            while explorer.More():
                face = topods.Face(explorer.Current())
                face_count += 1
                
                location = TopLoc_Location()
                triangulation = BRep_Tool.Triangulation(face, location)
                
                if triangulation is not None:
                    # Get vertices
                    face_vertices = []
                    for i in range(1, triangulation.NbNodes() + 1):
                        pnt = triangulation.Node(i)
                        face_vertices.append((pnt.X(), pnt.Y(), pnt.Z()))
                    face_vertices = np.array(face_vertices)

                    # Get faces
                    face_faces = []
                    for i in range(1, triangulation.NbTriangles() + 1):
                        tri = triangulation.Triangle(i)
                        face_faces.append([
                            3,
                            total_vertex_offset + tri.Value(1) - 1,
                            total_vertex_offset + tri.Value(2) - 1,
                            total_vertex_offset + tri.Value(3) - 1
                        ])

                    # Store geometry
                    all_input_vertices.append(face_vertices)
                    all_input_faces.append(np.array(face_faces))
                    
                    # Simplified layer handling - just use shape index and face count
                    layer_name = f"Shape_{shape_idx}_Face_{face_count}"
                    all_layers.extend([layer_name] * len(face_faces))
                    total_vertex_offset += len(face_vertices)

                explorer.Next()

            st.info(f"Processed shape {shape_idx} with {face_count} faces")

        # Process geometry
        if all_input_vertices and all_input_faces:
            input_vertices = np.vstack(all_input_vertices)
            input_faces = np.vstack(all_input_faces)
            
            st.info(f"Final geometry stats:")
            st.info(f"- Total vertices: {len(input_vertices)}")
            st.info(f"- Total faces: {len(input_faces)}")
            st.info(f"- Unique layers: {len(set(all_layers))}")

            # Start visualization
            st.subheader("Interactive Visualization with Layers")
            
            # Create PyVista plotter
            plotter = pv.Plotter(window_size=(800, 600))
            
            # Process each layer
            unique_layers = list(set(all_layers))
            colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_layers)))
            
            for idx, layer in enumerate(unique_layers):
                # Get faces for this layer
                layer_faces = [face for j, face in enumerate(all_input_faces) if all_layers[j] == layer]
                if layer_faces:
                    layer_mesh = pv.PolyData(input_vertices, np.vstack(layer_faces))
                    color = colors[idx][:3]  # Remove alpha channel
                    plotter.add_mesh(layer_mesh, show_edges=True, opacity=0.7, 
                                   color=color, label=layer)
            
            plotter.add_legend()
            
            # Export visualization
            html_path = os.path.join(tempfile.gettempdir(), "geometry_layers.html")
            plotter.export_html(html_path)
            plotter.close()
            
            # Display in Streamlit
            with open(html_path, "r") as f:
                st.components.v1.html(f.read(), height=600)
                
                st.success("Input geometry with layers rendered successfully!")
                  # Convex Hull Calculation
                st.subheader("Convex Hull Calculation")
                if len(input_vertices) >= 3:  # Convex hull requires at least 3 points
                    hull = ConvexHull(input_vertices, qhull_options="Qt Qf")  # Handle planar surfaces with QJ option

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
        else:
            st.error("No valid geometry found in the STEP file")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Cleanup
        try:
            os.unlink(step_file_path)
        except:
            pass
    
else:
    st.info("Please upload a STEP file to begin.")