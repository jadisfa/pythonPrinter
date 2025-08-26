from PyInstaller.utils.hooks import collect_data_files, collect_submodules
 
datas = collect_data_files('reportlab')
hiddenimports = collect_submodules('reportlab')