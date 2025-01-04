from OCC.Core.TColStd import TColStd_HSequenceOfExtendedString

import streamlit as st
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
from OCC.Core.TDF import TDF_LabelSequence
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDocStd import TDocStd_Document
import matplotlib.pyplot as plt
from OCC.Core.IFSelect import IFSelect_RetDone

import pyvista as pv
import numpy as np
from scipy.spatial import ConvexHull
import tempfile
import os

# App title
st.title("TEST 2 - STEP File Visualization with Convex Hull and Layers")

# File upload
uploaded_file = st.file_uploader("Upload a STEP file", type=["step", "stp"])

if uploaded_file is not None:
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=".step") as tmp_file:
            tmp_file.write(uploaded_file.read())
            step_file_path = tmp_file.name

        st.info(f"Temporary file saved at: {step_file_path}")

        with open(step_file_path, "r", encoding="utf8") as step_file:
            step_file_as_string = step_file.read()

        _shapes = []

        # create an handle to a document
        # doc = TDocStd_Document("pythonocc-doc")
        doc = TDocStd_Document(TCollection_ExtendedString("pythonocc-doc"))

        # Get root assembly
        shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
        l_colors = XCAFDoc_DocumentTool.ColorTool(doc.Main())
        l_layers = XCAFDoc_DocumentTool.LayerTool(doc.Main())
        l_materials = XCAFDoc_DocumentTool.MaterialTool(doc.Main())

        step_reader = STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)

        # status = step_reader.ReadStream("pyocc_stream", step_file_as_string)
        status = step_reader.ReadFile(step_file_path)
        if status == IFSelect_RetDone:
            step_reader.Transfer(doc)

        labels = TDF_LabelSequence()
        color_labels = TDF_LabelSequence()

        shape_tool.GetFreeShapes(labels)

        st.write("Number of shapes at root :%i" % labels.Length())
        for i in range(labels.Length()):
            sub_shapes_labels = TDF_LabelSequence()
            print("Is Assembly :", shape_tool.IsAssembly(labels.Value(i + 1)))
            sub_shapes = shape_tool.GetSubShapes(labels.Value(i + 1),
                                                 sub_shapes_labels)
            st.write("Number of subshapes in the assemly :%i" %
                     sub_shapes_labels.Length())
        l_colors.GetColors(color_labels)

        st.write("Number of colors=%i" % color_labels.Length())
        for i in range(color_labels.Length()):
            color = color_labels.Value(i + 1)

        for i in range(labels.Length()):
            label = labels.Value(i + 1)
            a_shape = shape_tool.GetShape(label)
            m = l_layers.GetLayers(a_shape)
            st.write(f"length layers: {m.Length()} for shape {a_shape}")
            _shapes.append(a_shape)

        # Cleanup
        try:
            os.unlink(step_file_path)
        except Exception:
            pass

    except Exception:
        pass
else:
    st.info("Please upload a STEP file to begin.")
