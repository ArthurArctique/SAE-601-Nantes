import os
import streamlit.components.v1 as components

parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "dept_map_component")
_dept_map_component = components.declare_component("dept_map", path=build_dir)

def dept_map(selected, map_height=550, key=None):
    return _dept_map_component(selected=selected, map_height=map_height, key=key)
