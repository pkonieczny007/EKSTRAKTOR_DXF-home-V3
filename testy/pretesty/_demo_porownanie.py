# DEMO: miniatura "bez oczyszczenia" (caly surowy _conv.dxf) obok wyniku ekstrakcji.
# Cel: operator porownuje "skad" (caly rysunek) vs "co" (czysta pozycja) bez CAD-a.
import sys
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render_into(ax, dxf_path):
    doc = ezdxf.readfile(dxf_path)
    ax.set_facecolor("black")
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace())
    ax.set_aspect("equal")
    ax.axis("off")


def demo(surowy, wynik, out_png, tytul_l, tytul_r, tif=None):
    n = 3 if tif else 2
    fig, axes = plt.subplots(1, n, figsize=(10 * n, 7))
    fig.patch.set_facecolor("#101418")
    i = 0
    if tif:
        from PIL import Image
        axes[i].imshow(Image.open(tif).convert("L"), cmap="gray")
        axes[i].set_title("TIF (prawda wydrukowana)", color="#cfe", fontsize=13)
        axes[i].axis("off")
        i += 1
    render_into(axes[i], surowy)
    axes[i].set_title(tytul_l, color="#cfe", fontsize=13)
    render_into(axes[i + 1], wynik)
    axes[i + 1].set_title(tytul_r, color="#cfe", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_png, dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(out_png)


if __name__ == "__main__":
    surowy, wynik, out, tl, tr = sys.argv[1:6]
    tif = sys.argv[6] if len(sys.argv) > 6 else None
    demo(surowy, wynik, out, tl, tr, tif)
