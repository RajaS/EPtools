from eptools.io_tools import read_eko_duo_export, read_workmate_export
import os
from pathlib import Path

current_dir = Path(__file__).parent
sample_folder = current_dir / "samples"
sample_folder = sample_folder.resolve()

def test_read_eko_duo_export():
    eko_duo_sample_file = os.path.join(sample_folder, "eko_duo/eko_duo.zip")
    info, ecg_data, phono = read_eko_duo_export(eko_duo_sample_file)
    
    assert len(info['signal_names']) == 3
    assert ecg_data.shape == (3, 15000)
    assert phono.shape == (120000,)
    

def test_read_workmate_export():
    workmate_sample_folder = os.path.join(sample_folder, "workmate")
    info, data = read_workmate_export(workmate_sample_folder)
    
    assert info['id'] == 'J-740979'
    assert len(info['signal_names']) == 35
    assert data.shape == (35, 259294)



if __name__ == "__main__":
    test_read_workmate_export()
