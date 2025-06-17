import pywinctl

for i, title in enumerate(pywinctl.getAllTitles()):
    print(f"{i}: {repr(title)}")