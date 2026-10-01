"""Execute the Colab notebook in a fresh Jupyter kernel."""

from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
notebook = nbformat.read(root / "notebooks/reproduce_ssac27.ipynb", as_version=4)
NotebookClient(
    notebook,
    timeout=300,
    kernel_name="python3",
    resources={"metadata": {"path": str(root)}},
).execute()
print("Notebook executed successfully.")
