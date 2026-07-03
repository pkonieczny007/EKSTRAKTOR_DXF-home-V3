# Tymczasowy: podglady PNG wynikow ekstrakcji (czarne tlo jak w CAD)
import ezdxf, glob
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

import sys
pattern = sys.argv[1] if len(sys.argv) > 1 else r"testy\pretesty\dxf\*.dxf"
for f in glob.glob(pattern):
    doc = ezdxf.readfile(f)
    fig = plt.figure(figsize=(14, 6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
    out = f.replace(".dxf", ".png")
    fig.savefig(out, dpi=120, facecolor="black")
    plt.close(fig)
    print(out)
