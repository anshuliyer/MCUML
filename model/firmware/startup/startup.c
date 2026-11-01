/**
 * @file startup.c
 * @brief Consolidated Startup Code for Pre-Silicon (QEMU) and Post-Silicon (Pico RP2040).
 *
 * Provides:
 *  1. (Post-Silicon only) 256-byte RP2040 second-stage bootloader (.boot2) with valid CRC.
 *  2. ARM Cortex-M0+ Interrupt Vector Table (.vectors).
 *  3. Reset_Handler:
 *     - Sets ARM Cortex-M0+ VTOR register to point to vector table.
 *     - Copies initialized data (.data) from Flash to RAM.
 *     - Zeroes uninitialized data (.bss) in RAM.
 *     - Executes C/C++ global constructors (.init_array).
 *     - Jumps to main().
 *  4. Default weak exception handlers.
 */

#include <stdint.h>

/* Forward declaration of application entry point */
extern int main(void);

/* Linker symbols */
extern uint32_t __StackTop;
extern uint32_t __StackLimit;
extern uint32_t __vectors_start__;

extern uint32_t _sidata;       /* LMA of .data in Flash */
extern uint32_t _sdata;        /* VMA start of .data in RAM */
extern uint32_t _edata;        /* VMA end of .data in RAM */

extern uint32_t _sbss;         /* Start of .bss in RAM */
extern uint32_t _ebss;         /* End of .bss in RAM */

extern void (*__init_array_start[])(void);
extern void (*__init_array_end[])(void);

/*
 * ==============================================================================
 * Post-Silicon RP2040 Second-Stage Bootloader (.boot2)
 * The on-chip RP2040 ROM requires this 256-byte block at Flash offset 0x00000000
 * to configure external QSPI flash (W25Q080) into XIP mode before jumping to code.
 * In Pre-Silicon (QEMU), this block is omitted so Flash starts directly at .vectors.
 * ==============================================================================
 */
#ifdef POSTSIL
__attribute__((section(".boot2"), used))
const uint8_t rp2040_boot2_w25q080[256] = {
    0x00, 0xb5, 0x32, 0x4b, 0x21, 0x20, 0x58, 0x60, 0x98, 0x68, 0x02, 0x21, 0x88, 0x43, 0x98, 0x60,
    0xd8, 0x60, 0x18, 0x61, 0x58, 0x61, 0x2e, 0x4b, 0x00, 0x21, 0x99, 0x60, 0x02, 0x21, 0x59, 0x61,
    0x01, 0x21, 0xf0, 0x22, 0x99, 0x50, 0x2b, 0x49, 0x19, 0x60, 0x01, 0x21, 0x99, 0x60, 0x35, 0x20,
    0x00, 0xf0, 0x44, 0xf8, 0x02, 0x22, 0x90, 0x42, 0x14, 0xd0, 0x06, 0x21, 0x19, 0x66, 0x00, 0xf0,
    0x34, 0xf8, 0x19, 0x6e, 0x01, 0x21, 0x19, 0x66, 0x00, 0x20, 0x18, 0x66, 0x1a, 0x66, 0x00, 0xf0,
    0x2c, 0xf8, 0x19, 0x6e, 0x19, 0x6e, 0x19, 0x6e, 0x05, 0x20, 0x00, 0xf0, 0x2f, 0xf8, 0x01, 0x21,
    0x08, 0x42, 0xf9, 0xd1, 0x00, 0x21, 0x99, 0x60, 0x1b, 0x49, 0x19, 0x60, 0x00, 0x21, 0x59, 0x60,
    0x1a, 0x49, 0x1b, 0x48, 0x01, 0x60, 0x01, 0x21, 0x99, 0x60, 0xeb, 0x21, 0x19, 0x66, 0xa0, 0x21,
    0x19, 0x66, 0x00, 0xf0, 0x12, 0xf8, 0x00, 0x21, 0x99, 0x60, 0x16, 0x49, 0x14, 0x48, 0x01, 0x60,
    0x01, 0x21, 0x99, 0x60, 0x01, 0xbc, 0x00, 0x28, 0x00, 0xd0, 0x00, 0x47, 0x12, 0x48, 0x13, 0x49,
    0x08, 0x60, 0x03, 0xc8, 0x80, 0xf3, 0x08, 0x88, 0x08, 0x47, 0x03, 0xb5, 0x99, 0x6a, 0x04, 0x20,
    0x01, 0x42, 0xfb, 0xd0, 0x01, 0x20, 0x01, 0x42, 0xf8, 0xd1, 0x03, 0xbd, 0x02, 0xb5, 0x18, 0x66,
    0x18, 0x66, 0xff, 0xf7, 0xf2, 0xff, 0x18, 0x6e, 0x18, 0x6e, 0x02, 0xbd, 0x00, 0x00, 0x02, 0x40,
    0x00, 0x00, 0x00, 0x18, 0x00, 0x00, 0x07, 0x00, 0x00, 0x03, 0x5f, 0x00, 0x21, 0x22, 0x00, 0x00,
    0xf4, 0x00, 0x00, 0x18, 0x22, 0x20, 0x00, 0xa0, 0x00, 0x01, 0x00, 0x10, 0x08, 0xed, 0x00, 0xe0,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x74, 0xb2, 0x4e, 0x7a
};
#endif

