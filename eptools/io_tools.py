"""
Various IO utilities

to read ECG formats
or EP system exports

uniformly returns a data numpy array as channels x samples and
an info dict
"""
import zipfile
import numpy
from scipy.io import wavfile
import io
from datetime import datetime
import glob
import os

print('---------------------')
print("io_tools.py imported")

# utility functions
def _datetime_from_strings(date_string, time_string):
    """
    date is in format 24/09/2024
    and time like 08:59:25
    """
    datetime_str = date_string + " " + time_string
    datetime_format = "%d/%m/%Y %H:%M:%S"
    datetime_object = datetime.strptime(datetime_str, datetime_format)
    return datetime_object


def _read_info(session_files):
    """
    combine info from all files.
    Assume all sessions are from same patient and have same recording parameters 
    """
    info = {}
    with open(session_files[0], 'r') as f:
        lines = f.readlines()
        info['name'] = lines[0].split("=")[1].rstrip('\n')
        info['id'] = lines[1].split("=")[1].rstrip('\n')

        start_date = lines[2].split("=")[1].rstrip('\n')
        start_time = lines[3].split("=")[1].rstrip('\n')
        info['recording_start'] = _datetime_from_strings(start_date, start_time)  

        info['sample_rate'] = lines[4].split("=")[1].rstrip('\n')
        info['signal_resolution'] = lines[5].split("=")[1].rstrip('\n')

    with open(session_files[-1], 'r') as f:
        lines = f.readlines()
        end_date = lines[2].split("=")[1].rstrip('\n')
        end_time = lines[3].split("=")[1].rstrip('\n')
        recording_end = _datetime_from_strings(end_date, end_time)
        # ideally we want to add duration of the signal in this session
        # but this information is not available in thje session file
        info['recording_end'] = recording_end
    return info


def _get_unique_signals(session_file):
    with open(session_file) as f:
        lines = f.readlines()
        # first 6 lines are info
        lines = lines[6:]
        all_file_names = [line.split(',')[0] for line in lines]
        file_names = []
        signal_names = []
        for file_name in all_file_names:
            signal_name = file_name.split('.')[0]
            if signal_name not in signal_names:
                signal_names.append(signal_name)
                file_names.append(file_name)
    return signal_names, file_names


def read_workmate_export(foldername):
    """
    Exporting signals from EP workmate system produces a folder with all the files
    When the exported data is longer than 2 minutes, multiple sessions are exported
    for each session, each signal for each page is a separate file
    """
    # identify sessions
    session_files = glob.glob(os.path.join(foldername, "*Information*.TXT"))
    session_files.sort()
    
    # combine the info for each session to produce a common info
    info = _read_info(session_files)
    
    # identify all unique signals from first session file
    # order based on order of appearance in each page
    signal_names, file_names = _get_unique_signals(session_files[0])
    info['signal_names'] = signal_names
    
    # load the signals for each session and combine into one
    data_list = []
    for session_file in session_files:
        signal_names, file_names = _get_unique_signals(session_file)
        session_data_list = []
        for file_name in file_names:
            full_file_name = os.path.join(foldername, file_name)
            data = numpy.loadtxt(full_file_name)
            session_data_list.append(data)

        data = numpy.vstack(session_data_list)
        data_list.append(data)

    # combine data from all sessions
    data = numpy.hstack(data_list)
    
    return info, data


def read_eko_duo_export(zipfile_path):
    """
    zipfile that is exported contains 4 wav files
    one is the phonocardiogram, other three are ECGs

    returns info (dict),
    ecg_data and phonocardiogram (numpy arrays)
    """
    info = {}
    
    with zipfile.ZipFile(zipfile_path) as z:
        # read ecg files
        ecg_files = [f for f in z.namelist() if "ECG" in f]
        
        ecg_data_list = []
        for ecg_file in ecg_files:
            with z.open(ecg_file) as f:
                ecg_samp_rate, ecg = wavfile.read(io.BytesIO(f.read()))
                ecg_data_list.append(ecg)

        ecg_data = numpy.vstack(ecg_data_list)

        # read the phonocardiogram
        # file ends in wav, but does not have 'ECG'
        phonocardiogram_file = [f for f in z.namelist() if f not in ecg_files][0]
        with z.open(phonocardiogram_file) as f:
            phono_samp_rate, phonocardiogram = wavfile.read(io.BytesIO(f.read()))
        
    info['signal_names'] = ["_".join(f.split('.')[0].split('_')[7:])
                            for f in ecg_files]
    info['sampling_rate'] = ecg_samp_rate
    info['phonocardiogram_sampling_rate'] = phono_samp_rate

    return info, ecg_data, phonocardiogram


def read_xml_ecg(xmlfile):
    """
    Read ECG data from an XML file
    """
    return None


if __name__ == "__main__":
    ## test the functions
    # foldername = "../tests/samples/workmate"
    # info, data = read_workmate_export(foldername)
    # print(info)
    # print(data.shape)

    filename = "../tests/samples/eko_duo/eko_duo.zip"
    info, ecg_data, phono = read_eko_duo_export(filename)
    print(info)
    # print(ecg_data.shape)
    
