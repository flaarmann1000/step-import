import pyvista as pv

plotter = pv.Plotter()
plotter.add_mesh(pv.Sphere())
plotter.export_html("test_visualization.html")
print("Exported to test_visualization.html")