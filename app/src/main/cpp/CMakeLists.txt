cmake_minimum_required(VERSION 3.22.1)
project("soccerlegacy")

get_filename_component(
    NDK_MODULE_PATH
    "${ANDROID_NDK}/sources/android/native_app_glue"
    ABSOLUTE
)

add_library(
    soccerlegacy
    SHARED
    # ✅ Relative to CMakeLists.txt itself — just the filename
    main.cpp
    ${NDK_MODULE_PATH}/android_native_app_glue.c
)

target_include_directories(
    soccerlegacy PRIVATE
    ${NDK_MODULE_PATH}
)

target_link_libraries(
    soccerlegacy
    android
    log
    EGL
    GLESv3
)
