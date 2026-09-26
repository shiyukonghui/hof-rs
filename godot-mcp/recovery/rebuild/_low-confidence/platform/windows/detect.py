    from SCons.Variables import BoolVariable, EnumVariable

    mingw = os.getenv("MINGW_PREFIX", "")

    # Dependencies folder.
    deps_folder = os.getenv("LOCALAPPDATA")
    if deps_folder and not os.getenv("MSYSTEM"):
        deps_folder = os.path.join(deps_folder, "Godot", "build_deps")
    else:
        # Cross-compiling, the deps install script puts things in `bin`.
        # Getting an absolute path to it is a bit hacky in Python.
        try:
            import inspect

            caller_frame = inspect.stack()[1]
            caller_script_dir = os.path.dirname(os.path.abspath(caller_frame[1]))
            deps_folder = os.path.join(caller_script_dir, "bin", "build_deps")
        except Exception:  # Give up.
            deps_folder = ""

    return [
        ("mingw_prefix", "MinGW prefix", mingw),
        EnumVariable("windows_subsystem", "Windows subsystem", "gui", ["gui", "console"], ignorecase=2),
        ("msvc_version", "MSVC version to use. Handled automatically by SCons if omitted.", ""),
        ("mssdk_version", "Windows SDK version to use. Handled automatically by SCons if omitted.", ""),
        BoolVariable("use_mingw", "Use the Mingw compiler, even if MSVC is installed.", False),
        BoolVariable("use_llvm", "Use the LLVM compiler", False),
        BoolVariable("use_static_cpp", "Link MinGW/MSVC C++ runtime libraries statically", True),
        BoolVariable("use_asan", "Use address sanitizer (ASAN)", False),
        BoolVariable("use_ubsan", "Use LLVM compiler undefined behavior sanitizer (UBSAN)", False),
        BoolVariable("debug_crt", "Compile with MSVC's debug CRT (/MDd)", False),
        BoolVariable("incremental_link", "Use MSVC incremental linking. May increase or decrease build times.", False),
        BoolVariable("silence_msvc", "Silence MSVC's cl/link stdout bloat, redirecting any errors to stderr.", True),
        # Screen reader support.
        (
            "accesskit_sdk_path",
            "Path to the AccessKit C SDK",
            os.path.join(deps_folder, "accesskit"),
        ),
        # OpenGL over Direct3D 11.
        (
            "angle_libs",
            "Path to the ANGLE static libraries",
            os.path.join(deps_folder, "angle"),
        ),
        # Direct3D 12 support.
        (
            "mesa_libs",
            "Path to the MESA/NIR static libraries (required for D3D12)",
            os.path.join(deps_folder, "mesa"),
        ),
        (
            "agility_sdk_path",
            "Path to the Agility SDK distribution (optional for D3D12)",
            os.path.join(deps_folder, "agility_sdk"),
        ),
        BoolVariable(
            "agility_sdk_multiarch",
            "Whether the Agility SDK DLLs will be stored in arch-specific subdirectories",
            False,
        ),
        BoolVariable("use_pix", "Use PIX (Performance tuning and debugging for DirectX 12) runtime", False),
        (
            "pix_path",
            "Path to the PIX runtime distribution (optional for D3D12)",
            os.path.join(deps_folder, "pix"),
        ),
        BoolVariable(
            "prefer_high_performance_gpu", "Prefer high-performance GPU on NVIDIA Optimus/AMD PowerXpress systems", True
        ),
    ]


def get_doc_classes():
    return [
            if env["arch"] == "arm64":
                env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/arm64/msvc/static"])
            elif env["arch"] == "x86_64":
                env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86_64/msvc/static"])
            elif env["arch"] == "x86_32":
                env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86/msvc/static"])
            LIBS += [
                "accesskit",
                "runtimeobject",
                "propsys",
                "oleaut32",
                "user32",
                "userenv",
                "ntdll",
            ]
            env.Append(CPPDEFINES=["ACCESSKIT_ENABLED"])
        else:
            print_error(
                "The screen reader support driver requires dependencies to be installed.\n"
                f"You can install them by running `python {os.path.join('misc', 'scripts', 'install_accesskit.py')}`.\n"
                "See the documentation for more information:\n\t"
                "https://docs.godotengine.org/en/latest/engine_details/development/compiling/compiling_for_windows.html#compiling-with-accesskit-support"
                "\nAlternatively, disable this driver by compiling with `accesskit=no` explicitly."
            )
            env["accesskit"] = False

    if env["vulkan"]:
        env.AppendUnique(CPPDEFINES=["VULKAN_ENABLED"])

        if not env["use_volk"]:
            LIBS += ["vulkan"]

    if env["sdl"]:
        env.Append(CPPDEFINES=["SDL_ENABLED"])

                    env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86_64/mingw-llvm/static/"])
                elif env["arch"] == "x86_32":
                    env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86/mingw-llvm/static/"])
            else:
                if env["arch"] == "x86_64":
                    env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86_64/mingw/static/"])
                elif env["arch"] == "x86_32":
                    env.Append(LIBPATH=[env["accesskit_sdk_path"] + "/lib/windows/x86/mingw/static/"])
            env.Append(LIBPATH=["#bin/obj/platform/windows"])
            env.Append(
                LIBS=[
                    "accesskit",
                    "runtimeobject",
                    "propsys",
                    "oleaut32",
                    "user32",
                    "userenv",
                    "ntdll",
                ]
            )
            env.Append(LIBPATH=["#platform/windows"])
            env.Append(CPPDEFINES=["ACCESSKIT_ENABLED"])
        else:
            print_warning(
                "The screen reader support driver requires dependencies to be installed.\n"
                f"You can install them by running `python {os.path.join('misc', 'scripts', 'install_accesskit.py')}`.\n"
                "See the documentation for more information:\n\t"
                "https://docs.godotengine.org/en/latest/engine_details/development/compiling/compiling_for_windows.html#compiling-with-accesskit-support"
                "\nAlternatively, disable this driver by compiling with `accesskit=no` explicitly."
            )
            env["accesskit"] = False

    if env.debug_features:
        env.Append(LIBS=["psapi", "dbghelp"])

    if env["vulkan"]:
        env.Append(CPPDEFINES=["VULKAN_ENABLED"])

        if not env["use_volk"]:
            env.Append(LIBS=["vulkan"])

    if env["sdl"]:
        env.Append(CPPDEFINES=["SDL_ENABLED"])

    if env["d3d12"]:
        if env["use_llvm"]:
            check_d3d12_installed(env, env["arch"] + "-llvm")
        else:
            check_d3d12_installed(env, env["arch"] + "-gcc")

        env.AppendUnique(CPPDEFINES=["D3D12_ENABLED"])

        env.Append(LIBS=["dxgi", "dxguid"])

        # PIX
        if env["arch"] not in ["x86_64", "arm64"] or env["pix_path"] == "" or not os.path.exists(env["pix_path"]):
            env["use_pix"] = False

        if env["use_pix"]:
            arch_subdir = "arm64" if env["arch"] == "arm64" else "x64"