def set_scu_folders(scu_folders):
    global _scu_folders
    _scu_folders = scu_folders


def add_source_files_orig(self, sources, files, allow_gen=False):
    # Convert string to list of absolute paths (including expanding wildcard)
    if isinstance(files, str):
        # Exclude .gen.cpp files from globbing, to avoid including obsolete ones.
        # They should instead be added manually.
        skip_gen_cpp = "*" in files
        files = self.Glob(files)
        if skip_gen_cpp and not allow_gen:
            files = [f for f in files if not str(f).endswith(".gen.cpp")]

    # Add each path as compiled Object following environment (self) configuration
    for file in files:
        obj = self.Object(file)
        if obj in sources:
            print_warning('Object "{}" already included in environment sources.'.format(obj))
            continue
        sources.append(obj)


def add_source_files_scu(self, sources, files, allow_gen=False):
    if self["scu_build"] and isinstance(files, str):
        if "*." not in files:
            return False

        # If the files are in a subdirectory, we want to create the scu gen
        # files inside this subdirectory.
        subdir = os.path.dirname(files)
        subdir = subdir if subdir == "" else subdir + "/"
        section_name = self.Dir(subdir).tpath
        section_name = section_name.replace("\\", "/")  # win32
        # if the section name is in the hash table?
        # i.e. is it part of the SCU build?
        global _scu_folders
        if section_name not in (_scu_folders):
            return False

        # Add all the gen.cpp files in the SCU directory
        add_source_files_orig(self, sources, subdir + ".scu/scu_*.gen.cpp", True)
        return True
    return False


# Either builds the folder using the SCU system,
# or reverts to regular build.
def add_source_files(self, sources, files, allow_gen=False):
    if not add_source_files_scu(self, sources, files, allow_gen):
        # Wraps the original function when scu build is not active.
        add_source_files_orig(self, sources, files, allow_gen)
        return False
    return True


def redirect_emitter(target, source, env):
    """
    Emitter to automatically redirect object/library build files to the `bin/obj` directory,