/* Reset and Exception Handlers */
void Reset_Handler(void);
void Default_Handler(void);

void NMI_Handler(void)         __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void)   __attribute__((weak, alias("Default_Handler")));
void SVC_Handler(void)         __attribute__((weak, alias("Default_Handler")));
void PendSV_Handler(void)      __attribute__((weak, alias("Default_Handler")));
void SysTick_Handler(void)     __attribute__((weak, alias("Default_Handler")));

/*
 * Interrupt Vector Table.
 * Placed in section .vectors (aligned to 256 bytes).
 */
__attribute__((section(".vectors"), used))
void (* const g_pfnVectors[])(void) = {
    (void (*)(void))(&__StackTop),  /* 0x00: Initial Main Stack Pointer */
    Reset_Handler,                  /* 0x04: Reset Handler */
    NMI_Handler,                    /* 0x08: Non-Maskable Interrupt */
    HardFault_Handler,              /* 0x0C: Hard Fault */
    0, 0, 0, 0, 0, 0, 0,            /* 0x10 - 0x28: Reserved */
    SVC_Handler,                    /* 0x2C: SVCall */
    0, 0,                           /* 0x30 - 0x34: Reserved */
    PendSV_Handler,                 /* 0x38: PendSV */
    SysTick_Handler                 /* 0x3C: SysTick */
};

/**
 * @brief Reset Handler executed upon core power-on or reset.
 */
void Reset_Handler(void) {
    /*
     * 1. Point the Cortex-M0+ VTOR register to the active vector table.
     *    In QEMU (Pre-silicon), VTOR is 0x10000000.
     *    On RP2040 (Post-silicon), VTOR is 0x10000100 (immediately following .boot2).
     */
    *(volatile uint32_t *)0xE000ED08 = (uint32_t)&__vectors_start__;

    /*
     * 2. Copy initialized data (.data) from Flash to RAM.
     */
    uint32_t *pSrc = &_sidata;
    uint32_t *pDest = &_sdata;
    while (pDest < &_edata) {
        *pDest++ = *pSrc++;
    }

    /*
     * 3. Zero-fill uninitialized data (.bss) in RAM.
     */
    pDest = &_sbss;
    while (pDest < &_ebss) {
        *pDest++ = 0U;
    }

    /*
     * 4. Call C/C++ global constructors (.init_array).
     */
    uint32_t count = (uint32_t)(__init_array_end - __init_array_start);
    for (uint32_t i = 0; i < count; i++) {
        if (__init_array_start[i] != 0) {
            __init_array_start[i]();
        }
    }

    /*
     * 5. Jump to application entry point.
     */
    (void)main();

    /*
     * Fallback loop if main() ever returns.
     */
    while (1) {
        __asm__ volatile("wfi");
    }
}

/**
 * @brief Default interrupt and exception handler.
 */
void Default_Handler(void) {
    while (1) {
        __asm__ volatile("wfi");
    }
}
