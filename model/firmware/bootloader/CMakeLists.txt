cmake_minimum_required(VERSION 3.13)

# Target Raspberry Pi Pico (RP2040)
set(PICO_BOARD pico CACHE STRING "Board type")

# Locate pico-sdk
if(NOT DEFINED PICO_SDK_PATH)
    if(DEFINED ENV{PICO_SDK_PATH})
        set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
    elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/../../../deps/pico-sdk")
        set(PICO_SDK_PATH "${CMAKE_CURRENT_LIST_DIR}/../../../deps/pico-sdk")
    endif()
endif()

if(NOT EXISTS "${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
    message(FATAL_ERROR "pico-sdk not found at ${PICO_SDK_PATH}.")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_bootloader C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Build bl1 executable with USB CDC driver and SysTick timer
add_executable(bl1 
    bl1.c
    ../drivers/usb/usb.c
    ../drivers/timer/systick.c
)

target_include_directories(bl1 PUBLIC 
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/../drivers/usb/hdrs
    ${CMAKE_CURRENT_LIST_DIR}/../drivers/usb
    ${CMAKE_CURRENT_LIST_DIR}/../drivers/timer
)

target_link_libraries(bl1 
    pico_stdlib 
    pico_stdio_usb
)

# Enable USB CDC serial, disable hardware UART pins
pico_enable_stdio_usb(bl1 1)
pico_enable_stdio_uart(bl1 0)

# Generate UF2, BIN, and HEX outputs
pico_add_extra_outputs(bl1)
