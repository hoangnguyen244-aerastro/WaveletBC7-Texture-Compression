from src.wavelet_bc7.research import Method
from scripts.plot_sweep import plot
import csv

def test_sweep_plot(tmp_path):
    f=tmp_path/"raw_results.csv"
    rows=[
        dict(image_id="one",mode="identity",strength="0",psnr_db="40"),
        dict(image_id="one",mode="fixed",strength="1",psnr_db="39"),
        dict(image_id="one",mode="adaptive",strength="1",psnr_db="39.5"),
    ]
    with f.open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    assert plot(f).exists()
