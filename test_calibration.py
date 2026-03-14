import btk
import c3d_utils

file_path = r'C:\Users\20127\Desktop\Motion Analysis Corporation\walk\Walk1.c3d'
acq = c3d_utils.read_c3d(file_path)
cal, ftype = c3d_utils.get_force_plate_calibration(acq, 0)
print("校准矩阵:", cal)
print("力板类型:", ftype)