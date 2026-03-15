import c3d_utils
file_path = r'C:\Users\20127\Desktop\date c3d\S10CCPD002T3.c3d'
config = c3d_utils.get_project_config(file_path)
print(config.get('channels', {}))