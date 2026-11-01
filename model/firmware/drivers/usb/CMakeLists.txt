cmake_minimum_required(VERSION 3.13)

# Target standard Raspberry Pi Pico (RP2040)
set(PICO_BOARD pico CACHE STRING "Board type")

# Automatically locate pico-sdk from environment or known directories
if(NOT DEFINED PICO_SDK_PATH)
    if(DEFINED ENV{PICO_SDK_PATH})
        set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
    elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/../../../../deps/pico-sdk")
        set(PICO_SDK_PATH "${CMAKE_CURRENT_LIST_DIR}/../../../../deps/pico-sdk")
    elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/pico-sdk")
        set(PICO_SDK_PATH "${CMAKE_CURRENT_LIST_DIR}/pico-sdk")
    endif()
endif()

if(NOT EXISTS "${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
    message(FATAL_ERROR "pico-sdk not found at ${PICO_SDK_PATH}. Run ./pull_dependencies.sh or set PICO_SDK_PATH.")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_usb_driver C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Build USB driver library
add_library(usb_driver STATIC usb.c)
target_include_directories(usb_driver PUBLIC ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(usb_driver pico_stdlib pico_stdio_usb)

# Build test executable
add_executable(test_usb test_usb.c)
target_link_libraries(test_usb usb_driver pico_stdlib pico_stdio_usb)

# Configure USB CDC serial: enable USB, disable hardware UART pins
pico_enable_stdio_usb(test_usb 1)
pico_enable_stdio_uart(test_usb 0)

# Generate UF2, BIN, and HEX outputs
pico_add_extra_outputs(test_usb)
