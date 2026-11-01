/* ==============================================================================
 * Unified Bare-Metal Linker Script for MCUML (model/firmware/linker/linker.ld)
 * Consolidated for both Pre-Silicon (QEMU) and Post-Silicon (Raspberry Pi Pico RP2040).
 * Architecture: ARM Cortex-M0+ / ARMv6-M
 * ============================================================================== */

ENTRY(Reset_Handler)

MEMORY
{
    /* Flash memory: 2048 KB starting at 0x10000000 (RP2040 XIP & QEMU Flash) */
    FLASH (rx)  : ORIGIN = 0x10000000, LENGTH = 2048K
    /* SRAM: 16 KB starting at 0x20000000 (compatible with both QEMU 16K SRAM and RP2040) */
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 16K
}

SECTIONS
{
    /*
     * RP2040 Second-Stage Bootloader (.boot2).
     * If .boot2 section is present (post-silicon), placed at 0x10000000 (256 bytes).
     * If .boot2 is not present (pre-silicon QEMU), this section consumes 0 bytes.
     */
    .boot2 :
    {
        __boot2_start__ = .;
        KEEP(*(.boot2))
        *(.boot2*)
        . = ALIGN(256);
        __boot2_end__ = .;
    } > FLASH

    /*
     * Interrupt Vector Table (.vectors).
     * 256-byte aligned:
     * - Pre-Silicon (no boot2): placed at 0x10000000
     * - Post-Silicon (boot2 present): placed at 0x10000100
     */
    .vectors :
    {
        . = ALIGN(256);
        __vectors_start__ = .;
        KEEP(*(.vectors))
        __vectors_end__ = .;
    } > FLASH

    /* Program instructions and read-only data */
    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
        _etext = .;
    } > FLASH

    /* Global constructors table */
    .init_array :
    {
        . = ALIGN(4);
        __init_array_start = .;
        KEEP(*(.init_array*))
        __init_array_end = .;
        . = ALIGN(4);
    } > FLASH

    /* Load address of initialized data in Flash */
    _sidata = LOADADDR(.data);

    /* Initialized data copied from Flash to RAM at boot */
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT > FLASH

    /* Zero-initialized data (.bss) in RAM */
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    /* Stack definitions (grows downward from top of RAM) */
    __StackLimit = ORIGIN(RAM);
    __StackTop   = ORIGIN(RAM) + LENGTH(RAM);
    _estack      = __StackTop;
}
